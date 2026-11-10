"""Mission fuel fractions and kerosene-to-electric energy transfer calculator."""

from data import (
    Constraints,
    DesignParameters,
    ReferenceAircraftData,
    SiValue,
    load_constraints,
    load_design_parameters,
    load_reference_aircraft_data,
)
from formulas import (
    calc_breguet_fuel_mass_from_endurance,
    calc_breguet_fuel_mass_from_range,
    calc_breguet_range,
    calc_electric_cruise_energy,
    calc_electric_loiter_energy,
    calc_electric_range,
)


class ReferenceMissionCalculator:
    """Calculates reference turboprop (Do 228) mission energy, propulsion efficiency, and fuel masses."""

    def __init__(self, constraints: Constraints, ref: ReferenceAircraftData) -> None:
        self.constraints = constraints
        self.ref = ref

    @property
    def propulsion_efficiency(self) -> float:
        """Overall cruise propulsion efficiency of the reference turboprop aircraft [-]."""
        cruise_speed = self.ref.mission.cruiseSpeedTAS.si
        tsfc = self.ref.propulsion.tsfcCruise.si
        fuel_energy_density = self.ref.fuel.energyDensity.si
        return cruise_speed / (tsfc * fuel_energy_density)

    def propulsive_energy(self, fuel_mass: SiValue) -> SiValue:
        """Converts burned kerosene mass of reference aircraft into propulsive energy [J]."""
        chem_energy = fuel_mass * self.ref.fuel.energyDensity.si
        return SiValue(chem_energy * self.propulsion_efficiency, "J")

    @property
    def m_start_climb(self) -> SiValue:
        """Aircraft mass at brake-release / climb start after taxi-out [kg]."""
        return SiValue(
            self.ref.fuel.referenceMass.si - self.ref.fuel.taxiOutAndTakeOff.si,
            "kg",
        )

    @property
    def m_end_descent(self) -> SiValue:
        """Aircraft mass at the end of descent [kg]."""
        rf = self.ref.fuel
        return SiValue(
            self.m_start_climb - rf.climb.si - rf.cruise.si - rf.descent.si, "kg"
        )

    @property
    def m_start_reserves(self) -> SiValue:
        """Aircraft mass at trip completion / reserve start [kg]."""
        return SiValue(self.ref.fuel.referenceMass.si - self.ref.fuel.tripMass.si, "kg")

    def route_reserve_fuel_mass(self) -> SiValue:
        """Reference aircraft route reserve fuel mass [kg]."""
        return SiValue(
            self.constraints.mission.routeReserve * self.ref.fuel.tripMass.si, "kg"
        )

    def loiter_fuel_mass(self) -> SiValue:
        """Reference aircraft loiter fuel mass via Breguet endurance [kg]."""
        return calc_breguet_fuel_mass_from_endurance(
            self.m_start_reserves,
            self.constraints.mission.loiterTime.si,
            self.ref.aerodynamics.liftToDragRatioLoiter,
            self.ref.propulsion.tsfcCruise.si,
        )

    def diversion_fuel_mass(self) -> SiValue:
        """Reference aircraft diversion fuel mass via Breguet range [kg]."""
        return calc_breguet_fuel_mass_from_range(
            self.m_start_reserves,
            self.constraints.mission.diversionDistance.si,
            self.ref.aerodynamics.liftToDragRatioCruise,
            self.ref.mission.cruiseSpeedTAS.si,
            self.ref.propulsion.tsfcCruise.si,
        )

    def reserve_fuel_mass(self) -> SiValue:
        """Reference aircraft total reserve fuel mass [kg]."""
        return SiValue(
            self.route_reserve_fuel_mass()
            + self.loiter_fuel_mass()
            + self.diversion_fuel_mass(),
            "kg",
        )

    def equivalent_range(
        self, fuel_mass: SiValue, lift_to_drag: float | None = None
    ) -> SiValue:
        """Calculates equivalent Breguet cruise range for kerosene fuel [m]."""
        ld = (
            lift_to_drag
            if lift_to_drag is not None
            else self.ref.aerodynamics.liftToDragRatioCruise
        )
        # referenceMass (5950 kg) represents take-off mass at brake release (excluding taxi fuel)
        m_ref = self.ref.fuel.referenceMass.si
        return calc_breguet_range(
            m_ref,
            SiValue(m_ref - fuel_mass, "kg"),
            ld,
            self.ref.mission.cruiseSpeedTAS.si,
            self.ref.propulsion.tsfcCruise.si,
        )


class MissionEnergyCalculator:
    """Calculates mission segment energy demands, reserves, and battery sizing."""

    def __init__(
        self,
        constraints: Constraints,
        design: DesignParameters,
        ref_mission: ReferenceMissionCalculator,
        mtom: SiValue | None = None,
    ) -> None:
        self.constraints = constraints
        self.design = design
        self.ref_mission = ref_mission
        self.mtom: SiValue = (
            mtom if mtom is not None else design.initialSizing.maximumTakeOffMass.si
        )

    @property
    def range(self) -> SiValue:
        """Nominal mission cruise range [m]."""
        return self.design.mission.range.si

    def scaled_electric_energy(
        self, fuel_mass_ref: SiValue, m_start_ref: SiValue
    ) -> SiValue:
        """Scales reference segment fuel mass to required electric battery energy [J]."""
        m_avg_ref = m_start_ref - 0.5 * fuel_mass_ref
        prop_energy = (
            self.ref_mission.propulsive_energy(fuel_mass_ref) * self.mtom / m_avg_ref
        )
        return SiValue(prop_energy / self.design.propulsion.etaElectric, "J")

    def taxi_and_takeoff_energy(self) -> SiValue:
        """Electric energy required for taxi-out and take-off [J]."""
        fuel = self.ref_mission.ref.fuel
        return self.scaled_electric_energy(
            fuel.taxiOutAndTakeOff.si, fuel.referenceMass.si
        )

    def cruise_energy(self, distance: SiValue | None = None) -> SiValue:
        """Electric energy required for horizontal cruise flight via Breguet [J]."""
        dist = distance if distance is not None else self.design.mission.range.si
        return calc_electric_cruise_energy(
            dist,
            self.mtom,
            self.design.aerodynamics.liftToDragRatioCruise,
            self.design.propulsion.etaElectric,
        )

    def climb_and_descent_energy(self) -> SiValue:
        """Net additional electric energy required for climb and descent [J]."""
        rf = self.ref_mission.ref.fuel
        r_breguet = calc_breguet_range(
            self.ref_mission.m_start_climb,
            self.ref_mission.m_end_descent,
            self.ref_mission.ref.aerodynamics.liftToDragRatioCruise,
            self.ref_mission.ref.mission.cruiseSpeedTAS.si,
            self.ref_mission.ref.propulsion.tsfcCruise.si,
        )
        r_nom = rf.referenceRange.si
        return SiValue(((r_breguet - r_nom) / r_nom) * self.cruise_energy(r_nom), "J")

    def approach_and_landing_energy(self) -> SiValue:
        """Electric energy required for approach, landing, and taxi-in [J]."""
        return self.scaled_electric_energy(
            self.ref_mission.ref.fuel.approachLandingAndTaxiIn.si,
            self.ref_mission.m_end_descent,
        )

    def trip_energy(self) -> SiValue:
        """Total electric trip energy (Phases 1 to 5) [J]."""
        return SiValue(
            self.taxi_and_takeoff_energy()
            + self.climb_and_descent_energy()
            + self.cruise_energy()
            + self.approach_and_landing_energy(),
            "J",
        )

    def route_reserve_energy(self) -> SiValue:
        """Electric energy required for route reserve (e.g. 5% of trip) [J]."""
        return SiValue(self.constraints.mission.routeReserve * self.trip_energy(), "J")

    def loiter_energy(self) -> SiValue:
        """Electric energy required for loiter hold via Breguet [J]."""
        return calc_electric_loiter_energy(
            self.constraints.mission.loiterTime.si,
            self.constraints.performance.cruiseSpeedMin.si,
            self.mtom,
            self.design.aerodynamics.liftToDragRatioLoiter,
            self.design.propulsion.etaElectric,
        )

    def diversion_energy(self) -> SiValue:
        """Electric energy required for diversion to alternate airport [J]."""
        return self.cruise_energy(self.constraints.mission.diversionDistance.si)

    def reserve_energy(self) -> SiValue:
        """Total electric reserve energy (Route + Loiter + Diversion) [J]."""
        return SiValue(
            self.route_reserve_energy()
            + self.loiter_energy()
            + self.diversion_energy(),
            "J",
        )

    def total_mission_energy(self) -> SiValue:
        """Total electric mission energy (Trip + Reserve) [J]."""
        return SiValue(self.trip_energy() + self.reserve_energy(), "J")

    def battery_cell_mass(self, electric_energy: SiValue | None = None) -> SiValue:
        """Required battery cell mass for a given electric energy [kg]."""
        e = (
            electric_energy
            if electric_energy is not None
            else self.total_mission_energy()
        )
        return SiValue(e / self.constraints.battery.cellEnergyDensityMax.si, "kg")

    def battery_pack_mass(self, electric_energy: SiValue | None = None) -> SiValue:
        """Required battery pack mass (including cell-to-pack factor) [kg]."""
        return SiValue(
            self.battery_cell_mass(electric_energy)
            * self.constraints.battery.cellToPackFactorMin,
            "kg",
        )

    def equivalent_range(
        self, electric_energy: SiValue, lift_to_drag: float | None = None
    ) -> SiValue:
        """Calculates achievable Breguet cruise range for electric battery energy [m]."""
        ld = (
            lift_to_drag
            if lift_to_drag is not None
            else self.design.aerodynamics.liftToDragRatioCruise
        )
        e_pack = SiValue(
            self.constraints.battery.cellEnergyDensityMax.si
            / self.constraints.battery.cellToPackFactorMin,
            "J/kg",
        )
        return calc_electric_range(
            e_pack,
            self.design.propulsion.etaElectric,
            ld,
            self.battery_pack_mass(electric_energy),
            self.mtom,
        )


if __name__ == "__main__":
    from visualizations.fuel_fractions import print_mission_energy_breakdown

    constraints = load_constraints()
    ref_mission = ReferenceMissionCalculator(
        constraints, load_reference_aircraft_data()
    )
    calculator = MissionEnergyCalculator(
        constraints,
        load_design_parameters(),
        ref_mission,
    )
    print_mission_energy_breakdown(calculator)
