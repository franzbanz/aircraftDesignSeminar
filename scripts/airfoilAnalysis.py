import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

XFOIL = r"C:\Users\franz\Documents\Xfoil\xfoil.exe"
RESULTS = Path("xfoil_results")
AIRFOILS = {"Airfoil A": "airfoils/airfoil_A.dat",
            "Airfoil B": "airfoils/airfoil_B.dat",
            "Airfoil C": "airfoils/airfoil_C.dat"}
FLAPS = {"takeOff": 15, "approach": 30, "cruise": 0} # flap deflection in deg, 0 = clean
HINGE_X = 0.70 # flap hinge position in x/c
ALPHA = (-4.0, 16.0, 0.5) # min, max, step in deg
COLUMNS = ["alpha", "CL", "CD", "CDp", "CM", "Top_Xtr", "Bot_Xtr"]

def hook(d):
    return SimpleNamespace(**{k: v[0] if isinstance(v, list) and len(v) == 2 else v
                              for k, v in d.items()})

def getFlightConditions():
    with open("battery_aircraft.json") as f:
        bat = json.load(f, object_hook=hook)

    # aircraft
    mass = bat.mass.takeOffMassMax
    area = bat.dimensions.wingArea
    chord = bat.dimensions.meanAerodynamicChord
    kts = 0.514444 # convert kts to SI
    speed = {"takeOff": bat.performance.takeOffSpeed * kts,
             "approach": bat.performance.approachSpeed * kts,
             "cruise": bat.performance.cruiseSpeedTAS * kts}
    altitude = {"takeOff": 0, "approach": 0, "cruise": bat.performance.cruiseAltitude * 0.3048} # convert ft to SI

    # constants
    g = 9.81
    gamma = 1.4
    R = 287
    T0 = 288.15
    rho0 = 1.225
    lapseRate = 0.0065

    cond = {}
    for name in speed:
        T = T0 - lapseRate * altitude[name] # isa troposphere
        rho = rho0 * (T / T0) ** (g / (lapseRate * R) - 1)
        mu = 1.458e-6 * T ** 1.5 / (T + 110.4) # dynamic viscosity, sutherland
        cond[name] = SimpleNamespace(name=name, speed=speed[name], altitude=altitude[name], T=T, rho=rho,
                                     re=rho * speed[name] * chord / mu,
                                     mach=speed[name] / np.sqrt(gamma * R * T),
                                     cl=mass * g / (0.5 * rho * speed[name] ** 2 * area))

    for c in cond.values():
        print("")
        print(c.name.upper())
        print(f"Speed:                    {c.speed:.2f} m/s")
        print(f"Altitude:                 {c.altitude:.0f} m")
        print(f"Temperature:              {c.T:.2f} K")
        print(f"Air density:              {c.rho:.4f} kg/m^3")
        print(f"Reynolds number:          {c.re:.0f}")
        print(f"Mach number:              {c.mach:.4f}")
        print(f"Required lift coeff.:     {c.cl:.4f}")
    print("")

    return cond

def runXfoil(airfoil, file, c):
    runDir = RESULTS / f"{airfoil.replace(' ', '_')}_{c.name}"
    runDir.mkdir(parents=True, exist_ok=True)
    shutil.copy(file, runDir / "airfoil.dat")
    (runDir / "polar.txt").unlink(missing_ok=True) # old polar would make xfoil ask to overwrite

    flap = FLAPS[c.name]
    commands = ["LOAD airfoil.dat"] # G F: no graphics window
    if flap:
        commands += ["GDES", "FLAP", HINGE_X, 0, flap, ""]
    commands += ["PANE", "OPER", f"VISC {c.re:.0f}", f"MACH {c.mach:.4f}", "ITER 200",
                 "PACC", "polar.txt", "", "ASEQ " + " ".join(map(str, ALPHA)), "PACC", "", "QUIT"]

    log = subprocess.run([XFOIL], input="\n".join(map(str, commands)) + "\n", text=True, cwd=runDir,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120).stdout
    (runDir / "xfoil.log").write_text(log)

    try:
        polar = pd.read_csv(runDir / "polar.txt", sep=r"\s+", skiprows=12, names=COLUMNS)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        raise RuntimeError(f"XFOIL failed for {airfoil}, {c.name}. Check {runDir / 'xfoil.log'}")
    polar["L/D"] = polar.CL / polar.CD
    return polar

def evaluatePolar(polar, clReq):
    iMax = polar.CL.idxmax()
    pre = polar.loc[:iMax].drop_duplicates("CL").sort_values("CL") # pre-stall branch
    res = {"CL_required": clReq, "CL_max": polar.CL[iMax], "alpha_stall": polar.alpha[iMax],
           "CL_margin": polar.CL[iMax] / clReq, "CD": np.nan, "L/D": np.nan, "alpha": np.nan}

    # interpolate at required CL, only possible if it is reached before stall
    if pre.CL.min() <= clReq <= pre.CL.max():
        res["CD"] = np.interp(clReq, pre.CL, pre.CD)
        res["alpha"] = np.interp(clReq, pre.CL, pre.alpha)
        res["L/D"] = clReq / res["CD"]
    return res

def compareAirfoils(cond):
    results, polars = [], {}
    for airfoil, file in AIRFOILS.items():
        for name, c in cond.items():
            print(f"Analyzing {airfoil}, {name}, flap {FLAPS[name]} deg")
            polars[airfoil, name] = runXfoil(airfoil, file, c)
            results.append({"Airfoil": airfoil, "Condition": name, "Flap": FLAPS[name],
                            **evaluatePolar(polars[airfoil, name], c.cl)})

    df = pd.DataFrame(results)
    print("\nAERODYNAMIC COMPARISON SUMMARY")
    print(df.to_string(index=False))
    df.to_csv(RESULTS / "airfoil_comparison.csv", index=False)
    return df, polars

def plotPerCondition(df, polars, x, y, title):
    res = df.set_index(["Airfoil", "Condition"])
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, name in zip(axes, FLAPS):
        for airfoil in AIRFOILS:
            line, = ax.plot(polars[airfoil, name][x], polars[airfoil, name][y], label=airfoil)
            if y == "CL": # mark operating point
                ax.scatter(res.loc[airfoil, name][x], res.loc[airfoil, name].CL_required, color=line.get_color())
        ax.set(title=name, xlabel=x, ylabel=y)
        ax.grid(True)
        ax.legend()
    fig.suptitle(title)
    fig.tight_layout()

def plotResults(df, polars):
    plotPerCondition(df, polars, "CD", "CL", "Drag polars")
    plotPerCondition(df, polars, "alpha", "CL", "Lift coefficient vs angle of attack")
    plotPerCondition(df, polars, "alpha", "CD", "Drag coefficient vs angle of attack")
    plotPerCondition(df, polars, "alpha", "L/D", "Lift-to-drag ratio vs angle of attack")

    # required vs maximum CL
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, name in zip(axes, FLAPS):
        df[df.Condition == name].set_index("Airfoil")[["CL_required", "CL_max"]].plot.bar(
            ax=ax, title=name, rot=0, grid=True)
    fig.suptitle("Required vs maximum lift coefficient")
    fig.tight_layout()

    # cruise efficiency
    df[df.Condition == "cruise"].set_index("Airfoil")["L/D"].plot.bar(
        title="Cruise efficiency", ylabel="Lift-to-drag ratio", rot=0, grid=True, figsize=(9, 5))
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    cond = getFlightConditions()
    df, polars = compareAirfoils(cond)
    plotResults(df, polars)
