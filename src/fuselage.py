"""Fuselage and cabin geometry design for the 19-passenger commuter aircraft.

Models a rounded-corner rectangular box cross-section and longitudinal layout:
nose (cockpit), passenger cabin directly aft of cockpit (1+1 front rows,
1 starboard door row opposite the 1-row port entry door, and a 3-seat rear bench),
aft baggage compartment, and tailcone, reading cabin dimensions from
design_parameters.json and constraints.json.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from data import SiValue
from formulas.geometry import calc_fuselage_wetted_area
from formulas.mass import calc_fuselage_mass

if TYPE_CHECKING:
    from data import Constraints, DesignParameters
    from reference_aircraft import ReferenceAircraft


class FuselageDesign:
    """Encapsulates cabin seating, cross-section, longitudinal sizing, and mass."""

    def __init__(
        self,
        constraints: Constraints,
        design: DesignParameters,
        ref: ReferenceAircraft,
    ) -> None:
        self.constraints = constraints
        self.design = design
        self.ref = ref
        self.n_pax: int = int(self.design.mission.numberOfPassengers.value)
        if self.n_pax < 5:
            raise ValueError(f"Passenger count must be at least 5, got {self.n_pax}.")
        if self.design.fuselage.cabinLayout not in ("single_door", "dual_door"):
            raise ValueError(
                f"cabinLayout must be 'single_door' or 'dual_door', got {self.design.fuselage.cabinLayout!r}."
            )

    @property
    def cabin_width(self) -> SiValue:
        """Internal cabin width for 1+1 seating layout [m]."""
        fuse = self.design.fuselage
        return SiValue(
            2.0 * fuse.seatWidth.si
            + fuse.aisleWidth.si
            + 2.0 * fuse.wallClearance.si,
            "m",
        )

    @property
    def width(self) -> SiValue:
        """External fuselage width [m]."""
        return SiValue(
            self.cabin_width + 2.0 * self.design.fuselage.wallThickness.si, "m"
        )

    @property
    def height(self) -> SiValue:
        """External fuselage height [m]."""
        fuse = self.design.fuselage
        roof_structure = 0.12  # frames + skin + ceiling panels
        underfloor_h = fuse.underfloorBaggageHeight.si
        belly_wall = fuse.wallThickness.si if underfloor_h > 0 else 0.0
        return SiValue(
            fuse.aisleHeadroom.si
            + roof_structure
            + fuse.floorStructuralDepth.si
            + underfloor_h
            + belly_wall,
            "m",
        )

    @property
    def corner_radius(self) -> SiValue:
        """Outer corner radius of rounded rectangular box cross-section [m]."""
        return SiValue(min(0.20, 0.15 * min(self.width, self.height)), "m")

    @property
    def frontal_area(self) -> SiValue:
        """Cross-sectional frontal area of rounded rectangular fuselage [m^2]."""
        return SiValue(
            self.width * self.height - (4.0 - math.pi) * (self.corner_radius**2),
            "m^2",
        )

    @property
    def _equivalent_diameter(self) -> SiValue:
        """Area-equivalent fuselage diameter d_equiv [m]."""
        return SiValue(math.sqrt(4.0 * self.frontal_area / math.pi), "m")

    @property
    def is_dual_door(self) -> bool:
        """True if cabin uses front RH + rear LH doors without overwing exits."""
        return self.design.fuselage.cabinLayout == "dual_door"

    @property
    def n_door_seats(self) -> int:
        """Starboard seats in the rear port-door row [-]."""
        if self.is_dual_door:
            # Note: 2 seats opposite the rear door may violate the CS-23 escape path for even n_pax.
            return 1 if self.n_pax % 2 == 1 else 2
        return 2 if self.n_pax % 2 == 1 else 1

    @property
    def n_front_rows(self) -> int:
        """Full 1+1 rows between cockpit/front-door row and rear door row [-]."""
        rear_bench_seats = 3
        front_door_row_seats = 1 if self.is_dual_door else 0
        return (
            self.n_pax - rear_bench_seats - self.n_door_seats - front_door_row_seats
        ) // 2

    @property
    def n_rows(self) -> int:
        """Total passenger seating rows [-]."""
        front_door_rows = 1 if self.is_dual_door else 0
        rear_door_rows = 1
        rear_bench_rows = 1
        return front_door_rows + self.n_front_rows + rear_door_rows + rear_bench_rows

    @property
    def cabin_length(self) -> SiValue:
        """Passenger cabin length including forward clearance [m]."""
        fuse = self.design.fuselage
        return SiValue(
            self.n_rows * fuse.seatPitch.si + fuse.frontClearance.si,
            "m",
        )

    @property
    def cargo_volume_required(self) -> SiValue:
        """Required passenger luggage volume [m^3]."""
        return SiValue(
            self.n_pax * self.constraints.payload.luggageVolumePerPassenger.si,
            "m^3",
        )

    @property
    def _usable_baggage_area(self) -> SiValue:
        """Usable internal cross-sectional area of aft baggage bay [m^2]."""
        fuse = self.design.fuselage
        return SiValue(
            fuse.usableBaggageFactor * self.cabin_width * fuse.aisleHeadroom.si,
            "m^2",
        )

    @property
    def underfloor_baggage_volume(self) -> SiValue:
        """Usable underfloor baggage compartment volume beneath the cabin [m^3]."""
        fuse = self.design.fuselage
        return SiValue(
            fuse.usableBaggageFactor
            * self.cabin_width
            * fuse.underfloorBaggageHeight.si
            * self.cabin_length,
            "m^3",
        )

    @property
    def forward_baggage_volume(self) -> SiValue:
        """Usable forward/nose baggage compartment volume [m^3]."""
        return self.design.fuselage.forwardBaggageVolume.si

    @property
    def baggage_length(self) -> SiValue:
        """Aft baggage compartment length [m]."""
        remaining_volume = max(
            0.0,
            self.cargo_volume_required
            - self.underfloor_baggage_volume
            - self.forward_baggage_volume,
        )
        return SiValue(
            max(
                self.design.fuselage.minBaggageLength.si,
                remaining_volume / self._usable_baggage_area,
            ),
            "m",
        )

    @property
    def aft_baggage_volume(self) -> SiValue:
        """Actual available aft baggage compartment volume [m^3]."""
        return SiValue(self.baggage_length * self._usable_baggage_area, "m^3")

    @property
    def baggage_volume(self) -> SiValue:
        """Total available baggage volume (aft + underfloor + forward) [m^3]."""
        return SiValue(
            self.aft_baggage_volume
            + self.underfloor_baggage_volume
            + self.forward_baggage_volume,
            "m^3",
        )

    @property
    def tail_length(self) -> SiValue:
        """Aerodynamic tailcone length [m]."""
        return SiValue(2.5 * self._equivalent_diameter, "m")

    @property
    def length(self) -> SiValue:
        """Total fuselage length (Nose -> Cabin -> Aft Baggage -> Tail) [m]."""
        return SiValue(
            self.design.fuselage.noseLength.si
            + self.cabin_length
            + self.baggage_length
            + self.tail_length,
            "m",
        )

    @property
    def slenderness_ratio(self) -> float:
        """Fuselage fineness / slenderness ratio l_F / d_equiv [-]."""
        return self.length / self._equivalent_diameter

    @property
    def wetted_area(self) -> SiValue:
        """Fuselage wetted surface area (CAD override if set, else [Torenbeek - Synthesis of Subsonic Airplane Design | p. 447]) [m^2]."""
        if self.design.fuselage.wettedArea is not None:
            return self.design.fuselage.wettedArea.si
        perimeter = SiValue(
            2.0 * (self.width + self.height)
            - (8.0 - 2.0 * math.pi) * self.corner_radius,
            "m",
        )
        return calc_fuselage_wetted_area(
            perimeter, self.length, self.slenderness_ratio
        )

    @property
    def mass(self) -> SiValue:
        """Calibrated fuselage mass [kg]."""
        v_d = SiValue(1.25 * self.design.mission.cruiseSpeedTAS.si, "m/s")
        raw = calc_fuselage_mass(
            v_d,
            self.ref.horizontal_tail_lever_arm.si,
            self.width,
            self.height,
            self.wetted_area,
            self.design.fuselage.fuselageMassPenaltyFactor,
        )
        return SiValue(
            raw
            * self.ref.fuselage_calibration_factor
            * self.design.fuselage.technologyFactor,
            "kg",
        )


if __name__ == "__main__":
    from data import load_constraints, load_design_parameters
    from reference_aircraft import load_reference_aircraft
    from visualizations.fuselage import (
        plot_fuselage_sizing,
        print_fuselage_summary,
    )

    fuselage = FuselageDesign(
        load_constraints(),
        load_design_parameters(),
        load_reference_aircraft(),
    )
    print_fuselage_summary(fuselage)
    plot_fuselage_sizing(fuselage)
