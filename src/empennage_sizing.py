"""Empennage sizing and calibrated mass estimation for the battery-electric aircraft."""

from __future__ import annotations

from typing import TYPE_CHECKING

from data import SiValue
from formulas import (
    calc_empennage_mass,
    calc_horizontal_tail_area,
    calc_vertical_tail_area,
)

if TYPE_CHECKING:
    from data import DesignParameters
    from reference_aircraft import ReferenceAircraft
    from wing_design import WingDesign


class EmpennageDesign:
    """Encapsulates horizontal and vertical tailplane sizing and calibrated mass."""

    def __init__(
        self,
        design: DesignParameters,
        ref: ReferenceAircraft,
        wing: WingDesign,
    ) -> None:
        self.design = design
        self.ref = ref
        self.wing = wing

    @property
    def horizontal_tail_area(self) -> SiValue:
        """Horizontal tailplane area S_HTP scaled via volume coefficient [m^2]."""
        c_ht = min(
            self.ref.horizontal_tail_volume_coefficient,
            self.design.empennage.maxHorizontalVolumeCoefficient,
        )
        r_h = self.ref.horizontal_tail_lever_arm.si
        return calc_horizontal_tail_area(
            c_ht, r_h, self.wing.area, self.wing.mean_aerodynamic_chord
        )

    @property
    def vertical_tail_area(self) -> SiValue:
        """Vertical tailplane area S_VTP scaled via volume coefficient [m^2]."""
        c_vt = self.ref.vertical_tail_volume_coefficient
        r_v = self.ref.vertical_tail_lever_arm.si
        return calc_vertical_tail_area(c_vt, r_v, self.wing.area, self.wing.span)

    @property
    def mass(self) -> SiValue:
        """Calibrated empennage mass [kg]."""
        n_ult = self.design.assumptions.limitLoad * 1.5
        raw = calc_empennage_mass(
            n_ult, self.horizontal_tail_area, self.vertical_tail_area
        )
        return SiValue(raw * self.ref.empennage_calibration_factor, "kg")
