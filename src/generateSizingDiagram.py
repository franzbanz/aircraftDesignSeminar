import json
import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace

def hook(d):
    return SimpleNamespace(**{k: v[0] if isinstance(v, list) and len(v) == 2 else v
                              for k, v in d.items()})

def isaDensity(h, rho0):
    return rho0 * (1 - 2.25577e-5 * h) ** 4.2559

def getSizingDiagram():
    with open("parameters.json") as f:
        par = json.load(f, object_hook=hook)
    with open("reference_aircraft.json") as f:
        ref = json.load(f, object_hook=hook)
    with open("battery_aircraft.json") as f:
        bat = json.load(f, object_hook=hook)

    # parameters
    g = par.mission.gravity
    sTofl = par.performance.takeOffFieldLengthMax
    lLdg = par.performance.landingFieldLengthMax
    rho0 = par.performance.takeOffDensity
    fieldElevation = par.performance.takeOffAltitude
    vCruise = par.performance.cruiseSpeedMin * 0.5144

    # ref aircraft
    m0Ref = ref.mass.takeOffMassMax
    Sref = ref.dimensions.wingArea
    b = ref.dimensions.wingspan
    nEng = ref.propulsion.numberOfEngines
    eCruise = ref.aerodynamics.liftToDragRatioCruise
    hCruise = ref.performance.cruiseAltitude
    caMaxTo = ref.assumptions.maxTakeOffLiftCoefficient
    caMaxL = ref.aerodynamics.maxLandingLiftCoefficient

    # electric aircraft
    kTO = bat.assumptions.kTakeOff
    vSMax = bat.assumptions.maxStallSpeed * 0.5144  # transfer to SI units
    lA = bat.assumptions.obstacleClearance
    A = bat.assumptions.reverseThrustFactorA
    gammaMinOei = bat.assumptions.minClimbGradient
    mClimbRatio = bat.assumptions.massClimbRatio
    oswaldE = bat.assumptions.oswaldFactor
    fOverFcr = bat.assumptions.maxThrustOverCruiseThrustRatio
    mCrRatio = bat.assumptions.maxMassOverCruiseMassRatio
    mlwRatio = bat.assumptions.maxMassOverLandingMassRatio

    Lambda = b**2 / Sref                                # (A.1) aspect ratio
    cW0 = np.pi * Lambda * oswaldE / (4 * eCruise**2)   # from E_max = 0.5*sqrt(pi*Lambda*e/cW0)
    eps = 1 / eCruise                                   # (A.2) eps = CW/CA
    sigma = isaDensity(fieldElevation, rho0) / rho0     # 1, because start at standard density
    rhoCr = isaDensity(hCruise, rho0)                   # density at cruise height
    qCr = 0.5 * rhoCr * vCruise**2                      # dynamic pressure
    x = np.linspace(50, 600, 800)                       # m0/S in kg/m^2, needed for plotting everything

    # (G.2) stall speed vertical line
    xStall = caMaxL * rho0 / (2 * g) * vSMax**2
    # (F.8) takeoff field length line through origin
    yTo = kTO / (caMaxTo * sigma * sTofl) * x
    # (H.2) OEI climb gradient horizontal line
    yClimb = mClimbRatio * nEng / (nEng - 1) * (gammaMinOei + eps) * np.ones_like(x)
    # (I.1) cruise curve
    yCruise = fOverFcr * (cW0 * qCr / (x * g) + x * g / (qCr * np.pi * Lambda * oswaldE) * mCrRatio**2)
    # (K.6) landing distance vertical line
    xLanding = mlwRatio * (lLdg - lA) * sigma * caMaxL / (0.51 * A * g)

    # calculate design point
    yReq = np.maximum.reduce([yTo, yClimb, yCruise])
    feasible = x <= min(xStall, xLanding)
    idx = np.flatnonzero(feasible & (yReq <= yReq[feasible].min() * (1 + 1e-6)))[-1]
    designPoint = (x[idx], yReq[idx])

    print("")
    print(f"Aspect ratio:                      {Lambda:.2f}")
    print(f"Cruise lift to drag ratio:         {eCruise:.2f}")
    print(f"Cruise speed:                      {vCruise:.2f} m/s")
    print(f"Cruise air density:                {rhoCr:.4f} kg/m^3")
    print(f"Cruise dynamic pressure:           {qCr:.2f} Pa")
    print(f"Max. wing loading (stall):         {xStall:.2f} kg/m^2")
    print(f"Max. wing loading (landing):       {xLanding:.2f} kg/m^2")
    print(f"Take-off thrust loading:           {yTo[idx]:.4f}")
    print(f"OEI climb thrust loading:          {yClimb[idx]:.4f}")
    print(f"Cruise thrust loading:             {yCruise[idx]:.4f}")
    print(f"Active thrust constraint:          {['take-off', 'OEI climb', 'cruise'][np.argmax([yTo[idx], yClimb[idx], yCruise[idx]])]}")
    print(f"Limiting wing loading:             {'stall' if xStall < xLanding else 'landing'}")
    print(f"DESIGN WING LOADING:               {designPoint[0]:.2f} kg/m^2")
    print(f"DESIGN THRUST LOADING:             {designPoint[1]:.4f}")
    print("")

    # plot
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axvline(xStall, color="red", ls="--", label="Überziehgeschwindigkeit (G.2)")
    ax.plot(x, yTo, label="Startstrecke (F.8)")
    ax.plot(x, yClimb, label="Steiggradient OEI (H.2)")
    ax.plot(x, yCruise, label="Reiseflug (I.1)")
    ax.plot(*designPoint, "ko", label="Entwurfspunkt")
    ax.axvline(xLanding, color="purple", ls="--", label="Landestrecke (K.6)")
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(0, 0.6)
    ax.set_xlabel(r"$m_0/S$ in kg m$^{-2}$")
    ax.set_ylabel(r"$F/(m_0\cdot g)$ (–)")
    ax.set_title("Entwurfsdiagramm")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    plt.tight_layout()
    plt.show()
    
    return designPoint
