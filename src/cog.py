"""Center of Gravity (CoG) aggregation and loading excursion analyzer.

Aggregates component CG positions (referenced to nose datum x = 0, +x aft) into
whole-aircraft CoG states (% MAC) and forward/aft loading excursions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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

    @property
    def x_htp_ac(self) -> SiValue:
        """Horizontal tailplane aerodynamic center station [m]."""
        return self.aircraft.empennage.x_htp_ac

    @property
    def x_wing_ac(self) -> SiValue:
        """Wing 25% MAC aerodynamic center station [m]."""
        return self.aircraft.wing.x_ac

    @property
    def x_lemac(self) -> SiValue:
        """Leading edge of the Mean Aerodynamic Chord (LEMAC) station [m]."""
        return self.aircraft.wing.x_lemac

    def to_mac_fraction(self, x_cg: SiValue) -> float:
        """Converts a longitudinal station [m] to fraction of MAC [-]."""
        return (x_cg - self.x_lemac) / self.aircraft.wing.mean_aerodynamic_chord

    @property
    def x_battery_cg(self) -> SiValue:
        """Battery pack CG station [m] (wing-mounted if bending relief active, else at wing AC)."""
        if self.aircraft.design.wing.bendingReliefFactor.value > 0:
            return self.aircraft.wing.cog
        return self.x_wing_ac

    @property
    def empty_components(self) -> list[ComponentCG]:
        """Operating Empty Mass (OEM) components excluding battery."""
        ac = self.aircraft
        fuse = ac.fuselage
        wing = ac.wing
        emp = ac.empennage
        c_mac = wing.mean_aerodynamic_chord
        l_nose = ac.design.fuselage.noseLength.si
        x_cabin_mid = fuse.cabin_center

        x_gear = SiValue(0.15 * (0.55 * l_nose) + 0.85 * (self.x_lemac + 0.50 * c_mac), "m")
        crew_mass = min(160.0, ac.m_operator_items)
        x_ops = SiValue(
            (crew_mass * (0.60 * l_nose) + (ac.m_operator_items - crew_mass) * x_cabin_mid)
            / ac.m_operator_items,
            "m",
        )

        return [
            ComponentCG("Wing", wing.mass, wing.cog),
            ComponentCG("Fuselage", fuse.mass, fuse.cog),
            ComponentCG("Horizontal Empennage", emp.horizontal_tail_mass, emp.htp_cog),
            ComponentCG("Vertical Empennage", emp.vertical_tail_mass, emp.vtp_cog),
            ComponentCG("Landing Gear", ac.m_landing_gear, x_gear),
            ComponentCG("Pylons & Nacelles", ac.m_pylons, SiValue(self.x_lemac - 0.10 * c_mac, "m")),
            ComponentCG("Engines & Propellers", ac.m_engine, SiValue(self.x_lemac - 0.35 * c_mac, "m")),
            ComponentCG("Systems", ac.m_systems, fuse.cog),
            ComponentCG("Furnishings", ac.m_furnishings, x_cabin_mid),
            ComponentCG("Operator Items (Crew)", ac.m_operator_items, x_ops),
        ]

    @property
    def components(self) -> list[ComponentCG]:
        """Full aircraft component mass and CG breakdown at MTOM."""
        return [
            *self.empty_components,
            ComponentCG("Battery Pack", self.aircraft.m_battery, self.x_battery_cg),
            ComponentCG(
                f"Payload ({self.aircraft.fuselage.n_pax} PAX + Luggage)",
                self.aircraft.m_payload,
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
            [*self.empty_components, ComponentCG("Battery Pack", self.aircraft.m_battery, self.x_battery_cg)],
        )

    @property
    def mtom_state(self) -> LoadingState:
        """Full payload state (MTOM = OEM + Battery + 19 PAX + Luggage)."""
        return self._state_from("MTOM (Full Payload)", self.components)

    def _loading_curve(self, *, forward: bool) -> list[LoadingState]:
        """Generates progressive front-to-back or back-to-front loading excursion."""
        fuse = self.aircraft.fuselage
        total_per_pax = self.aircraft.constraints.payload.weightPerPassenger.si
        luggage_mass = SiValue(min(15.0, 0.18 * total_per_pax), "kg")
        seat_mass = SiValue(total_per_pax - luggage_mass, "kg")
        total_luggage = SiValue(fuse.n_pax * luggage_mass, "kg")

        baggage = fuse.baggage
        fwd_share, underfloor_share, aft_share = baggage.shares
        luggage_bays = [
            ("Fwd Luggage", SiValue(total_luggage * fwd_share, "kg"), baggage.x_forward),
            (
                "Underfloor Luggage",
                SiValue(total_luggage * underfloor_share, "kg"),
                baggage.x_underfloor,
            ),
            ("Aft Luggage", SiValue(total_luggage * aft_share, "kg"), baggage.x_aft),
        ]
        active_bays = [(name, mass, x) for name, mass, x in luggage_bays if mass > 0]

        items = [*self.empty_components, ComponentCG("Battery Pack", self.aircraft.m_battery, self.x_battery_cg)]
        states = [self.zero_payload_state]
        prefix = "Fwd" if forward else "Aft"

        x_ref = self.zero_payload_state.x_cg
        if forward:
            before_bays = [bay for bay in active_bays if bay[2] < x_ref]
            after_bays = [bay for bay in active_bays if bay[2] >= x_ref]
        else:
            before_bays = [bay for bay in reversed(active_bays) if bay[2] >= x_ref]
            after_bays = [bay for bay in reversed(active_bays) if bay[2] < x_ref]

        for bay_name, bay_mass, bay_x in before_bays:
            bay_item = ComponentCG(bay_name, bay_mass, bay_x)
            items.append(bay_item)
            states.append(
                self._state_from(f"{prefix} +{bay_name}", items, added_item=bay_item)
            )

        rows = fuse.passenger_rows if forward else reversed(fuse.passenger_rows)
        pax_loaded = 0
        for count, x_row in rows:
            for _ in range(count):
                pax_loaded += 1
                pax_item = ComponentCG(f"PAX {pax_loaded}", seat_mass, x_row)
                items.append(pax_item)
                states.append(
                    self._state_from(
                        f"{prefix} +{pax_loaded} PAX", items, added_item=pax_item
                    )
                )

        for bay_name, bay_mass, bay_x in after_bays:
            bay_item = ComponentCG(bay_name, bay_mass, bay_x)
            items.append(bay_item)
            states.append(
                self._state_from(f"{prefix} +{bay_name}", items, added_item=bay_item)
            )
        return states

    @property
    def forward_loading_curve(self) -> list[LoadingState]:
        """Progressive front-to-back passenger loading excursion."""
        return self._loading_curve(forward=True)

    @property
    def aft_loading_curve(self) -> list[LoadingState]:
        """Progressive back-to-front passenger loading excursion (luggage first)."""
        return self._loading_curve(forward=False)

    @property
    def most_forward_state(self) -> LoadingState:
        """Forward-most CoG across all loading scenarios."""
        return min(self.forward_loading_curve + self.aft_loading_curve, key=lambda s: s.mac_fraction)

    @property
    def most_aft_state(self) -> LoadingState:
        """Aft-most CoG across all loading scenarios."""
        return max(self.forward_loading_curve + self.aft_loading_curve, key=lambda s: s.mac_fraction)

    @property
    def cg_travel_mac(self) -> float:
        """Total CoG travel range in fraction of MAC [-]."""
        return self.most_aft_state.mac_fraction - self.most_forward_state.mac_fraction

    def required_battery_x_cg(self, target_mac_fraction: float = 0.25) -> SiValue:
        """Computes required battery CG station [m] to achieve target MAC% at MTOM."""
        x_target = self.x_lemac + target_mac_fraction * self.aircraft.wing.mean_aerodynamic_chord
        non_bat_moment = sum(c.moment for c in self.components if c.name != "Battery Pack")
        return SiValue((self.aircraft.mtom * x_target - non_bat_moment) / self.aircraft.m_battery, "m")
