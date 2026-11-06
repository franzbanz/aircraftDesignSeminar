"""Sizing diagram (Matching Chart) for wing loading and thrust loading determination."""

import warnings

import matplotlib.pyplot as plt
import numpy as np

from constants import GRAVITY, RHO_0, isa_density
from data import (
    Constraints,
    DesignParameters,
    SiValue,
    UnitValue,
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


class SizingDiagram:
    """Calculates performance constraint curves, limits, and the optimum design point."""

    def __init__(
        self,
        constraints: Constraints | None = None,
        design: DesignParameters | None = None,
    ) -> None:
        # TODO remove inline loader
        self.constraints = constraints or load_constraints()
        self.design = design or load_design_parameters()

        # Constraints
        self.s_tofl = self.constraints.performance.takeOffFieldLengthMax.si
        self.l_ldg = self.constraints.performance.landingFieldLengthMax.si
        self.field_elevation = self.constraints.performance.takeOffAltitude.si
        # CS-23 certification requirements
        self.v_s_max = self.constraints.cs23.maxStallSpeed.si
        self.gamma_min_oei = self.constraints.cs23.minClimbGradient

        # Electric aircraft design parameters and flight conditions
        self.n_engines = int(self.design.propulsion.numberOfEngines)
        self.l_d_cruise = self.design.aerodynamics.liftToDragRatioCruise
        self.h_cruise = self.design.mission.cruiseAltitude.si
        self.c_a_max_to = self.design.assumptions.maxTakeOffLiftCoefficient
        self.c_a_max_l = self.design.aerodynamics.maxLandingLiftCoefficient
        self.v_cruise = self.design.mission.cruiseSpeedTAS.si

        # Design parameters of the electric aircraft
        self.aspect_ratio = self.design.aerodynamics.aspectRatio
        self.oswald_factor = self.design.aerodynamics.oswaldFactor
        self.thrust_ratio = self.design.propulsion.maxThrustOverCruiseThrustRatio

        # Aerodynamics and atmosphere
        # l_d_cruise is not necessarily the best L/D
        self.c_w0 = np.pi * self.aspect_ratio * self.oswald_factor / (4.0 * self.l_d_cruise**2)
        self.eps = 1.0 / self.l_d_cruise
        self.rho_takeoff = isa_density(self.field_elevation)
        self.rho_cruise = isa_density(self.h_cruise)
        self.q_cruise = 0.5 * self.rho_cruise * (self.v_cruise**2)

        # Performance constraint curves
        self.wing_loadings = np.linspace(5, 600, 800)
        self.x_stall = calc_stall_wing_loading(self.c_a_max_l, RHO_0, self.v_s_max)
        self.y_takeoff = calc_takeoff_thrust_loading(self.n_engines, self.c_a_max_to, self.rho_takeoff, self.s_tofl, self.wing_loadings)
        self.y_climb = calc_oei_climb_thrust_loading(self.n_engines, self.gamma_min_oei, self.eps, self.wing_loadings)
        self.y_cruise = calc_cruise_thrust_loading(self.thrust_ratio, self.c_w0, self.q_cruise, self.aspect_ratio, self.oswald_factor, self.wing_loadings)
        self.x_landing = calc_landing_wing_loading(self.l_ldg, self.rho_takeoff, self.c_a_max_l)

        # Optimum design point determination (minimum thrust loading in feasible region)
        self.y_req = np.maximum.reduce([self.y_takeoff, self.y_climb, self.y_cruise])
        self.feasible = self.wing_loadings <= min(self.x_stall, self.x_landing)
        idx = int(np.flatnonzero(self.feasible & (self.y_req <= self.y_req[self.feasible].min() * (1 + 1e-6)))[-1])
        self.design_point = (self.wing_loadings[idx], self.y_req[idx])

        thrust_constraints = ["take-off", "OEI climb", "cruise"]
        self.active_thrust_constraint = thrust_constraints[int(np.argmax([self.y_takeoff[idx], self.y_climb[idx], self.y_cruise[idx]]))]
        self.limiting_wing_loading = "stall" if self.x_stall < self.x_landing else "landing"

    @property
    def design_wing_loading(self) -> float:
        """Optimum wing loading m_0 / S [kg/m^2]."""
        return self.design_point[0]

    @property
    def design_thrust_loading(self) -> float:
        """Optimum thrust loading T / (m_0 * g) [-]."""
        return self.design_point[1]

    def print_summary(self) -> None:
        """Prints a structured summary of sizing diagram parameters and design point."""
        print("=" * 65)
        print("                      SIZING DIAGRAM SUMMARY")
        print("=" * 65)
        print(f"Aspect ratio:                      {self.aspect_ratio:.2f}")
        print(f"Cruise lift to drag ratio:         {self.l_d_cruise:.2f}")
        print(f"Cruise speed:                      {self.v_cruise:.2f} m/s")
        print(f"Cruise air density:                {self.rho_cruise:.4f} kg/m^3")
        print(f"Cruise dynamic pressure:           {self.q_cruise:.2f} Pa")
        print(f"Max. wing loading (stall):         {self.x_stall:.2f} kg/m^2")
        print(f"Max. wing loading (landing):       {self.x_landing:.2f} kg/m^2")
        print(f"Active thrust constraint:          {self.active_thrust_constraint}")
        print(f"Limiting wing loading:             {self.limiting_wing_loading}")
        print(f"DESIGN WING LOADING:               {self.design_point[0]:.2f} kg/m^2")
        print(f"DESIGN THRUST LOADING:             {self.design_point[1]:.4f}")
        print("=" * 65 + "\n")

    def plot(self) -> None:
        """Plots the sizing diagram (matching chart) with design point and feasible region."""
        fig, ax = plt.subplots(figsize=(10, 6.5))
        ax.plot(
            self.wing_loadings,
            self.y_takeoff,
            color="#1f77b4",
            lw=2,
            label=r"Take-off field length $s_{\mathrm{TOFL}} \leq 800\,\mathrm{m}$ (F.8)",
        )
        ax.plot(
            self.wing_loadings,
            self.y_climb,
            color="#ff7f0e",
            lw=2,
            label=r"Climb gradient OEI $\gamma_{\mathrm{OEI}} \geq 1.5\,\%$ (H.2)",
        )
        ax.plot(
            self.wing_loadings,
            self.y_cruise,
            color="#2ca02c",
            lw=2,
            label=r"Cruise speed $v_{\mathrm{cruise}} = 200\,\mathrm{kts}$ (I.1)",
        )
        ax.axvline(
            self.x_stall,
            color="#d62728",
            lw=2,
            ls="--",
            label=f"Stall speed $v_S \\leq 61\\,\\mathrm{{kts}}$ ({self.x_stall:.1f} kg/m²)",
        )
        ax.axvline(
            self.x_landing,
            color="#9467bd",
            lw=2,
            ls="--",
            label=f"Landing field length $s_{{\\mathrm{{LDG}}}} \\leq 800\\,\\mathrm{{m}}$ ({self.x_landing:.1f} kg/m²)",
        )

        # Feasible design region shading
        x_lim = min(self.x_stall, self.x_landing)
        mask_feas = self.wing_loadings <= x_lim
        y_envelope = np.maximum.reduce([self.y_takeoff, self.y_climb, self.y_cruise])
        ax.fill_between(
            self.wing_loadings[mask_feas],
            y_envelope[mask_feas],
            0.6,
            color="green",
            alpha=0.12,
            label="Feasible Design Region",
        )

        # Design point
        dp = self.design_point
        ax.plot(
            dp[0],
            dp[1],
            marker="*",
            markersize=14,
            color="black",
            label=f"Design Point ({dp[0]:.1f} kg/m², {dp[1]:.4f})",
        )
        ax.annotate(
            f"DP: ({dp[0]:.1f} kg/m², {dp[1]:.4f})",
            xy=dp,
            xytext=(dp[0] - 45, dp[1] + 0.05),
            arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=7),
            fontsize=10,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", fc="yellow", alpha=0.7),
        )

        ax.set_xlim(self.wing_loadings[0], 350)
        ax.set_ylim(0, 0.55)
        ax.set_xlabel(r"Wing Loading $m_0 / S$ [$\mathrm{kg/m}^2$]", fontsize=11)
        ax.set_ylabel(r"Thrust-to-Weight Ratio $T / (m_0 \cdot g)$ [–]", fontsize=11)
        ax.set_title("Sizing Diagram (Matching Chart) – Electric Aircraft", fontsize=13, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    diagram = SizingDiagram()
    diagram.print_summary()
    diagram.plot()
