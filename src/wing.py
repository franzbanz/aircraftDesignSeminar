"""Wing and aerodynamic polar design calculations for the battery-electric aircraft."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from data import SiValue
from formulas.aerodynamics import (
    calc_cruise_lift_coefficient,
    calc_wing_zero_lift_drag_coefficient,
)
from formulas.geometry import (
    calc_aspect_ratio,
    calc_mean_aerodynamic_chord,
    calc_wingspan,
)
from formulas.mass import calc_wing_mass

if TYPE_CHECKING:
    from data import Constraints, DesignParameters
    from reference_aircraft import ReferenceAircraft


class WingDesign:
    """Encapsulates wing geometry, calibrated wing mass, and cruise polar evaluation."""

    def __init__(
        self,
        constraints: Constraints,
        design: DesignParameters,
        ref: ReferenceAircraft,
        mtom: SiValue,
        wing_loading_design: float,
        fuselage_width: SiValue = SiValue(0.0, "m"),
        battery_mass: SiValue = SiValue(0.0, "kg"),
    ) -> None:
        self.constraints = constraints
        self.design = design
        self.ref = ref
        self.mtom = mtom
        self.wing_loading_design = wing_loading_design
        self.fuselage_width = fuselage_width
        self.battery_mass = battery_mass

    @property
    def area(self) -> SiValue:
        """Wing reference area S_W [m^2]."""
        constraint_mtom = self.constraints.performance.takeOffMassMax.si
        mtom = self.mtom if self.mtom < constraint_mtom else constraint_mtom
        return SiValue(mtom / self.wing_loading_design, "m^2")

    @property
    def span(self) -> SiValue:
        """Wingspan b_W [m], constrained to maximum allowable span."""
        b_s = calc_wingspan(self.area, self.design.wing.aspectRatio)
        return min(b_s, self.constraints.performance.wingSpanMax.si)

    @property
    def aspect_ratio(self) -> float:
        """Effective wing aspect ratio b_W^2 / S_W [-]."""
        return calc_aspect_ratio(self.span, self.area)

    @property
    def mean_aerodynamic_chord(self) -> SiValue:
        """Mean aerodynamic chord c_mu [m]."""
        return calc_mean_aerodynamic_chord(self.area, self.span)

    @property
    def x_lemac(self) -> SiValue:
        """Leading edge of the Mean Aerodynamic Chord (LEMAC) station [m]."""
        return self.design.wing.leadingEdgeMeanAerodynamicChordPosition.si

    @property
    def x_ac(self) -> SiValue:
        """Wing aerodynamic center at 25% MAC [m]."""
        return SiValue(self.x_lemac + 0.25 * self.mean_aerodynamic_chord, "m")

    @property
    def cog(self) -> SiValue:
        """Wing structural center of gravity at 42% MAC [m] [Strohmayer - Flugzeugentwurf 2 | p. 131]."""
        return SiValue(self.x_lemac + 0.42 * self.mean_aerodynamic_chord, "m")

    @property
    def root_thickness(self) -> SiValue:
        """Wing thickness at root t_root = c_mu * rel_thickness [m]."""
        rel_t = self.design.wing.relWingThickness.value
        return SiValue(self.mean_aerodynamic_chord * rel_t, "m")

    @property
    def effective_mzfm(self) -> SiValue:
        """Effective zero-fuel mass accounting for wing-mounted battery bending relief [kg]."""
        m_bat_wing = self.design.wing.batteryWingMassFraction * self.battery_mass
        if m_bat_wing <= 0:
            return self.mtom
        y_root = self.fuselage_width / 2.0
        half_span = self.span / 2.0
        # Centroid of a quarter-ellipse: aerodynamic center of lift for elliptical distribution
        y_aero = (4.0 / (3.0 * math.pi)) * half_span
        # Lever arms relative to the wing-fuselage root attachment y_root
        r_aero = max(0.0, y_aero - y_root)
        r_bat = max(0.0, self.design.wing.batterySpanwisePosition.si - y_root)
        # Ratio of battery relief moment to lift bending moment at wing root
        kappa_bat = r_bat / r_aero if r_aero > 0 else 0.0
        return SiValue(max(0.0, self.mtom - kappa_bat * m_bat_wing), "kg")

    def _calc_calibrated_mass(self, mzfm: SiValue) -> SiValue:
        raw = calc_wing_mass(
            mzfm=mzfm,
            b_s=self.span,
            n_ult=self.design.assumptions.limitLoad * 1.5,
            d_root=self.root_thickness,
            s_w=self.area,
            delta_m_F=self.design.wing.wingMassPenaltyFactor.value,
        )
        return SiValue(
            raw * self.ref.wing_calibration_factor * self.design.wing.technologyFactor,
            "kg",
        )

    @property
    def unrelieved_mass(self) -> SiValue:
        """Calibrated wing structural mass without battery bending relief [kg]."""
        return self._calc_calibrated_mass(self.mtom)

    @property
    def mass(self) -> SiValue:
        """Calibrated wing structural mass [kg]."""
        return self._calc_calibrated_mass(self.effective_mzfm)

    @property
    def bending_relief_factor(self) -> float:
        """Effective wing bending relief factor resulting from wing battery mass and spanwise lever arm [-]."""
        if self.effective_mzfm >= self.mtom:
            return 0.0
        return 1.0 - self.mass / self.unrelieved_mass

    @property
    def wing_zero_lift_drag_coefficient(self) -> float:
        """Zero-lift drag coefficient of the new wing c_W0,wing [-]."""
        return calc_wing_zero_lift_drag_coefficient(
            velocity=self.design.mission.cruiseSpeedTAS.si,
            altitude=self.design.mission.cruiseAltitude.si,
            mean_aerodynamic_chord=self.mean_aerodynamic_chord,
            rel_thickness=self.design.wing.relWingThickness,
            sweep_deg=self.design.wing.wingSweepHalfChord,
        )

    @property
    def zero_lift_drag_coefficient(self) -> float:
        """Total aircraft zero-lift drag coefficient c_W0 referenced to new wing area S_W [-]."""
        # TODO: Account for increased zero-lift drag of enlarged empennage surfaces (S_HTP, S_VTP)
        c_w0_rest_ref = (
            self.ref.zero_lift_drag_coefficient
            - self.ref.wing_zero_lift_drag_coefficient
        )
        s_w_ref = self.ref.data.dimensions.wingArea.si
        return self.wing_zero_lift_drag_coefficient + c_w0_rest_ref * (
            s_w_ref / self.area
        )

    @property
    def cruise_lift_coefficient(self) -> float:
        """Cruise lift coefficient C_L = (m_0 / S) * g / q [-]."""
        return calc_cruise_lift_coefficient(
            self.wing_loading_design,
            self.design.mission.cruiseSpeedTAS.si,
            self.design.mission.cruiseAltitude.si,
        )

    @property
    def induced_drag_coefficient(self) -> float:
        """Cruise induced drag coefficient c_Wi = C_L^2 / (pi * AR * e) [-]."""
        return (self.cruise_lift_coefficient**2) / (
            math.pi * self.aspect_ratio * self.design.aerodynamics.oswaldFactor
        )

    @property
    def cruise_drag_coefficient(self) -> float:
        """Total cruise drag coefficient C_D = c_W0 + c_Wi [-]."""
        return self.zero_lift_drag_coefficient + self.induced_drag_coefficient

    @property
    def lift_to_drag_cruise(self) -> float:
        """Cruise lift-to-drag ratio L/D = C_L / C_D [-]."""
        override = self.design.aerodynamics.liftToDragRatioCruise
        if override == "reference":
            return self.ref.data.aerodynamics.liftToDragRatioCruise
        if isinstance(override, str):
            msg = (
                f"Unknown liftToDragRatioCruise: '{override}'. "
                "Expected null, 'reference', or a [value, ''] pair."
            )
            raise ValueError(msg)
        if override is not None:
            return override
        return self.cruise_lift_coefficient / self.cruise_drag_coefficient
