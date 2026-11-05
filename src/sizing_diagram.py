from formulas.geometry import aspect_ratio
from formulas.propulsion import calc_thrust_loading_from_electric_power
from data import SiValue, UnitValue, load_constraints, load_reference_aircraft, load_design_parameters
import json
import warnings
import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace
from constants import GRAVITY, RHO_0, isa_density

def hook(d):
    return SimpleNamespace(**{k: UnitValue(v[0], v[1]) if isinstance(v, list) and len(v) == 2 else v
                              for k, v in d.items()})


def calc_stall_wing_loading(caMaxL: float, rho0: SiValue, vSMax: SiValue) -> SiValue:
    """Calculates maximum allowable wing loading from stall speed [Strohmayer - Flugzeugentwurf 2 | p. 105] [kg/m^2].

    Args:
        caMaxL: Maximum landing lift coefficient c_A,max,L [-].
        rho0: Take-off air density rho_0 [kg/m^3].
        vSMax: Maximum stall speed v_S,max [m/s].

    Returns:
        Maximum allowable wing loading for stall speed [kg/m^2].
    """
    return SiValue(caMaxL * rho0 / (2 * GRAVITY) * vSMax**2, "kg/m^2")


def calc_takeoff_thrust_loading(
    n_engines: int,
    caMaxTo: float,
    sigma: float,
    sTofl: SiValue,
    x: np.ndarray,
) -> np.ndarray:
    """Calculates required take-off thrust loading T/G as a function of wing loading [Strohmayer - Flugzeugentwurf 2 | p. 82] [-].

    Args:
        n_engines: Number of engines [-].
        caMaxTo: Maximum take-off lift coefficient c_A,max,TO [-].
        sigma: Relative air density ratio rho / rho_0 [-].
        sTofl: Required take-off field length s_TOFL [m].
        x: Wing loading array m_0 / S [kg/m^2].

    Returns:
        Required take-off thrust loading array T/G [-].
    """
    k_to_map = {2: 2.45, 3: 2.26, 4: 2.06}
    if (n := int(n_engines)) not in k_to_map:
        warnings.warn(f"kTO only defined for 2, 3, 4 engines (got {n_engines}).")
    kTO = k_to_map.get(n, 2.45 if n < 2 else 2.06)

    return kTO / (caMaxTo * sigma * sTofl) * x


def calc_oei_climb_thrust_loading(
    mClimbRatio: float,
    nEng: int,
    gammaMinOei: float,
    eps: float,
    x: np.ndarray,
) -> np.ndarray:
    """Calculates required OEI 2nd segment climb thrust loading T/G [Strohmayer - Flugzeugentwurf 2 | p. 86] [-].

    Args:
        mClimbRatio: Ratio of climb mass to take-off mass m_climb / m_0 [-].
        nEng: Number of engines n [-].
        gammaMinOei: Minimum climb gradient with one engine inoperative [-].
        eps: Inverse glide ratio in climb eps = c_W / c_A [-].
        x: Wing loading array m_0 / S [kg/m^2].

    Returns:
        Required OEI climb thrust loading array T/G [-].
    """
    return mClimbRatio * nEng / (nEng - 1) * (gammaMinOei + eps) * np.ones_like(x)


def calc_cruise_thrust_loading(
    fOverFcr: float,
    cW0: float,
    qCr: float,
    Lambda: float,
    oswaldE: float,
    mCrRatio: float,
    x: np.ndarray,
) -> np.ndarray:
    """Calculates required cruise thrust loading T/G as a function of wing loading [Strohmayer - Flugzeugentwurf 2 | p. 92] [-].

    Args:
        fOverFcr: Ratio of maximum take-off thrust to cruise thrust F_max / F_cr [-].
        cW0: Zero-lift drag coefficient c_W0 [-].
        qCr: Dynamic pressure in cruise [Pa].
        Lambda: Wing aspect ratio Lambda [-].
        oswaldE: Oswald efficiency factor e [-].
        mCrRatio: Ratio of cruise mass to take-off mass m_cr / m_0 [-].
        x: Wing loading array m_0 / S [kg/m^2].

    Returns:
        Required cruise thrust loading array T/G [-].
    """
    return fOverFcr * (
        cW0 * qCr / (x * GRAVITY)
        + x * GRAVITY / (qCr * np.pi * Lambda * oswaldE) * mCrRatio**2
    )


def calc_landing_wing_loading(
    mlwRatio: float,
    lLdg: SiValue,
    sigma: float,
    caMaxL: float,
) -> SiValue:
    """Calculates maximum allowable wing loading from landing field length [Strohmayer - Flugzeugentwurf 2 | p. 106] [kg/m^2].

    Args:
        mlwRatio: Ratio of take-off mass to maximum landing mass m_0 / m_MLW [-].
        lLdg: Available landing field length [m].
        sigma: Relative air density ratio rho / rho_0 [-].
        caMaxL: Maximum landing lift coefficient c_A,max,L [-].

    Returns:
        Maximum allowable wing loading for landing [kg/m^2].
    """
    lA = SiValue(183.0, "m")  # CS-23 standard air distance over 50 ft obstacle (600 ft)
    A = 1.0                   # CS-23 standard braking factor (wheel brakes only)
    return SiValue(mlwRatio * (lLdg - lA) * sigma * caMaxL / (0.51 * A * GRAVITY), "kg/m^2")


def getDesignPoint(should_plot: bool = False):
    constraints = load_constraints()
    ref = load_reference_aircraft()
    design = load_design_parameters()

    # constraints
    sTofl = constraints.performance.takeOffFieldLengthMax.si
    lLdg = constraints.performance.landingFieldLengthMax.si
    fieldElevation = constraints.performance.takeOffAltitude.si
    vCruise = constraints.performance.cruiseSpeedMin.si

    # ref aircraft
    Sref = ref.dimensions.wingArea.si
    b = ref.dimensions.wingspan.si
    nEng = int(ref.propulsion.numberOfEngines)
    eCruise = ref.aerodynamics.liftToDragRatioCruise
    hCruise = ref.performance.cruiseAltitude.si
    caMaxTo = ref.assumptions.maxTakeOffLiftCoefficient
    caMaxL = ref.aerodynamics.maxLandingLiftCoefficient

    # CS-23 certification requirements
    vSMax = constraints.cs23.maxStallSpeed.si
    gammaMinOei = constraints.cs23.minClimbGradient.value

    # electric aircraft
    oswaldE = design.aerodynamics.oswaldFactor
    fOverFcr = design.propulsion.maxThrustOverCruiseThrustRatio

    Lambda = aspect_ratio(b, Sref)
    cW0 = np.pi * Lambda * oswaldE / (4 * eCruise**2)   # from E_max = 0.5*sqrt(pi*Lambda*e/cW0)
    eps = 1 / eCruise                                   # (A.2) eps = CW/CA
    sigma = isa_density(fieldElevation) / RHO_0         # 1, because start at standard density
    rhoCr = isa_density(hCruise)                        # density at cruise height
    qCr = 0.5 * rhoCr * vCruise**2                      # dynamic pressure
    x = np.linspace(5, 600, 800)                        # m0/S in kg/m^2, needed for plotting everything

    xStall = calc_stall_wing_loading(caMaxL, RHO_0, vSMax)
    yTo = calc_takeoff_thrust_loading(nEng, caMaxTo, sigma, sTofl, x)
    yClimb = calc_oei_climb_thrust_loading(1, nEng, gammaMinOei, eps, x)
    yCruise = calc_cruise_thrust_loading(fOverFcr, cW0, qCr, Lambda, oswaldE, 1, x)
    xLanding = calc_landing_wing_loading(1, lLdg, sigma, caMaxL)

    # calculate design point
    yReq = np.maximum.reduce([yTo, yClimb, yCruise])
    feasible = x <= min(xStall, xLanding)
    idx = np.flatnonzero(feasible & (yReq <= yReq[feasible].min() * (1 + 1e-6)))[-1]
    designPoint = (x[idx], yReq[idx])
    """
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
    """
    if should_plot:
        _, ax = plt.subplots(figsize=(9, 6))
        ax.axvline(xStall, color="red", ls="--", label="Stall speed (G.2)")
        ax.plot(x, yTo, label="Take-off field length (F.8)")
        ax.plot(x, yClimb, label="Climb gradient OEI (H.2)")
        ax.plot(x, yCruise, label="Cruise (I.1)")
        ax.plot(*designPoint, "ko", label="Design point")
        ax.axvline(xLanding, color="purple", ls="--", label="Landing field length (K.6)")
        ax.set_xlim(x[0], x[-1])
        ax.set_ylim(0, 0.6)
        ax.set_xlabel(r"$m_0/S$ in kg m$^{-2}$")
        ax.set_ylabel(r"$T/(m_0\cdot g)$ (–)")
        ax.set_title("Sizing Diagram")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")
        plt.tight_layout()
        plt.show()
    
    return designPoint

if __name__ == "__main__":
    getDesignPoint(True)
