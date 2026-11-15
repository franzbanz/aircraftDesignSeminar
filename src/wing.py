"""Wing and aerodynamic polar design calculations for the battery-electric aircraft."""

from __future__ import annotations

from typing import TYPE_CHECKING

from data import SiValue
from formulas.aerodynamics import calc_wing_zero_lift_drag_coefficient
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
    """Encapsulates wing geometry, calibrated wing mass, and wing parasite drag."""

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
    def root_thickness(self) -> SiValue:
        """Wing thickness at root t_root = c_mu * rel_thickness [m]."""
        rel_t = self.design.wing.relWingThickness.value
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
            delta_m_F=self.design.wing.wingMassPenaltyFactor.value,
        )
        relief = 1.0 - self.design.wing.bendingReliefFactor.value
        return SiValue(
            raw
            * self.ref.wing_calibration_factor
            * relief
            * self.design.wing.technologyFactor,
            "kg",
        )

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
    def drag_area(self) -> SiValue:
        """Wing parasite drag area f_wing = c_W0,wing * S_W [m^2]."""
        return SiValue(self.wing_zero_lift_drag_coefficient * self.area, "m^2")
