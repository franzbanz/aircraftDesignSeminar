"""Wing and aerodynamic polar design calculations for the battery-electric aircraft."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from data import SiValue
from formulas import (
    calc_aspect_ratio,
    calc_cruise_lift_coefficient,
    calc_mean_aerodynamic_chord,
    calc_wing_mass,
    calc_wing_zero_lift_drag_coefficient,
    calc_wingspan,
)

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
    ) -> None:
        self.constraints = constraints
        self.design = design
        self.ref = ref
        self.mtom = mtom
        self.wing_loading_design = wing_loading_design

    @property
    def area(self) -> SiValue:
        """Wing reference area S_W [m^2]."""
        constraint_mtom = self.constraints.performance.takeOffMassMax.si
        mtom = self.mtom if self.mtom < constraint_mtom else constraint_mtom
        return SiValue(mtom / self.wing_loading_design, "m^2")

    @property
    def span(self) -> SiValue:
        """Wingspan b_W [m], constrained to maximum allowable span."""
        b_s = calc_wingspan(self.area, self.design.aerodynamics.aspectRatio)
        return min(b_s, self.design.aerodynamics.maxWingSpan.si)

    @property
    def aspect_ratio(self) -> float:
        """Effective wing aspect ratio b_W^2 / S_W [-]."""
        return calc_aspect_ratio(self.span, self.area)

    @property
    def mean_aerodynamic_chord(self) -> SiValue:
        """Mean aerodynamic chord c_mu [m]."""
        return calc_mean_aerodynamic_chord(self.area, self.span)

    @property
    def root_thickness(self) -> SiValue:
        """Wing thickness at root t_root = c_mu * rel_thickness [m]."""
        rel_t = self.design.aerodynamics.relWingThickness.value
        return SiValue(self.mean_aerodynamic_chord * rel_t, "m")

    @property
    def mass(self) -> SiValue:
        """Calibrated wing structural mass [kg]."""
        raw = calc_wing_mass(
            mzfm=self.mtom,
            b_s=self.span,
            n_ult=self.design.assumptions.limitLoad * 1.5,
            d_root=self.root_thickness,
            s_w=self.area,
            delta_m_F=self.design.assumptions.wingMassPenaltyFactor.value,
        )
        return SiValue(raw * self.ref.wing_calibration_factor, "kg")

    @property
    def wing_zero_lift_drag_coefficient(self) -> float:
        """Zero-lift drag coefficient of the new wing c_W0,wing [-]."""
        return calc_wing_zero_lift_drag_coefficient(
            velocity=self.design.mission.cruiseSpeedTAS.si,
            altitude=self.design.mission.cruiseAltitude.si,
            mean_aerodynamic_chord=self.mean_aerodynamic_chord,
            rel_thickness=self.design.aerodynamics.relWingThickness,
            sweep_deg=self.design.assumptions.wingSweepHalfChord,
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
        return self.cruise_lift_coefficient / self.cruise_drag_coefficient
