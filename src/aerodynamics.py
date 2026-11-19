from __future__ import annotations

import math
from typing import TYPE_CHECKING

from data import SiValue
from formulas.aerodynamics import calc_cruise_lift_coefficient

if TYPE_CHECKING:
    from data import DesignParameters
    from empennage import EmpennageDesign
    from fuselage import FuselageDesign
    from reference_aircraft import ReferenceAircraft
    from wing import WingDesign


class AerodynamicDesign:
    """Whole-aircraft zero-lift drag buildup and cruise polar."""

    def __init__(
        self,
        design: DesignParameters,
        ref: ReferenceAircraft,
        wing: WingDesign,
        fuselage: FuselageDesign,
        empennage: EmpennageDesign,
    ) -> None:
        self.design = design
        self.ref = ref
        self.wing = wing
        self.fuselage = fuselage
        self.empennage = empennage

    @property
    def total_drag_area(self) -> SiValue:
        """Total aircraft parasite drag area f = sum(c_D0 * S) [m^2]."""
        return SiValue(
            self.wing.drag_area
            + self.fuselage.drag_area
            + self.empennage.drag_area
            + self.ref.misc_drag_area,
            "m^2",
        )

    @property
    def zero_lift_drag_coefficient(self) -> float:
        """Total aircraft zero-lift drag coefficient c_W0 referenced to wing area S_W [-]."""
        return self.total_drag_area / self.wing.area

    @property
    def cruise_lift_coefficient(self) -> float:
        """Cruise lift coefficient C_L = (m_0 / S) * g / q [-]."""
        return calc_cruise_lift_coefficient(
            self.wing.wing_loading_design,
            self.design.mission.cruiseSpeedTAS.si,
            self.design.mission.cruiseAltitude.si,
        )

    @property
    def induced_drag_coefficient(self) -> float:
        """Cruise induced drag coefficient c_Wi = C_L^2 / (pi * AR * e) [-]."""
        return (self.cruise_lift_coefficient**2) / (
            math.pi * self.wing.aspect_ratio * self.design.aerodynamics.oswaldFactor
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
