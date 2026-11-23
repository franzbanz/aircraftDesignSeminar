"""Empennage sizing and calibrated mass estimation for the battery-electric aircraft."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from data import SiValue
from formulas.geometry import calc_horizontal_tail_area, calc_vertical_tail_area
from formulas.mass import (
    calc_empennage_mass,
    calc_tailplane_mass,
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
    def horizontal_tail_mac(self) -> SiValue:
        """Horizontal tailplane mean aerodynamic chord c_mu,HTP [m]."""
        return SiValue(
            math.sqrt(
                self.horizontal_tail_area
                / self.design.empennage.horizontalTailAspectRatio
            ),
            "m",
        )

    @property
    def vertical_tail_mac(self) -> SiValue:
        """Vertical tailplane mean aerodynamic chord c_mu,VTP [m]."""
        return SiValue(
            math.sqrt(
                self.vertical_tail_area / self.design.empennage.verticalTailAspectRatio
            ),
            "m",
        )

    @property
    def x_htp_ac(self) -> SiValue:
        """Aerodynamic center of the horizontal tailplane at 25% HTP MAC [m]."""
        return SiValue(self.wing.x_ac + self.ref.horizontal_tail_lever_arm.si, "m")

    @property
    def htp_cog(self) -> SiValue:
        """Horizontal tailplane center of gravity at 42% HTP MAC [m] [Strohmayer - Flugzeugentwurf 2 | p. 131]."""
        return SiValue(self.x_htp_ac + 0.17 * self.horizontal_tail_mac, "m")

    @property
    def vtp_cog(self) -> SiValue:
        """Vertical tailplane center of gravity at 42% VTP MAC [m] [Strohmayer - Flugzeugentwurf 2 | p. 131]."""
        return SiValue(
            self.wing.x_ac
            + self.ref.vertical_tail_lever_arm.si
            + 0.17 * self.vertical_tail_mac,
            "m",
        )

    def _calibrate_mass(self, raw: SiValue) -> SiValue:
        """Applies reference calibration and composite technology factor [kg]."""
        return SiValue(
            raw
            * self.ref.empennage_calibration_factor
            * self.design.empennage.technologyFactor,
            "kg",
        )

    @property
    def horizontal_tail_mass(self) -> SiValue:
        """Calibrated horizontal tailplane mass [kg]."""
        if self.design.empennage.massMethod == "transport":
            v_d = SiValue(1.25 * self.design.mission.cruiseSpeedTAS.si, "m/s")
            return self._calibrate_mass(
                calc_tailplane_mass(v_d, self.horizontal_tail_area)
            )
        s_htp = self.horizontal_tail_area
        s_vtp = self.vertical_tail_area
        return SiValue(self.mass * (s_htp / (s_htp + s_vtp)), "kg")

    @property
    def vertical_tail_mass(self) -> SiValue:
        """Calibrated vertical tailplane mass [kg]."""
        if self.design.empennage.massMethod == "transport":
            v_d = SiValue(1.25 * self.design.mission.cruiseSpeedTAS.si, "m/s")
            return self._calibrate_mass(
                calc_tailplane_mass(v_d, self.vertical_tail_area)
            )
        s_htp = self.horizontal_tail_area
        s_vtp = self.vertical_tail_area
        return SiValue(self.mass * (s_vtp / (s_htp + s_vtp)), "kg")

    @property
    def mass(self) -> SiValue:
        """Calibrated total empennage mass [kg]."""
        method = self.design.empennage.massMethod
        if method == "transport":
            return SiValue(self.horizontal_tail_mass + self.vertical_tail_mass, "kg")
        if method == "small":
            n_ult = self.design.assumptions.limitLoad * 1.5
            return self._calibrate_mass(
                calc_empennage_mass(
                    n_ult, self.horizontal_tail_area, self.vertical_tail_area
                )
            )
        msg = f"Unknown empennage massMethod: '{method}'. Expected 'transport' or 'small'."
        raise ValueError(msg)
