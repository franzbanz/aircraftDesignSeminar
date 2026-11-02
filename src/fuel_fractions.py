"""Mission fuel fractions and kerosene-to-electric energy transfer calculator."""

from breguet import (
    calc_breguet_fuel_mass_from_endurance,
    calc_breguet_fuel_mass_from_range,
    calc_breguet_range,
)
from read_parameters import load_parameters
from read_reference_aircraft import load_reference_aircraft

params = load_parameters()
ref_aircraft = load_reference_aircraft()

GRAVITY = 9.81  # [m/s^2]
KTS_TO_MS = 1.852 / 3.6  # [m/s per kt]
MJ_TO_KWH = 1.0 / 3.6  # [kWh per MJ]

MTOM = 8600.0  # [kg] Design take-off mass of the electric aircraft
ETA_ELECTRIC = 0.85  # [-] Overall electric powertrain efficiency
L_D = 12.1  # [-] Cruise lift-to-drag ratio
L_D_LOITER = 15.7  # [-] Loiter lift-to-drag ratio


def calc_reference_propulsion_efficiency() -> float:
    """Calculates overall cruise propulsion efficiency of the reference turboprop aircraft [-].

    Uses efficiency = cruise_speed / (thrust_specific_fuel_consumption_si * fuel_energy_density),
    where thrust specific fuel consumption (TSFC) is converted from [lb/(h*lbf)] to SI units
    [kg/(N*s)] by dividing by (3600 * GRAVITY).
    """
    cruise_speed_ms = ref_aircraft.performance.cruiseSpeedTAS * KTS_TO_MS
    thrust_specific_fuel_consumption_si = ref_aircraft.propulsion.tsfcCruise / (3600.0 * GRAVITY)  # [kg/(N*s)]
    fuel_energy_density_j_per_kg = ref_aircraft.fuel.energyDensity * 1e6  # [J/kg]
    return cruise_speed_ms / (thrust_specific_fuel_consumption_si * fuel_energy_density_j_per_kg)


def calc_reference_propulsive_energy(fuel_mass_kg: float) -> float:
    """Converts burned kerosene mass of the reference aircraft into propulsive energy [kWh]."""
    chemical_energy_kwh = fuel_mass_kg * ref_aircraft.fuel.energyDensity * MJ_TO_KWH
    reference_propulsion_efficiency = calc_reference_propulsion_efficiency()
    return chemical_energy_kwh * reference_propulsion_efficiency


def calc_scaled_electric_energy(
    fuel_mass_ref_kg: float,
    m_start_ref_kg: float,
) -> float:
    """Scales reference segment fuel mass to required electric battery energy [kWh].

    Scales propulsive energy with the instantaneous mass ratio (MTOM / m_avg_ref).
    """
    m_avg_ref = m_start_ref_kg - 0.5 * fuel_mass_ref_kg
    propulsive_energy_ref_kwh = calc_reference_propulsive_energy(fuel_mass_ref_kg)

    propulsive_energy_new_kwh = propulsive_energy_ref_kwh * MTOM / m_avg_ref
    return propulsive_energy_new_kwh / ETA_ELECTRIC


def calc_taxi_and_takeoff_energy() -> float:
    """Calculates electric energy required for taxi-out and take-off [kWh].

    Scales the reference fuel energy with MTOM and uses the reference cruise
    propulsion efficiency.
    """
    m_start_ref = ref_aircraft.fuel.referenceMass
    fuel_ref = ref_aircraft.fuel.taxiOutAndTakeOff
    return calc_scaled_electric_energy(fuel_ref, m_start_ref)


def calc_cruise_energy(range_m: float = params.mission.range * 1000.0) -> float:
    """Calculates required electrical battery energy for horizontal cruise flight [kWh].

    Derived from steady level flight equilibrium (D = MTOM * g / (L/D)):
    E_el = (D * R) / eta = (R * g * MTOM) / (eta * L/D)
    Converted from Joules [Ws] to kilowatt-hours [kWh] by dividing by 3.6e6.

    Args:
        range_m: Cruise range [m]. Defaults to params.mission.range in meters.

    Returns:
        Required electrical energy [kWh].
    """
    energy_j = range_m * GRAVITY * MTOM / (ETA_ELECTRIC * L_D)
    return energy_j / 3.6e6


def calc_climb_and_descent_energy() -> float:
    """Calculates net additional electric energy required for climb and descent [kWh].

    Computes the equivalent Breguet range of the reference aircraft's combined
    Climb + Cruise + Descent phases (110.3 NM at 5950 kg reference mission mass)
    and compares it to the 100 NM (185.2 km) reference mission range to obtain
    the relative climb/descent overhead factor (~10.3%).
    """
    m_start_climb = ref_aircraft.fuel.referenceMass - ref_aircraft.fuel.taxiOutAndTakeOff
    m_end_descent = (
        m_start_climb
        - ref_aircraft.fuel.climb
        - ref_aircraft.fuel.cruise
        - ref_aircraft.fuel.descent
    )
    breguet_range_m = calc_breguet_range(m_start_climb, m_end_descent)
    reference_range_m = ref_aircraft.fuel.referenceRange
    climb_descent_overhead_factor = (breguet_range_m - reference_range_m) / reference_range_m

    reference_cruise_energy_kwh = calc_cruise_energy(reference_range_m)
    return climb_descent_overhead_factor * reference_cruise_energy_kwh


def calc_approach_and_landing_energy() -> float:
    """Calculates electric energy required for approach, landing, and taxi-in [kWh].

    Scales the reference fuel energy with MTOM (relative to the reference aircraft's
    segment mass) and uses the reference cruise propulsion efficiency.
    """
    m_start_ref = (
        ref_aircraft.fuel.referenceMass
        - ref_aircraft.fuel.taxiOutAndTakeOff
        - ref_aircraft.fuel.climb
        - ref_aircraft.fuel.cruise
        - ref_aircraft.fuel.descent
    )
    fuel_ref = ref_aircraft.fuel.approachLandingAndTaxiIn
    return calc_scaled_electric_energy(fuel_ref, m_start_ref)


def calc_trip_energy() -> float:
    """Calculates total electric trip energy (Phases 1 to 5) [kWh]."""
    return (
        calc_taxi_and_takeoff_energy()
        + calc_climb_and_descent_energy()
        + calc_cruise_energy()
        + calc_approach_and_landing_energy()
    )


def calc_reference_route_reserve_fuel_mass() -> float:
    """Calculates reference aircraft fuel mass for the 5% route reserve [kg]."""
    return params.mission.routeReserve * ref_aircraft.fuel.tripMass


def calc_reference_loiter_fuel_mass(
    loiter_time_h: float = params.mission.loiterTime,
    lift_to_drag_loiter: float = ref_aircraft.aerodynamics.liftToDragRatioLoiter,
) -> float:
    """Calculates reference aircraft fuel mass for loiter via Breguet endurance [kg]."""
    m_start_ref = ref_aircraft.fuel.referenceMass - ref_aircraft.fuel.tripMass
    return calc_breguet_fuel_mass_from_endurance(m_start_ref, loiter_time_h, lift_to_drag_loiter)


def calc_reference_diversion_fuel_mass(
    diversion_distance_m: float = params.mission.diversionDistance * 1000.0,
    lift_to_drag_cruise: float = ref_aircraft.aerodynamics.liftToDragRatioCruise,
) -> float:
    """Calculates reference aircraft fuel mass for diversion via Breguet range [kg]."""
    m_start_ref = ref_aircraft.fuel.referenceMass - ref_aircraft.fuel.tripMass
    return calc_breguet_fuel_mass_from_range(m_start_ref, diversion_distance_m, lift_to_drag_cruise)


def calc_reference_reserve_fuel_mass() -> float:
    """Calculates total reference reserve fuel mass from the three reserve components [kg]."""
    return (
        calc_reference_route_reserve_fuel_mass()
        + calc_reference_loiter_fuel_mass()
        + calc_reference_diversion_fuel_mass()
    )


def calc_route_reserve_energy() -> float:
    """Calculates electric energy required for the 5% route reserve [kWh]."""
    return params.mission.routeReserve * calc_trip_energy()


def calc_loiter_energy(
    loiter_time_h: float = params.mission.loiterTime,
    lift_to_drag_loiter: float = L_D_LOITER,
    loiter_speed_ms: float = params.performance.cruiseSpeedMin * KTS_TO_MS,
) -> float:
    """Calculates required electrical battery energy for loiter flight [kWh].

    Derived from the electric Breguet endurance equation (P_prop = D * v = MTOM * g * v / (L/D)_loiter):
    E_el = (v * t_loiter * g * MTOM) / (eta_el * (L/D)_loiter)
    Converted from Joules [Ws] to kilowatt-hours [kWh] by dividing by 3.6e6.

    Args:
        loiter_time_h: Loiter duration [h]. Defaults to params.mission.loiterTime.
        lift_to_drag_loiter: Lift-to-drag ratio in loiter [-]. Defaults to reference loiter L/D.
        loiter_speed_ms: True airspeed during loiter [m/s]. Defaults to params.performance.cruiseSpeedMin.

    Returns:
        Required electrical energy [kWh].
    """
    loiter_time_s = loiter_time_h * 3600.0
    energy_j = (loiter_speed_ms * loiter_time_s * GRAVITY * MTOM) / (ETA_ELECTRIC * lift_to_drag_loiter)
    return energy_j / 3.6e6


def calc_diversion_energy(
    diversion_distance_m: float = params.mission.diversionDistance * 1000.0,
) -> float:
    """Calculates electric energy required for diversion to alternate airport [kWh]."""
    return calc_cruise_energy(diversion_distance_m)


def calc_reserve_energy() -> float:
    """Calculates electric reserve energy (5% route + 30 min loiter + 50 NM diversion) [kWh]."""
    return calc_route_reserve_energy() + calc_loiter_energy() + calc_diversion_energy()


def calc_total_mission_energy() -> float:
    """Calculates total electric mission energy (Trip + Reserve) [kWh]."""
    return calc_trip_energy() + calc_reserve_energy()


def calc_battery_cell_mass(electric_energy_kwh: float) -> float:
    """Calculates required battery mass at cell level for a given electric energy [kg]."""
    cell_energy_density_kwh_per_kg = params.battery.cellEnergyDensityMax / 1000.0
    return electric_energy_kwh / cell_energy_density_kwh_per_kg


def calc_battery_pack_mass(electric_energy_kwh: float) -> float:
    """Calculates required battery mass at pack level (including cell-to-pack factor) [kg]."""
    return calc_battery_cell_mass(electric_energy_kwh) * params.battery.cellToPackFactorMin


if __name__ == "__main__":
    segments = [
        ("1. Taxi-out & Take-off", ref_aircraft.fuel.taxiOutAndTakeOff, calc_taxi_and_takeoff_energy()),
        (f"2. Cruise ({params.mission.range:.1f} km)", ref_aircraft.fuel.cruise, calc_cruise_energy()),
        ("3. Climb & Descent (+10.3% Ref.)", ref_aircraft.fuel.climb + ref_aircraft.fuel.descent, calc_climb_and_descent_energy()),
        ("4. Approach, Landing & Taxi-in", ref_aircraft.fuel.approachLandingAndTaxiIn, calc_approach_and_landing_energy()),
    ]

    reserve_segments = [
        ("  - 5% Route Reserve", calc_reference_route_reserve_fuel_mass(), calc_route_reserve_energy()),
        ("  - 30 min Loiter (L/D = 15.7)", calc_reference_loiter_fuel_mass(), calc_loiter_energy()),
        ("  - 50 NM Diversion", calc_reference_diversion_fuel_mass(), calc_diversion_energy()),
    ]

    e_trip_kwh = calc_trip_energy()
    e_reserve_kwh = calc_reserve_energy()
    e_total_kwh = calc_total_mission_energy()
    fuel_reserve_calc_kg = calc_reference_reserve_fuel_mass()

    print("----- MISSION ENERGY & BATTERY MASS BREAKDOWN -----")
    print(f"Reference Turboprop Efficiency (eta_ref): {calc_reference_propulsion_efficiency() * 100:.2f} %")
    print(f"Electric Aircraft: MTOM = {MTOM:.0f} kg, eta_el = {ETA_ELECTRIC * 100:.1f} %, Range = {params.mission.range}\n")
    print(f"{'Segment':<32} | {'Ref Fuel':>10} | {'E_el [kWh]':>11} | {'m_Bat (Cell)':>13} | {'m_Bat (Pack)':>13}")
    print("-" * 90)

    for name, fuel_kg, e_kwh in segments:
        print(
            f"{name:<32} | {fuel_kg:7.1f} kg | {e_kwh:11.1f} | "
            f"{calc_battery_cell_mass(e_kwh):10.1f} kg | {calc_battery_pack_mass(e_kwh):10.1f} kg"
        )

    print("-" * 90)
    print(
        f"{'TRIP TOTAL (Phases 1-5)':<32} | {ref_aircraft.fuel.tripMass:7.1f} kg | {e_trip_kwh:11.1f} | "
        f"{calc_battery_cell_mass(e_trip_kwh):10.1f} kg | {calc_battery_pack_mass(e_trip_kwh):10.1f} kg"
    )
    print("-" * 90)

    for name, fuel_kg, e_kwh in reserve_segments:
        print(
            f"{name:<32} | {fuel_kg:7.1f} kg | {e_kwh:11.1f} | "
            f"{calc_battery_cell_mass(e_kwh):10.1f} kg | {calc_battery_pack_mass(e_kwh):10.1f} kg"
        )

    print(
        f"{'6. Reserve Total (Ref: 186 kg)':<32} | {fuel_reserve_calc_kg:7.1f} kg | {e_reserve_kwh:11.1f} | "
        f"{calc_battery_cell_mass(e_reserve_kwh):10.1f} kg | {calc_battery_pack_mass(e_reserve_kwh):10.1f} kg"
    )
    print("=" * 90)
    print(
        f"{'MISSION TOTAL (Trip + Reserve)':<32} | {ref_aircraft.fuel.tripMass + fuel_reserve_calc_kg:7.1f} kg | {e_total_kwh:11.1f} | "
        f"{calc_battery_cell_mass(e_total_kwh):10.1f} kg | {calc_battery_pack_mass(e_total_kwh):10.1f} kg"
    )
