"""Sizing diagram (Matching Chart) for wing loading and thrust loading determination."""

import warnings

import numpy as np

from constants import GRAVITY, RHO_0, isa_density
from data import (
    Constraints,
    DesignParameters,
    SiValue,
    load_constraints,
    load_design_parameters,
)
from formulas.aerodynamics import calc_cruise_lift_coefficient, calc_dynamic_pressure
from reference_aircraft import ReferenceAircraft, load_reference_aircraft


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
        + wing_loading
        * GRAVITY
        / (q_cruise * np.pi * aspect_ratio * oswald_factor)
        * m_cruise_ratio**2
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
    l_A = SiValue(
        183.0, "m"
    )  # CS-23 standard air distance over 50 ft obstacle (600 ft)
    A = 1.0  # CS-23 standard braking factor (wheel brakes only)
    return SiValue(
        mlw_ratio
        * (l_ldg - l_A)
        * (rho_takeoff / RHO_0)
        * c_a_max_l
        / (0.51 * A * GRAVITY),
        "kg/m^2",
    )


class SizingDiagram:
    """Calculates performance constraint curves, limits, and the optimum design point."""

    def __init__(
        self,
        constraints: Constraints | None = None,
        design: DesignParameters | None = None,
        ref: ReferenceAircraft | None = None,
    ) -> None:
        # TODO remove inline loader
        self.constraints = constraints or load_constraints()
        self.design = design or load_design_parameters()
        self.ref = ref or load_reference_aircraft()

        # Constraints
        self.s_tofl = self.constraints.performance.takeOffFieldLengthMax.si
        self.l_ldg = self.constraints.performance.landingFieldLengthMax.si
        self.field_elevation = self.constraints.performance.takeOffAltitude.si
        # CS-23 certification requirements
        self.v_s_max = self.constraints.cs23.maxStallSpeed.si
        self.gamma_min_oei = self.constraints.cs23.minClimbGradient

        # Electric aircraft design parameters and flight conditions
        self.n_engines = int(self.design.propulsion.numberOfEngines)
        self.h_cruise = self.design.mission.cruiseAltitude.si
        self.c_a_max_to = self.design.assumptions.maxTakeOffLiftCoefficient
        self.c_a_max_l = self.design.aerodynamics.maxLandingLiftCoefficient
        self.v_cruise = self.design.mission.cruiseSpeedTAS.si

        # Design parameters of the electric aircraft
        self.aspect_ratio = self.design.aerodynamics.aspectRatio
        self.oswald_factor = self.design.aerodynamics.oswaldFactor
        self.thrust_ratio = self.design.propulsion.maxThrustOverCruiseThrustRatio

        # Aerodynamics and atmosphere
        self.c_w0 = self.ref.zero_lift_drag_coefficient
        self.rho_takeoff = isa_density(self.field_elevation)
        self.rho_cruise = isa_density(self.h_cruise)
        self.q_cruise = calc_dynamic_pressure(self.v_cruise, self.h_cruise)

        # Performance constraint curves
        self.wing_loadings = np.linspace(5, 600, 800)
        self.x_stall = calc_stall_wing_loading(self.c_a_max_l, RHO_0, self.v_s_max)
        self.x_landing = calc_landing_wing_loading(
            self.l_ldg, self.rho_takeoff, self.c_a_max_l
        )

        # Evaluate cruise L/D from polar at limiting wing loading
        x_lim = float(min(self.x_stall, self.x_landing))
        c_l_cruise = calc_cruise_lift_coefficient(x_lim, self.v_cruise, self.h_cruise)
        self.l_d_cruise = self.ref.lift_to_drag_from_polar(c_l_cruise)
        self.eps = 1.0 / self.l_d_cruise

        self.y_takeoff = calc_takeoff_thrust_loading(
            self.n_engines,
            self.c_a_max_to,
            self.rho_takeoff,
            self.s_tofl,
            self.wing_loadings,
        )
        self.y_climb = calc_oei_climb_thrust_loading(
            self.n_engines, self.gamma_min_oei, self.eps, self.wing_loadings
        )
        self.y_cruise = calc_cruise_thrust_loading(
            self.thrust_ratio,
            self.c_w0,
            self.q_cruise,
            self.aspect_ratio,
            self.oswald_factor,
            self.wing_loadings,
        )

        # Optimum design point determination (minimum thrust loading in feasible region)
        self.y_req = np.maximum(np.maximum(self.y_takeoff, self.y_climb), self.y_cruise)
        self.feasible = self.wing_loadings <= min(self.x_stall, self.x_landing)
        idx = int(
            np.flatnonzero(
                self.feasible
                & (self.y_req <= self.y_req[self.feasible].min() * (1 + 1e-6))
            )[-1]
        )
        self.design_point = (self.wing_loadings[idx], self.y_req[idx])

        # Evaluate cruise L/D from polar at the determined design point
        c_l_cruise = calc_cruise_lift_coefficient(
            self.design_point[0], self.v_cruise, self.h_cruise
        )
        self.l_d_cruise = self.ref.lift_to_drag_from_polar(c_l_cruise)

        thrust_constraints = ["take-off", "OEI climb", "cruise"]
        self.active_thrust_constraint = thrust_constraints[
            int(np.argmax([self.y_takeoff[idx], self.y_climb[idx], self.y_cruise[idx]]))
        ]
        self.limiting_wing_loading = (
            "stall" if self.x_stall < self.x_landing else "landing"
        )

    @property
    def design_wing_loading(self) -> float:
        """Optimum wing loading m_0 / S [kg/m^2]."""
        return self.design_point[0]

    @property
    def design_thrust_loading(self) -> float:
        """Optimum thrust loading T / (m_0 * g) [-]."""
        return self.design_point[1]


if __name__ == "__main__":
    from visualizations.sizing_diagram import plot_sizing_diagram, print_sizing_diagram

    diagram = SizingDiagram()
    print_sizing_diagram(diagram)
    plot_sizing_diagram(diagram)
