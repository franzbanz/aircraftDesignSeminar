"""Mission fuel fractions and kerosene-to-electric energy transfer calculator."""

from constants import GRAVITY
from data import (
    Constraints,
    DesignParameters,
    ReferenceAircraft,
    SiValue,
    load_constraints,
    load_design_parameters,
    load_reference_aircraft,
)
from formulas import (
    calc_breguet_fuel_mass_from_endurance,
    calc_breguet_fuel_mass_from_range,
    calc_breguet_range,
    calc_electric_cruise_energy,
    calc_electric_loiter_energy,
    calc_electric_range,
)


class MissionEnergyCalculator:
    """Calculates mission segment energy demands, reserves, and battery sizing.

    Transfers the kerosene mission profile of the reference aircraft (Do 228)
    into electric energy requirements for a battery-electric aircraft.
    """

    def __init__(
        self,
        constraints: Constraints,
        design: DesignParameters,
        ref: ReferenceAircraft,
        mtom: SiValue | None = None,
    ) -> None:
        self.constraints = constraints
        self.design = design
        self.ref = ref
        self.mtom: SiValue = (
            mtom if mtom is not None else design.initialSizing.maximumTakeOffMass.si
        )

    # --------------------------------------------------------------------------
    # Aerodynamic & Propulsion Shortcuts
    # --------------------------------------------------------------------------

    @property
    def eta_electric(self) -> float:
        """Overall electric powertrain efficiency [-]."""
        return float(self.design.propulsion.etaElectric.value)

    @property
    def lift_to_drag_cruise(self) -> float:
        """Electric aircraft cruise lift-to-drag ratio [-]."""
        return float(self.design.aerodynamics.liftToDragRatioCruise.value)

    @property
    def lift_to_drag_loiter(self) -> float:
        """Electric aircraft loiter lift-to-drag ratio [-]."""
        return float(self.design.aerodynamics.liftToDragRatioLoiter.value)

    @property
    def range(self) -> SiValue:
        """Nominal mission cruise range [m]."""
        return self.design.mission.range.si

    # --------------------------------------------------------------------------
    # Reference Turboprop Properties
    # --------------------------------------------------------------------------

    @property
    def reference_propulsion_efficiency(self) -> float:
        """Overall cruise propulsion efficiency of the reference turboprop aircraft [-]."""
        cruise_speed = self.ref.mission.cruiseSpeedTAS.si
        tsfc = self.ref.propulsion.tsfcCruise.si
        fuel_energy_density = self.ref.fuel.energyDensity.si
        return cruise_speed / (tsfc * fuel_energy_density)

    def reference_propulsive_energy(self, fuel_mass: SiValue) -> SiValue:
        """Converts burned kerosene mass of reference aircraft into propulsive energy [J]."""
        chem_energy = fuel_mass * self.ref.fuel.energyDensity.si
        return SiValue(chem_energy * self.reference_propulsion_efficiency, "J")

    def scaled_electric_energy(
        self,
        fuel_mass_ref: SiValue,
        m_start_ref: SiValue,
    ) -> SiValue:
        """Scales reference segment fuel mass to required electric battery energy [J].

        Scales propulsive energy with the instantaneous mass ratio (mtom / m_avg_ref).
        """
        m_avg_ref = m_start_ref - 0.5 * fuel_mass_ref
        prop_energy_ref = self.reference_propulsive_energy(fuel_mass_ref)
        prop_energy_new = prop_energy_ref * self.mtom / m_avg_ref
        return SiValue(prop_energy_new / self.eta_electric, "J")

    # --------------------------------------------------------------------------
    # Trip Flight Phases (Phases 1-5)
    # --------------------------------------------------------------------------

    def taxi_and_takeoff_energy(self) -> SiValue:
        """Electric energy required for taxi-out and take-off [J]."""
        m_start_ref = self.ref.fuel.referenceMass.si
        fuel_ref = self.ref.fuel.taxiOutAndTakeOff.si
        return self.scaled_electric_energy(fuel_ref, m_start_ref)

    def cruise_energy(self, distance: SiValue | None = None) -> SiValue:
        """Electric energy required for horizontal cruise flight via Breguet [J]."""
        dist = distance if distance is not None else self.range
        return calc_electric_cruise_energy(
            range_=dist,
            take_off_mass=self.mtom,
            lift_to_drag=self.lift_to_drag_cruise,
            eta_electric=self.eta_electric,
        )

    def climb_and_descent_energy(self) -> SiValue:
        """Net additional electric energy required for climb and descent [J].

        Uses equivalent Breguet range overhead of reference aircraft (~10.3%).
        """
        m_start_climb = SiValue(self.ref.fuel.referenceMass.si - self.ref.fuel.taxiOutAndTakeOff.si, "kg")
        m_end_descent = SiValue(
            m_start_climb
            - self.ref.fuel.climb.si
            - self.ref.fuel.cruise.si
            - self.ref.fuel.descent.si,
            "kg",
        )
        breguet_range = calc_breguet_range(
            m_start=m_start_climb,
            m_end=m_end_descent,
            lift_to_drag=float(self.ref.aerodynamics.liftToDragRatioCruise.value),
            cruise_speed=self.ref.mission.cruiseSpeedTAS.si,
            thrust_specific_fuel_consumption=self.ref.propulsion.tsfcCruise.si,
        )
        ref_range = self.ref.fuel.referenceRange.si
        overhead_factor = (breguet_range - ref_range) / ref_range

        ref_cruise_energy = self.cruise_energy(ref_range)
        return SiValue(overhead_factor * ref_cruise_energy, "J")

    def approach_and_landing_energy(self) -> SiValue:
        """Electric energy required for approach, landing, and taxi-in [J]."""
        m_start_ref = SiValue(
            self.ref.fuel.referenceMass.si
            - self.ref.fuel.taxiOutAndTakeOff.si
            - self.ref.fuel.climb.si
            - self.ref.fuel.cruise.si
            - self.ref.fuel.descent.si,
            "kg",
        )
        fuel_ref = self.ref.fuel.approachLandingAndTaxiIn.si
        return self.scaled_electric_energy(fuel_ref, m_start_ref)

    def trip_energy(self) -> SiValue:
        """Total electric trip energy (Phases 1 to 5) [J]."""
        return SiValue(
            self.taxi_and_takeoff_energy()
            + self.climb_and_descent_energy()
            + self.cruise_energy()
            + self.approach_and_landing_energy(),
            "J",
        )

    # --------------------------------------------------------------------------
    # Reserve Flight Phases
    # --------------------------------------------------------------------------

    def route_reserve_energy(self) -> SiValue:
        """Electric energy required for route reserve (e.g. 5% of trip) [J]."""
        return SiValue(self.constraints.mission.routeReserve * self.trip_energy(), "J")

    def loiter_energy(self) -> SiValue:
        """Electric energy required for loiter hold via Breguet [J]."""
        t_loiter = self.constraints.mission.loiterTime.si
        v_loiter = self.constraints.performance.cruiseSpeedMin.si
        return calc_electric_loiter_energy(
            loiter_time=t_loiter,
            loiter_speed=v_loiter,
            take_off_mass=self.mtom,
            lift_to_drag_loiter=self.lift_to_drag_loiter,
            eta_electric=self.eta_electric,
        )

    def diversion_energy(self) -> SiValue:
        """Electric energy required for diversion to alternate airport [J]."""
        dist = self.constraints.mission.diversionDistance.si
        return self.cruise_energy(dist)

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

    # --------------------------------------------------------------------------
    # Battery Sizing
    # --------------------------------------------------------------------------

    def battery_cell_mass(self, electric_energy: SiValue | None = None) -> SiValue:
        """Required battery cell mass for a given electric energy [kg]."""
        energy = electric_energy if electric_energy is not None else self.total_mission_energy()
        density = self.constraints.battery.cellEnergyDensityMax.si
        return SiValue(energy / density, "kg")

    def battery_pack_mass(self, electric_energy: SiValue | None = None) -> SiValue:
        """Required battery pack mass (including cell-to-pack factor) [kg]."""
        cell_mass = self.battery_cell_mass(electric_energy)
        pack_factor = float(self.constraints.battery.cellToPackFactorMin.value)
        return SiValue(cell_mass * pack_factor, "kg")

    # --------------------------------------------------------------------------
    # Breguet Range Equivalence
    # --------------------------------------------------------------------------

    def kerosene_equivalent_range(
        self,
        fuel_mass: SiValue,
        lift_to_drag: float | None = None,
    ) -> SiValue:
        """Calculates equivalent Breguet cruise range for kerosene fuel [m]."""
        ld = lift_to_drag if lift_to_drag is not None else float(self.ref.aerodynamics.liftToDragRatioCruise.value)
        m_ref = self.ref.fuel.referenceMass.si
        return calc_breguet_range(
            m_start=m_ref,
            m_end=SiValue(m_ref - fuel_mass, "kg"),
            lift_to_drag=ld,
            cruise_speed=self.ref.mission.cruiseSpeedTAS.si,
            thrust_specific_fuel_consumption=self.ref.propulsion.tsfcCruise.si,
        )

    def electric_equivalent_range(
        self,
        electric_energy: SiValue,
        lift_to_drag: float | None = None,
    ) -> SiValue:
        """Calculates achievable Breguet cruise range for electric battery energy [m]."""
        ld = lift_to_drag if lift_to_drag is not None else self.lift_to_drag_cruise
        e_pack = SiValue(
            self.constraints.battery.cellEnergyDensityMax.si
            / float(self.constraints.battery.cellToPackFactorMin.value),
            "J/kg",
        )
        m_pack = self.battery_pack_mass(electric_energy)
        return calc_electric_range(
            battery_energy_density=e_pack,
            eta_electric=self.eta_electric,
            lift_to_drag=ld,
            battery_mass=m_pack,
            take_off_mass=self.mtom,
        )

    # --------------------------------------------------------------------------
    # Reference Kerosene Reserves
    # --------------------------------------------------------------------------

    def reference_route_reserve_fuel_mass(self) -> SiValue:
        """Reference aircraft route reserve fuel mass [kg]."""
        return SiValue(float(self.constraints.mission.routeReserve.value) * self.ref.fuel.tripMass.si, "kg")

    def reference_loiter_fuel_mass(self) -> SiValue:
        """Reference aircraft loiter fuel mass via Breguet endurance [kg]."""
        m_start_ref = SiValue(self.ref.fuel.referenceMass.si - self.ref.fuel.tripMass.si, "kg")
        t_loiter = self.constraints.mission.loiterTime.si
        ld_loiter = float(self.ref.aerodynamics.liftToDragRatioLoiter.value)
        tsfc = self.ref.propulsion.tsfcCruise.si
        return calc_breguet_fuel_mass_from_endurance(
            m_start=m_start_ref,
            endurance=t_loiter,
            lift_to_drag=ld_loiter,
            thrust_specific_fuel_consumption=tsfc,
        )

    def reference_diversion_fuel_mass(self) -> SiValue:
        """Reference aircraft diversion fuel mass via Breguet range [kg]."""
        m_start_ref = SiValue(self.ref.fuel.referenceMass.si - self.ref.fuel.tripMass.si, "kg")
        d_div = self.constraints.mission.diversionDistance.si
        ld_cruise = float(self.ref.aerodynamics.liftToDragRatioCruise.value)
        cruise_speed = self.ref.mission.cruiseSpeedTAS.si
        tsfc = self.ref.propulsion.tsfcCruise.si
        return calc_breguet_fuel_mass_from_range(
            m_start=m_start_ref,
            range_=d_div,
            lift_to_drag=ld_cruise,
            cruise_speed=cruise_speed,
            thrust_specific_fuel_consumption=tsfc,
        )

    def reference_reserve_fuel_mass(self) -> SiValue:
        """Reference aircraft total reserve fuel mass [kg]."""
        return SiValue(
            self.reference_route_reserve_fuel_mass()
            + self.reference_loiter_fuel_mass()
            + self.reference_diversion_fuel_mass(),
            "kg",
        )

    # --------------------------------------------------------------------------
    # Detailed Breakdown Table
    # --------------------------------------------------------------------------

    def print_breakdown(self) -> None:
        """Prints a comprehensive breakdown table comparing reference kerosene and electric battery sizing."""
        e_taxi = self.taxi_and_takeoff_energy()
        e_cruise = self.cruise_energy()
        e_climb_descent = self.climb_and_descent_energy()
        e_approach = self.approach_and_landing_energy()

        segments = [
            ("1. Taxi-out & Take-off", self.ref.fuel.taxiOutAndTakeOff.si, e_taxi, None),
            (f"2. Cruise ({self.range.to('nm'):.0f} nm)", self.ref.fuel.cruise.si, e_cruise, None),
            ("3. Climb & Descent (+10.3% Ref.)", SiValue(self.ref.fuel.climb.si + self.ref.fuel.descent.si, "kg"), e_climb_descent, None),
            ("4. Approach, Landing & Taxi-in", self.ref.fuel.approachLandingAndTaxiIn.si, e_approach, None),
        ]

        fuel_route_res = self.reference_route_reserve_fuel_mass()
        fuel_loiter_res = self.reference_loiter_fuel_mass()
        fuel_div_res = self.reference_diversion_fuel_mass()

        e_route_res = self.route_reserve_energy()
        e_loiter_res = self.loiter_energy()
        e_div_res = self.diversion_energy()

        reserve_segments = [
            ("  - 5% Route Reserve", fuel_route_res, e_route_res, None),
            (f"  - 30 min Loiter (L/D = {self.lift_to_drag_loiter:.1f})", fuel_loiter_res, e_loiter_res, self.lift_to_drag_loiter),
            ("  - 50 NM Diversion", fuel_div_res, e_div_res, None),
        ]

        e_trip = self.trip_energy()
        e_reserve = self.reserve_energy()
        e_total = self.total_mission_energy()
        fuel_reserve_calc = self.reference_reserve_fuel_mass()

        print("----- MISSION ENERGY & BATTERY MASS BREAKDOWN -----")
        print(f"Reference Turboprop Efficiency (eta_ref): {self.reference_propulsion_efficiency * 100:.2f} %")
        print(f"Electric Aircraft: MTOM = {self.mtom}, eta_el = {self.eta_electric * 100:.1f} %, Range = {self.range.to('nm'):.0f} nm, L/D = {self.lift_to_drag_cruise:.1f}\n")
        print(f"{'Segment':<32} | {'Ref Fuel':>9} | {'R (Kero)':>9} | {'E_el [kWh]':>10} | {'m_Cell':>10} | {'m_Pack':>10} | {'R (Bat)':>9}")
        print("-" * 105)

        for name, fuel, e, ld in segments:
            r_kero = self.kerosene_equivalent_range(fuel, ld)
            r_bat = self.electric_equivalent_range(e, ld)
            print(
                f"{name:<32} | {fuel.to('kg'):6.1f} kg | {r_kero.to('nm'):6.1f} NM | {e.to('kWh'):10.1f} | "
                f"{self.battery_cell_mass(e):7.1f} kg | {self.battery_pack_mass(e):7.1f} kg | {r_bat.to('nm'):6.1f} NM"
            )

        print("-" * 105)
        r_kero_trip = self.kerosene_equivalent_range(self.ref.fuel.tripMass.si)
        r_bat_trip = self.electric_equivalent_range(e_trip)
        print(
            f"{'TRIP TOTAL (Phases 1-5)':<32} | {self.ref.fuel.tripMass.to('kg'):6.1f} kg | {r_kero_trip.to('nm'):6.1f} NM | {e_trip.to('kWh'):10.1f} | "
            f"{self.battery_cell_mass(e_trip):7.1f} kg | {self.battery_pack_mass(e_trip):7.1f} kg | {r_bat_trip.to('nm'):6.1f} NM"
        )
        print("-" * 105)

        for name, fuel, e, ld in reserve_segments:
            r_kero = self.kerosene_equivalent_range(fuel, float(self.ref.aerodynamics.liftToDragRatioLoiter.value) if ld else None)
            r_bat = self.electric_equivalent_range(e, ld)
            print(
                f"{name:<32} | {fuel.to('kg'):6.1f} kg | {r_kero.to('nm'):6.1f} NM | {e.to('kWh'):10.1f} | "
                f"{self.battery_cell_mass(e):7.1f} kg | {self.battery_pack_mass(e):7.1f} kg | {r_bat.to('nm'):6.1f} NM"
            )

        r_kero_res = self.kerosene_equivalent_range(fuel_reserve_calc)
        r_bat_res = self.electric_equivalent_range(e_reserve)
        print(
            f"{'6. Reserve Total (Ref: 186 kg)':<32} | {fuel_reserve_calc.to('kg'):6.1f} kg | {r_kero_res.to('nm'):6.1f} NM | {e_reserve.to('kWh'):10.1f} | "
            f"{self.battery_cell_mass(e_reserve):7.1f} kg | {self.battery_pack_mass(e_reserve):7.1f} kg | {r_bat_res.to('nm'):6.1f} NM"
        )
        print("=" * 105)
        total_fuel = SiValue(self.ref.fuel.tripMass.si + fuel_reserve_calc.si, "kg")
        r_kero_tot = self.kerosene_equivalent_range(total_fuel)
        r_bat_tot = self.electric_equivalent_range(e_total)
        print(
            f"{'MISSION TOTAL (Trip + Reserve)':<32} | {total_fuel.to('kg'):6.1f} kg | {r_kero_tot.to('nm'):6.1f} NM | {e_total.to('kWh'):10.1f} | "
            f"{self.battery_cell_mass(e_total):7.1f} kg | {self.battery_pack_mass(e_total):7.1f} kg | {r_bat_tot.to('nm'):6.1f} NM"
        )


if __name__ == "__main__":
    calculator = MissionEnergyCalculator(
        constraints=load_constraints(),
        design=load_design_parameters(),
        ref=load_reference_aircraft(),
    )
    calculator.print_breakdown()
