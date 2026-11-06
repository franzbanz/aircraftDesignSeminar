"""Sizing diagram (Matching Chart) for wing loading and thrust loading determination."""

import warnings

import matplotlib.pyplot as plt
import numpy as np

from constants import GRAVITY, RHO_0, isa_density
from data import (
    SiValue,
    load_constraints,
    load_design_parameters,
)


def calc_stall_wing_loading(
    c_a_max_l: float,
    rho: SiValue,
    v_s_max: SiValue,
) -> SiValue:
    """Calculates maximum allowable wing loading from stall speed [Strohmayer - Flugzeugentwurf 2 | p. 105] [kg/m^2].

    Args:
        c_a_max_l: Maximum landing lift coefficient c_A,max,L [-].
        rho: Air density rho [kg/m^3].
        v_s_max: Maximum allowable stall speed v_S,max [m/s].

    Returns:
        Maximum allowable wing loading for stall speed [kg/m^2].
    """
    return SiValue(c_a_max_l * rho / (2.0 * GRAVITY) * v_s_max**2, "kg/m^2")


def calc_takeoff_thrust_loading(
    n_engines: int,
    c_a_max_to: float,
    rho_takeoff: SiValue,
    s_tofl: SiValue,
    wing_loading: np.ndarray,
) -> np.ndarray:
    """Calculates required take-off thrust loading T/G as a function of wing loading [Strohmayer - Flugzeugentwurf 2 | p. 82] [-].

    Args:
        n_engines: Number of engines [-].
        c_a_max_to: Maximum take-off lift coefficient c_A,max,TO [-].
        rho_takeoff: Air density at take-off conditions [kg/m^3].
        s_tofl: Required take-off field length s_TOFL [m].
        wing_loading: Wing loading array m_0 / S [kg/m^2].

    Returns:
        Required take-off thrust loading array T/G [-].
    """
    k_to_map = {2: 2.45, 3: 2.26, 4: 2.06}
    if n_engines not in k_to_map:
        warnings.warn(f"k_to only defined for 2, 3, 4 engines (got {n_engines}).")
    k_to = k_to_map.get(n_engines, 2.45 if n_engines < 2 else 2.06)

    return k_to / (c_a_max_to * (rho_takeoff / RHO_0) * s_tofl) * wing_loading


def calc_oei_climb_thrust_loading(
    n_engines: int,
    gamma_min_oei: float,
    eps: float,
    wing_loading: np.ndarray,
    m_climb_ratio: float = 1.0,
) -> np.ndarray:
    """Calculates required OEI 2nd segment climb thrust loading T/G [Strohmayer - Flugzeugentwurf 2 | p. 86] [-].

    Args:
        n_engines: Number of engines n [-].
        gamma_min_oei: Minimum climb gradient with one engine inoperative [-].
        eps: Inverse glide ratio in climb eps = c_W / c_A [-].
        wing_loading: Wing loading array m_0 / S [kg/m^2].
        m_climb_ratio: Ratio of climb mass to take-off mass m_climb / m_0 [-] (defaults to 1.0 for electric aircraft).

    Returns:
        Required OEI climb thrust loading array T/G [-].
    """
    return (
        m_climb_ratio
        * n_engines
        / (n_engines - 1)
        * (gamma_min_oei + eps)
        * np.ones_like(wing_loading)
    )


def calc_cruise_thrust_loading(
    thrust_ratio: float,
    c_w0: float,
    q_cruise: float,
    aspect_ratio: float,
    oswald_factor: float,
    wing_loading: np.ndarray,
    m_cruise_ratio: float = 1.0,
) -> np.ndarray:
    """Calculates required cruise thrust loading T/G as a function of wing loading [Strohmayer - Flugzeugentwurf 2 | p. 92] [-].

    Args:
        thrust_ratio: Ratio of maximum take-off thrust to cruise thrust F_max / F_cr [-].
        c_w0: Zero-lift drag coefficient c_W0 [-].
        q_cruise: Dynamic pressure in cruise [Pa].
        aspect_ratio: Wing aspect ratio Lambda [-].
        oswald_factor: Oswald efficiency factor e [-].
        wing_loading: Wing loading array m_0 / S [kg/m^2].
        m_cruise_ratio: Ratio of cruise mass to take-off mass m_cr / m_0 [-] (defaults to 1.0 for electric aircraft).

    Returns:
        Required cruise thrust loading array T/G [-].
    """
    return thrust_ratio * (
        c_w0 * q_cruise / (wing_loading * GRAVITY)
        + wing_loading * GRAVITY / (q_cruise * np.pi * aspect_ratio * oswald_factor) * m_cruise_ratio**2
    )


def calc_landing_wing_loading(
    l_ldg: SiValue,
    rho_takeoff: SiValue,
    c_a_max_l: float,
    mlw_ratio: float = 1.0,
) -> SiValue:
    """Calculates maximum allowable wing loading from landing field length [Strohmayer - Flugzeugentwurf 2 | p. 106] [kg/m^2].

    Args:
        l_ldg: Available landing field length [m].
        rho_takeoff: Air density at take-off conditions [kg/m^3].
        c_a_max_l: Maximum landing lift coefficient c_A,max,L [-].
        mlw_ratio: Ratio of take-off mass to maximum landing mass m_0 / m_MLW [-] (defaults to 1.0 for electric aircraft).

    Returns:
        Maximum allowable wing loading for landing [kg/m^2].
    """
    l_A = SiValue(183.0, "m")  # CS-23 standard air distance over 50 ft obstacle (600 ft)
    A = 1.0                    # CS-23 standard braking factor (wheel brakes only)
    return SiValue(
        mlw_ratio * (l_ldg - l_A) * (rho_takeoff / RHO_0) * c_a_max_l / (0.51 * A * GRAVITY),
        "kg/m^2",
    )


def get_design_point(should_plot: bool = False) -> tuple[float, float]:
    """Calculates the optimum design point (m_0/S, T/G) from CS-23 and performance constraints.

    Args:
        should_plot: Whether to display the sizing diagram plot.

    Returns:
        Tuple of (design_wing_loading [kg/m^2], design_thrust_loading [-]).
    """
    constraints = load_constraints()
    design = load_design_parameters()

    # Constraints
    s_tofl = constraints.performance.takeOffFieldLengthMax.si
    l_ldg = constraints.performance.landingFieldLengthMax.si
    field_elevation = constraints.performance.takeOffAltitude.si
    # CS-23 certification requirements
    v_s_max = constraints.cs23.maxStallSpeed.si
    gamma_min_oei = constraints.cs23.minClimbGradient

    # Electric aircraft design parameters and flight conditions
    n_engines = int(design.propulsion.numberOfEngines)
    l_d_cruise = design.aerodynamics.liftToDragRatioCruise
    h_cruise = design.mission.cruiseAltitude.si
    c_a_max_to = design.assumptions.maxTakeOffLiftCoefficient
    c_a_max_l = design.aerodynamics.maxLandingLiftCoefficient
    v_cruise = design.mission.cruiseSpeedTAS.si

    # Design parameters of the electric aircraft
    aspect_ratio = design.aerodynamics.aspectRatio
    oswald_factor = design.aerodynamics.oswaldFactor
    thrust_ratio = design.propulsion.maxThrustOverCruiseThrustRatio

    # Aerodynamics and atmosphere
    # l_d_cruise is not necessarily the best L/D
    c_w0 = np.pi * aspect_ratio * oswald_factor / (4.0 * l_d_cruise**2)
    eps = 1.0 / l_d_cruise
    rho_takeoff = isa_density(field_elevation)
    rho_cruise = isa_density(h_cruise)
    q_cruise = 0.5 * rho_cruise * v_cruise**2

    # Wing loading range for calculation
    wing_loadings = np.linspace(5, 600, 800)

    # Performance constraint curves
    x_stall = calc_stall_wing_loading(c_a_max_l, RHO_0, v_s_max)
    y_takeoff = calc_takeoff_thrust_loading(n_engines, c_a_max_to, rho_takeoff, s_tofl, wing_loadings)
    y_climb = calc_oei_climb_thrust_loading(n_engines, gamma_min_oei, eps, wing_loadings)
    y_cruise = calc_cruise_thrust_loading(thrust_ratio, c_w0, q_cruise, aspect_ratio, oswald_factor, wing_loadings)
    x_landing = calc_landing_wing_loading(l_ldg, rho_takeoff, c_a_max_l)

    # Optimum design point determination (minimum thrust loading in feasible region)
    y_req = np.maximum.reduce([y_takeoff, y_climb, y_cruise])
    feasible = wing_loadings <= min(x_stall, x_landing)
    idx = np.flatnonzero(feasible & (y_req <= y_req[feasible].min() * (1 + 1e-6)))[-1]
    design_point = (float(wing_loadings[idx]), float(y_req[idx]))
    """
    print("")
    print(f"Aspect ratio:                      {aspect_ratio:.2f}")
    print(f"Cruise lift to drag ratio:         {l_d_cruise:.2f}")
    print(f"Cruise speed:                      {v_cruise:.2f}")
    print(f"Cruise air density:                {rho_cruise:.4f}")
    print(f"Cruise dynamic pressure:           {q_cruise:.2f}")
    print(f"Max. wing loading (stall):         {x_stall:.2f}")
    print(f"Max. wing loading (landing):       {x_landing:.2f}")
    print(f"Take-off thrust loading:           {y_takeoff[idx]:.4f}")
    print(f"OEI climb thrust loading:          {y_climb[idx]:.4f}")
    print(f"Cruise thrust loading:             {y_cruise[idx]:.4f}")
    print(f"Active thrust constraint:          {['take-off', 'OEI climb', 'cruise'][np.argmax([y_takeoff[idx], y_climb[idx], y_cruise[idx]])]}")
    print(f"Limiting wing loading:             {'stall' if x_stall < x_landing else 'landing'}")
    print(f"DESIGN WING LOADING:               {design_point[0]:.2f} kg/m^2")
    print(f"DESIGN THRUST LOADING:             {design_point[1]:.4f}")
    print("")
    """
    if should_plot:
        fig, ax = plt.subplots(figsize=(10, 6.5))
        ax.plot(wing_loadings, y_takeoff, color="#1f77b4", lw=2, label=r"Take-off field length $s_{\mathrm{TOFL}} \leq 800\,\mathrm{m}$ (F.8)")
        ax.plot(wing_loadings, y_climb, color="#ff7f0e", lw=2, label=r"Climb gradient OEI $\gamma_{\mathrm{OEI}} \geq 1.5\,\%$ (H.2)")
        ax.plot(wing_loadings, y_cruise, color="#2ca02c", lw=2, label=r"Cruise speed $v_{\mathrm{cruise}} = 200\,\mathrm{kts}$ (I.1)")
        ax.axvline(x_stall, color="#d62728", lw=2, ls="--", label=f"Stall speed $v_S \\leq 61\\,\\mathrm{{kts}}$ ({x_stall:.1f} kg/m²)")
        ax.axvline(x_landing, color="#9467bd", lw=2, ls="--", label=f"Landing field length $s_{{\\mathrm{{LDG}}}} \\leq 800\\,\\mathrm{{m}}$ ({x_landing:.1f} kg/m²)")

        # Feasible design region shading
        x_lim = min(x_stall, x_landing)
        mask_feas = wing_loadings <= x_lim
        y_envelope = np.maximum.reduce([y_takeoff, y_climb, y_cruise])
        ax.fill_between(
            wing_loadings[mask_feas],
            y_envelope[mask_feas],
            0.6,
            color="green",
            alpha=0.12,
            label="Feasible Design Region",
        )

        # Design point
        ax.plot(design_point[0], design_point[1], marker="*", markersize=14, color="black", label=f"Design Point ({design_point[0]:.1f} kg/m², {design_point[1]:.4f})")
        ax.annotate(
            f"DP: ({design_point[0]:.1f} kg/m², {design_point[1]:.4f})",
            xy=design_point,
            xytext=(design_point[0] - 45, design_point[1] + 0.05),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=7),
            fontsize=10,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", fc="yellow", alpha=0.7),
        )

        ax.set_xlim(wing_loadings[0], 350)
        ax.set_ylim(0, 0.55)
        ax.set_xlabel(r"Wing Loading $m_0 / S$ [$\mathrm{kg/m}^2$]", fontsize=11)
        ax.set_ylabel(r"Thrust-to-Weight Ratio $T / (m_0 \cdot g)$ [–]", fontsize=11)
        ax.set_title("Sizing Diagram (Matching Chart) – Electric Aircraft", fontsize=13, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
        plt.tight_layout()
        plt.show()

    return design_point


if __name__ == "__main__":
    get_design_point(should_plot=True)
