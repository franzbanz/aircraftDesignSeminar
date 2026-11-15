"""Empennage sizing and calibrated mass estimation for the battery-electric aircraft."""

from __future__ import annotations

from typing import TYPE_CHECKING

from data import SiValue
from formulas.aerodynamics import calc_tailplane_drag_area
from formulas.geometry import calc_horizontal_tail_area, calc_vertical_tail_area
from formulas.mass import (
    calc_empennage_mass,
    calc_empennage_mass_transport,
)

if TYPE_CHECKING:
    from data import DesignParameters
    from reference_aircraft import ReferenceAircraft
    from wing import WingDesign


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
        method = self.design.empennage.massMethod
        if method == "transport":
            v_d = SiValue(1.25 * self.design.mission.cruiseSpeedTAS.si, "m/s")
            raw = calc_empennage_mass_transport(
                v_d,
                self.horizontal_tail_area,
                self.vertical_tail_area,
            )
        elif method == "small":
            n_ult = self.design.assumptions.limitLoad * 1.5
            raw = calc_empennage_mass(
                n_ult, self.horizontal_tail_area, self.vertical_tail_area
            )
        else:
            msg = f"Unknown empennage massMethod: '{method}'. Expected 'transport' or 'small'."
            raise ValueError(msg)
        return SiValue(
            raw
            * self.ref.empennage_calibration_factor
            * self.design.empennage.technologyFactor,
            "kg",
        )

    @property
    def horizontal_tail_drag_area(self) -> SiValue:
        """Horizontal tailplane parasite drag area f_HTP [m^2]."""
        return calc_tailplane_drag_area(
            velocity=self.design.mission.cruiseSpeedTAS.si,
            altitude=self.design.mission.cruiseAltitude.si,
            area=self.horizontal_tail_area,
            aspect_ratio=4.5,
        )

    @property
    def vertical_tail_drag_area(self) -> SiValue:
        """Vertical tailplane parasite drag area f_VTP [m^2]."""
        return calc_tailplane_drag_area(
            velocity=self.design.mission.cruiseSpeedTAS.si,
            altitude=self.design.mission.cruiseAltitude.si,
            area=self.vertical_tail_area,
            aspect_ratio=1.5,
        )

    @property
    def drag_area(self) -> SiValue:
        """Total empennage (HTP + VTP) parasite drag area f_empennage [m^2]."""
        return SiValue(
            self.horizontal_tail_drag_area + self.vertical_tail_drag_area, "m^2"
        )
