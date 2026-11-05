"""Mission fuel fractions and kerosene-to-electric energy transfer calculator."""

from constants import GRAVITY
from data import SiValue, load_constraints, load_reference_aircraft
from formulas import (
    calc_breguet_fuel_mass_from_endurance,
    calc_breguet_fuel_mass_from_range,
    calc_breguet_range, calc_electric_range,
)

constraints = load_constraints()
ref_aircraft = load_reference_aircraft()

MTOM = SiValue(8618, "kg")  # [kg] Design take-off mass of the electric aircraft
ETA_ELECTRIC = 0.85  # [-] Overall electric powertrain efficiency
L_D = 12.1  # [-] Cruise lift-to-drag ratio
L_D_LOITER = 15.7  # [-] Loiter lift-to-drag ratio


def calc_reference_propulsion_efficiency() -> float:
    """Calculates overall cruise propulsion efficiency of the reference turboprop aircraft [-]."""
    cruise_speed = ref_aircraft.performance.cruiseSpeedTAS.si
    thrust_specific_fuel_consumption = ref_aircraft.propulsion.tsfcCruise.si
    fuel_energy_density = ref_aircraft.fuel.energyDensity.si
    return cruise_speed / (thrust_specific_fuel_consumption * fuel_energy_density)


def calc_reference_propulsive_energy(fuel_mass: SiValue) -> SiValue:
    """Converts burned kerosene mass of the reference aircraft into propulsive energy [J]."""
    chemical_energy = fuel_mass * ref_aircraft.fuel.energyDensity.si
    reference_propulsion_efficiency = calc_reference_propulsion_efficiency()
    return SiValue(chemical_energy * reference_propulsion_efficiency, "J")


def calc_scaled_electric_energy(
    fuel_mass_ref: SiValue,
    m_start_ref: SiValue,
    mtom: SiValue = MTOM,
) -> SiValue:
    """Scales reference segment fuel mass to required electric battery energy [J].

    Scales propulsive energy with the instantaneous mass ratio (mtom / m_avg_ref).
    """
    m_avg_ref = m_start_ref - 0.5 * fuel_mass_ref
    propulsive_energy_ref = calc_reference_propulsive_energy(fuel_mass_ref)

    propulsive_energy_new = propulsive_energy_ref * mtom / m_avg_ref
    return SiValue(propulsive_energy_new / ETA_ELECTRIC, "J")


def calc_taxi_and_takeoff_energy(mtom: SiValue = MTOM) -> SiValue:
    """Calculates electric energy required for taxi-out and take-off [J]."""
    m_start_ref = ref_aircraft.fuel.referenceMass.si
    fuel_ref = ref_aircraft.fuel.taxiOutAndTakeOff.si
    return calc_scaled_electric_energy(fuel_ref, m_start_ref, mtom)


def calc_cruise_energy(
    range_: SiValue = constraints.mission.range.si,
    mtom: SiValue = MTOM,
) -> SiValue:
    """Calculates required electrical battery energy for horizontal cruise flight [J].

    Derived from steady level flight equilibrium (D = mtom * g / (L/D)):
    E_el = (D * R) / eta = (R * g * mtom) / (eta * L/D)

    Args:
        range_: Cruise range [m]. Defaults to constraints.mission.range.
        mtom: Aircraft take-off mass [kg].

    Returns:
        Required electrical energy [J].
    """
    energy_j = range_ * GRAVITY * mtom / (ETA_ELECTRIC * L_D)
    return SiValue(energy_j, "J")


def calc_climb_and_descent_energy(mtom: SiValue = MTOM) -> SiValue:
    """Calculates net additional electric energy required for climb and descent [J].

    Computes the equivalent Breguet range of the reference aircraft's combined
    Climb + Cruise + Descent phases (110.3 NM at 5950 kg reference mission mass)
    and compares it to the 100 NM (185.2 km) reference mission range to obtain
    the relative climb/descent overhead factor (~10.3%).
    """
    m_start_climb = SiValue(ref_aircraft.fuel.referenceMass.si - ref_aircraft.fuel.taxiOutAndTakeOff.si, "kg")
    m_end_descent = SiValue(
        m_start_climb
        - ref_aircraft.fuel.climb.si
        - ref_aircraft.fuel.cruise.si
        - ref_aircraft.fuel.descent.si,
        "kg",
    )
    breguet_range = calc_breguet_range(m_start_climb, m_end_descent)
    reference_range = ref_aircraft.fuel.referenceRange.si
    climb_descent_overhead_factor = (breguet_range - reference_range) / reference_range

    reference_cruise_energy = calc_cruise_energy(reference_range, mtom)
    return SiValue(climb_descent_overhead_factor * reference_cruise_energy, "J")


def calc_approach_and_landing_energy(mtom: SiValue = MTOM) -> SiValue:
    """Calculates electric energy required for approach, landing, and taxi-in [J]."""
    m_start_ref = SiValue(
        ref_aircraft.fuel.referenceMass.si
        - ref_aircraft.fuel.taxiOutAndTakeOff.si
        - ref_aircraft.fuel.climb.si
        - ref_aircraft.fuel.cruise.si
        - ref_aircraft.fuel.descent.si,
        "kg",
    )
    fuel_ref = ref_aircraft.fuel.approachLandingAndTaxiIn.si
    return calc_scaled_electric_energy(fuel_ref, m_start_ref, mtom)


def calc_trip_energy(mtom: SiValue = MTOM) -> SiValue:
    """Calculates total electric trip energy (Phases 1 to 5) [J]."""
    return SiValue(
        calc_taxi_and_takeoff_energy(mtom)
        + calc_climb_and_descent_energy(mtom)
        + calc_cruise_energy(mtom=mtom)
        + calc_approach_and_landing_energy(mtom),
        "J",
    )


def calc_reference_route_reserve_fuel_mass() -> SiValue:
    """Calculates reference aircraft fuel mass for the 5% route reserve [kg]."""
    return SiValue(constraints.mission.routeReserve * ref_aircraft.fuel.tripMass.si, "kg")


def calc_reference_loiter_fuel_mass(
    loiter_time: SiValue = constraints.mission.loiterTime.si,
    lift_to_drag_loiter: float = ref_aircraft.aerodynamics.liftToDragRatioLoiter,
) -> SiValue:
    """Calculates reference aircraft fuel mass for loiter via Breguet endurance [kg]."""
    m_start_ref = SiValue(ref_aircraft.fuel.referenceMass.si - ref_aircraft.fuel.tripMass.si, "kg")
    return calc_breguet_fuel_mass_from_endurance(m_start_ref, loiter_time, lift_to_drag_loiter)


def calc_reference_diversion_fuel_mass(
    diversion_distance: SiValue = constraints.mission.diversionDistance.si,
    lift_to_drag_cruise: float = ref_aircraft.aerodynamics.liftToDragRatioCruise,
) -> SiValue:
    """Calculates reference aircraft fuel mass for diversion via Breguet range [kg]."""
    m_start_ref = SiValue(ref_aircraft.fuel.referenceMass.si - ref_aircraft.fuel.tripMass.si, "kg")
    return calc_breguet_fuel_mass_from_range(m_start_ref, diversion_distance, lift_to_drag_cruise)


def calc_reference_reserve_fuel_mass() -> SiValue:
    """Calculates total reference reserve fuel mass from the three reserve components [kg]."""
    return SiValue(
        calc_reference_route_reserve_fuel_mass()
        + calc_reference_loiter_fuel_mass()
        + calc_reference_diversion_fuel_mass(),
        "kg",
    )


def calc_route_reserve_energy(mtom: SiValue = MTOM) -> SiValue:
    """Calculates electric energy required for the 5% route reserve [J]."""
    return SiValue(constraints.mission.routeReserve * calc_trip_energy(mtom), "J")


def calc_loiter_energy(
    loiter_time: SiValue = constraints.mission.loiterTime.si,
    lift_to_drag_loiter: float = L_D_LOITER,
    loiter_speed: SiValue = constraints.performance.cruiseSpeedMin.si,
    mtom: SiValue = MTOM,
) -> SiValue:
    """Calculates required electrical battery energy for loiter flight [J].

    Derived from the electric Breguet endurance equation (P_prop = D * v = mtom * g * v / (L/D)_loiter):
    E_el = (v * t_loiter * g * mtom) / (eta_el * (L/D)_loiter)

    Args:
        loiter_time: Loiter duration [s]. Defaults to constraints.mission.loiterTime.
        lift_to_drag_loiter: Lift-to-drag ratio in loiter [-]. Defaults to reference loiter L/D.
        loiter_speed: True airspeed during loiter [m/s]. Defaults to constraints.performance.cruiseSpeedMin.
        mtom: Aircraft take-off mass [kg].

    Returns:
        Required electrical energy [J].
    """
    energy_j = (loiter_speed * loiter_time * GRAVITY * mtom) / (ETA_ELECTRIC * lift_to_drag_loiter)
    return SiValue(energy_j, "J")


def calc_diversion_energy(
    diversion_distance: SiValue = constraints.mission.diversionDistance.si,
    mtom: SiValue = MTOM,
) -> SiValue:
    """Calculates electric energy required for diversion to alternate airport [J]."""
    return calc_cruise_energy(diversion_distance, mtom)


def calc_reserve_energy(mtom: SiValue = MTOM) -> SiValue:
    """Calculates electric reserve energy (5% route + 30 min loiter + 50 NM diversion) [J]."""
    return SiValue(calc_route_reserve_energy(mtom) + calc_loiter_energy(mtom=mtom) + calc_diversion_energy(mtom=mtom), "J")


def calc_total_mission_energy(mtom: SiValue = MTOM) -> SiValue:
    """Calculates total electric mission energy (Trip + Reserve) [J]."""
    return SiValue(calc_trip_energy(mtom) + calc_reserve_energy(mtom), "J")


def calc_battery_cell_mass(electric_energy: SiValue) -> SiValue:
    """Calculates required battery mass at cell level for a given electric energy [kg]."""
    cell_energy_density = constraints.battery.cellEnergyDensityMax.si
    return SiValue(electric_energy / cell_energy_density, "kg")


def calc_battery_pack_mass(electric_energy: SiValue) -> SiValue:
    """Calculates required battery mass at pack level (including cell-to-pack factor) [kg]."""
    return SiValue(calc_battery_cell_mass(electric_energy) * constraints.battery.cellToPackFactorMin, "kg")


if __name__ == "__main__":
    segments = [
        ("1. Taxi-out & Take-off", ref_aircraft.fuel.taxiOutAndTakeOff.si, calc_taxi_and_takeoff_energy()),
        (f"2. Cruise ({constraints.mission.range})", ref_aircraft.fuel.cruise.si, calc_cruise_energy()),
        ("3. Climb & Descent (+10.3% Ref.)", SiValue(ref_aircraft.fuel.climb.si + ref_aircraft.fuel.descent.si, "kg"), calc_climb_and_descent_energy()),
        ("4. Approach, Landing & Taxi-in", ref_aircraft.fuel.approachLandingAndTaxiIn.si, calc_approach_and_landing_energy()),
    ]

    reserve_segments = [
        ("  - 5% Route Reserve", calc_reference_route_reserve_fuel_mass(), calc_route_reserve_energy()),
        ("  - 30 min Loiter (L/D = 15.7)", calc_reference_loiter_fuel_mass(), calc_loiter_energy()),
        ("  - 50 NM Diversion", calc_reference_diversion_fuel_mass(), calc_diversion_energy()),
    ]

    e_trip = calc_trip_energy()
    e_reserve = calc_reserve_energy()
    e_total = calc_total_mission_energy()
    fuel_reserve_calc = calc_reference_reserve_fuel_mass()

    print("----- MISSION ENERGY & BATTERY MASS BREAKDOWN -----")
    print(f"Reference Turboprop Efficiency (eta_ref): {calc_reference_propulsion_efficiency() * 100:.2f} %")
    print(f"Electric Aircraft: MTOM = {MTOM}, eta_el = {ETA_ELECTRIC * 100:.1f} %, Range = {constraints.mission.range}\n")
    print(f"{'Segment':<32} | {'Ref Fuel':>10} | {'E_el [kWh]':>11} | {'m_Bat (Cell)':>13} | {'m_Bat (Pack)':>13}")
    print("-" * 90)

    for name, fuel, e in segments:
        print(
            f"{name:<32} | {fuel.to('kg'):7.1f} kg | {e.to('kWh'):11.1f} | "
            f"{calc_battery_cell_mass(e):10.1f} kg | {calc_battery_pack_mass(e):10.1f} kg"
        )

    print("-" * 90)
    print(
        f"{'TRIP TOTAL (Phases 1-5)':<32} | {ref_aircraft.fuel.tripMass.to('kg'):7.1f} kg | {e_trip.to('kWh'):11.1f} | "
        f"{calc_battery_cell_mass(e_trip):10.1f} kg | {calc_battery_pack_mass(e_trip):10.1f} kg"
    )
    print("-" * 90)

    for name, fuel, e in reserve_segments:
        print(
            f"{name:<32} | {fuel.to('kg'):7.1f} kg | {e.to('kWh'):11.1f} | "
            f"{calc_battery_cell_mass(e):10.1f} kg | {calc_battery_pack_mass(e):10.1f} kg"
        )

    print(
        f"{'6. Reserve Total (Ref: 186 kg)':<32} | {fuel_reserve_calc.to('kg'):7.1f} kg | {e_reserve.to('kWh'):11.1f} | "
        f"{calc_battery_cell_mass(e_reserve):10.1f} kg | {calc_battery_pack_mass(e_reserve):10.1f} kg"
    )
    print("=" * 90)
    total_fuel = SiValue(ref_aircraft.fuel.tripMass.si + fuel_reserve_calc.si, "kg")
    print(
        f"{'MISSION TOTAL (Trip + Reserve)':<32} | {total_fuel.to('kg'):7.1f} kg | {e_total.to('kWh'):11.1f} | "
        f"{calc_battery_cell_mass(e_total):10.1f} kg | {calc_battery_pack_mass(e_total):10.1f} kg"
    )

    print(calc_route_reserve_energy(MTOM))
    print(calc_loiter_energy(mtom=MTOM))
    print(calc_diversion_energy(mtom=MTOM))
    print(calc_trip_energy(MTOM))
    print(calc_route_reserve_energy(MTOM) + calc_loiter_energy(mtom=MTOM) + calc_diversion_energy(SiValue(50, "nm"), MTOM))
    print(calc_total_mission_energy(MTOM))
    print(calc_electric_range(SiValue(420, "Wh/kg"), 0.85, 12.1, SiValue(3260.4, "kg"), MTOM).to("nm"))