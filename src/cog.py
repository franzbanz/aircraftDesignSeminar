"""Center of Gravity (CoG) aggregation and loading excursion analyzer.

Aggregates component CG positions (referenced to nose datum x = 0, +x aft) into
whole-aircraft CoG states (% MAC) and forward/aft loading excursions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from data import SiValue

if TYPE_CHECKING:
    from aircraft import BatteryAircraft


@dataclass(frozen=True)
class ComponentCG:
    """Single mass component with its longitudinal CG station."""

    name: str
    mass: SiValue
    x_cg: SiValue

    @property
    def moment(self) -> float:
        """Longitudinal mass moment m * x_cg [kg*m]."""
        return self.mass * self.x_cg


@dataclass(frozen=True)
class LoadingState:
    """Aircraft mass and CoG state for a specific loading condition."""

    name: str
    mass: SiValue
    x_cg: SiValue
    mac_fraction: float
    added_item: ComponentCG | None = None


class CenterOfGravity:
    """Whole-aircraft longitudinal Center of Gravity (CoG) and loading excursion analyzer."""

    def __init__(self, aircraft: BatteryAircraft) -> None:
        self.aircraft = aircraft

    def to_mac_fraction(self, x_cg: SiValue) -> float:
        """Converts a longitudinal station [m] to fraction of MAC [-]."""
        return (
            x_cg - self.aircraft.wing.x_lemac
        ) / self.aircraft.wing.mean_aerodynamic_chord

    @property
    def x_battery_cg(self) -> SiValue:
        """Battery pack CG station [m]."""
        return SiValue(
            self.aircraft.wing.x_lemac
            + self.aircraft.design.wing.batteryLeadingEdgeOffset.si,
            "m",
        )

    @property
    def empty_components(self) -> list[ComponentCG]:
        """Operating Empty Mass (OEM) components excluding battery."""
        ac = self.aircraft
        mass = ac.mass
        fuse = ac.fuselage
        wing = ac.wing
        emp = ac.empennage
        x_cabin_mid = fuse.cabin_center
        x_lemac = wing.x_lemac

        x_nose_gear = ac.design.landingGear.noseGearPosition.si
        x_main_gear = ac.design.landingGear.mainGearPosition.si
        m_nose_gear = mass.nose_landing_gear
        m_main_gear = mass.main_landing_gear
        x_gear = SiValue(
            (m_nose_gear * x_nose_gear + m_main_gear * x_main_gear)
            / (m_nose_gear + m_main_gear),
            "m",
        )

        x_pylons = SiValue(
            x_lemac + ac.design.propulsion.pylonLeadingEdgeOffset.si, "m"
        )
        x_engines = SiValue(
            x_lemac + ac.design.propulsion.engineLeadingEdgeOffset.si, "m"
        )

        crew_mass = min(160.0, mass.operator_items)
        x_crew = ac.design.fuselage.crewPosition.si
        x_ops = SiValue(
            (crew_mass * x_crew + (mass.operator_items - crew_mass) * x_cabin_mid)
            / mass.operator_items,
            "m",
        )

        return [
            ComponentCG("Wing", wing.mass, wing.cog),
            ComponentCG("Fuselage", fuse.mass, fuse.cog),
            ComponentCG("Horizontal Empennage", emp.horizontal_tail_mass, emp.htp_cog),
            ComponentCG("Vertical Empennage", emp.vertical_tail_mass, emp.vtp_cog),
            ComponentCG("Landing Gear", mass.landing_gear, x_gear),
            ComponentCG("Pylons & Nacelles", mass.pylons, x_pylons),
            ComponentCG("Engines & Propellers", mass.engine, x_engines),
            ComponentCG("Systems", mass.systems, fuse.cog),
            ComponentCG("Furnishings", mass.furnishings, x_cabin_mid),
            ComponentCG("Operator Items (Crew)", mass.operator_items, x_ops),
        ]

    @property
    def components(self) -> list[ComponentCG]:
        """Full aircraft component mass and CG breakdown at MTOM."""
        return [
            *self.empty_components,
            ComponentCG("Battery Pack", self.aircraft.mass.battery, self.x_battery_cg),
            ComponentCG(
                f"Payload ({self.aircraft.fuselage.n_pax} PAX + Luggage)",
                self.aircraft.mass.payload,
                self.aircraft.fuselage.payload_cog,
            ),
        ]

    def _state_from(
        self,
        name: str,
        items: list[ComponentCG],
        added_item: ComponentCG | None = None,
    ) -> LoadingState:
        """Builds a LoadingState from a list of ComponentCG items."""
        total_mass = SiValue(sum(c.mass for c in items), "kg")
        x_cg = SiValue(sum(c.moment for c in items) / total_mass, "m")
        return LoadingState(
            name=name,
            mass=total_mass,
            x_cg=x_cg,
            mac_fraction=self.to_mac_fraction(x_cg),
            added_item=added_item,
        )

    @property
    def oem_state(self) -> LoadingState:
        """Operating Empty Mass (OEM) excluding battery and payload."""
        return self._state_from("OEM (excl. Battery)", self.empty_components)

    @property
    def zero_payload_state(self) -> LoadingState:
        """Zero-payload flight state (OEM + Battery Pack)."""
        return self._state_from(
            "Empty + Battery (0 PAX)",
            [
                *self.empty_components,
                ComponentCG("Battery Pack", self.aircraft.mass.battery, self.x_battery_cg),
            ],
        )

    @property
    def mtom_state(self) -> LoadingState:
        """Full payload state (MTOM = OEM + Battery + 19 PAX + Luggage)."""
        return self._state_from("MTOM (Full Payload)", self.components)

    def loading_curve(
        self, direction: Literal["forward", "aft"] = "forward"
    ) -> list[LoadingState]:
        """Generates progressive front-to-back or back-to-front loading excursion."""
        fuse = self.aircraft.fuselage
        total_per_pax = self.aircraft.constraints.payload.weightPerPassenger.si
        luggage_per_pax = self.aircraft.design.mission.baggageMassPerPassenger.si
        seat_mass = SiValue(total_per_pax - luggage_per_pax, "kg")
        total_luggage = SiValue(fuse.n_pax * luggage_per_pax, "kg")

        bag = fuse.baggage
        bays = [
            ComponentCG(name, SiValue(total_luggage * share, "kg"), x_cg)
            for (name, x_cg), share in zip(
                (
                    ("Fwd Luggage", bag.x_forward),
                    ("Underfloor Luggage", bag.x_underfloor),
                    ("Aft Luggage", bag.x_aft),
                ),
                bag.shares,
            )
            if total_luggage * share > 0
        ]

        items = [
            *self.empty_components,
            ComponentCG("Battery Pack", self.aircraft.mass.battery, self.x_battery_cg),
        ]
        states = [self.zero_payload_state]
        x_ref = self.zero_payload_state.x_cg
        is_fwd = direction == "forward"
        prefix = "Fwd" if is_fwd else "Aft"

        def _append(item: ComponentCG, label: str) -> None:
            items.append(item)
            states.append(self._state_from(f"{prefix} +{label}", items, added_item=item))

        ordered_bays = bays if is_fwd else list(reversed(bays))
        for bay in ordered_bays:
            if (bay.x_cg < x_ref) == is_fwd:
                _append(bay, bay.name)

        pax_count = 0
        for count, x_row in fuse.passenger_rows if is_fwd else reversed(fuse.passenger_rows):
            for _ in range(count):
                pax_count += 1
                _append(ComponentCG(f"PAX {pax_count}", seat_mass, x_row), f"{pax_count} PAX")

        for bay in ordered_bays:
            if (bay.x_cg < x_ref) != is_fwd:
                _append(bay, bay.name)
        return states

    def extreme_state(self, direction: Literal["forward", "aft"]) -> LoadingState:
        """Forward-most or aft-most CoG across all loading scenarios."""
        states = self.loading_curve("forward") + self.loading_curve("aft")
        selector = min if direction == "forward" else max
        return selector(states, key=lambda s: s.mac_fraction)

    @property
    def cg_travel_mac(self) -> float:
        """Total CoG travel range in fraction of MAC [-]."""
        return (
            self.extreme_state("aft").mac_fraction
            - self.extreme_state("forward").mac_fraction
        )

    def required_battery_x_cg(self, target_mac_fraction: float = 0.25) -> SiValue:
        """Computes required battery CG station [m] to achieve target MAC% at MTOM."""
        x_target = (
            self.aircraft.wing.x_lemac
            + target_mac_fraction * self.aircraft.wing.mean_aerodynamic_chord
        )
        non_bat_moment = sum(
            c.moment for c in self.components if c.name != "Battery Pack"
        )
        return SiValue(
            (self.mtom_state.mass * x_target - non_bat_moment) / self.aircraft.mass.battery,
            "m",
        )
