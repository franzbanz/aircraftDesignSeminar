"""Breguet range and endurance equations and their algebraic rearrangements."""

import math
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import GRAVITY
from data import SiValue


def calc_breguet_range(
    m_start: SiValue,
    m_end: SiValue,
    lift_to_drag: float,
    cruise_speed: SiValue,
    thrust_specific_fuel_consumption: SiValue,
) -> SiValue:
    """Calculates Breguet range from start and end mass [m].

    Formula:
        R = (v / (g * TSFC)) * (L/D) * ln(m_start / m_end)

    Args:
        m_start: Aircraft mass at the start of the segment [kg].
        m_end: Aircraft mass at the end of the segment [kg].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Breguet range [m].
    """
    range_m = (
        (cruise_speed / (GRAVITY * thrust_specific_fuel_consumption))
        * lift_to_drag
        * math.log(m_start / m_end)
    )
    return SiValue(range_m, "m")


def calc_breguet_mass_fraction_from_range(
    range_m: SiValue,
    lift_to_drag: float,
    cruise_speed: SiValue,
    thrust_specific_fuel_consumption: SiValue,
) -> float:
    """Calculates segment mass fraction M_ff = m_end / m_start for a given range [-].

    Formula:
        M_ff = m_end / m_start = exp(-R * g * TSFC / (v * (L/D)))

    Args:
        range_m: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Mass fraction M_ff = m_end / m_start [-].
    """
    breguet_factor = (
        cruise_speed / (GRAVITY * thrust_specific_fuel_consumption)
    ) * lift_to_drag
    return math.exp(-range_m / breguet_factor)


def calc_breguet_fuel_mass_from_range(
    m_start: SiValue,
    range_m: SiValue,
    lift_to_drag: float,
    cruise_speed: SiValue,
    thrust_specific_fuel_consumption: SiValue,
) -> SiValue:
    """Calculates burned fuel mass for a given start mass and range [kg].

    Formula:
        m_fuel = m_start - m_end = m_start * (1 - exp(-R * g * TSFC / (v * (L/D))))

    Args:
        m_start: Aircraft mass at the start of the segment [kg].
        range_m: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Burned fuel mass [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_range(
        range_m, lift_to_drag, cruise_speed, thrust_specific_fuel_consumption
    )
    return SiValue(m_start * (1.0 - mass_fraction), "kg")


def calc_breguet_mass_fraction_from_endurance(
    endurance: SiValue,
    lift_to_drag: float,
    thrust_specific_fuel_consumption: SiValue,
) -> float:
    """Calculates segment mass fraction M_ff = m_end / m_start for a given endurance [-].

    Formula:
        M_ff = m_end / m_start = exp(-t * g * TSFC / (L/D))

    Args:
        endurance: Flight duration (endurance) [s].
        lift_to_drag: Lift-to-drag ratio [-].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Mass fraction M_ff = m_end / m_start [-].
    """
    return math.exp(
        -(endurance * GRAVITY * thrust_specific_fuel_consumption) / lift_to_drag
    )


def calc_breguet_fuel_mass_from_endurance(
    m_start: SiValue,
    endurance: SiValue,
    lift_to_drag: float,
    thrust_specific_fuel_consumption: SiValue,
) -> SiValue:
    """Calculates burned fuel mass for a given start mass and endurance [kg].

    Formula:
        m_fuel = m_start - m_end = m_start * (1 - exp(-t * g * TSFC / (L/D)))

    Args:
        m_start: Aircraft mass at the start of the segment [kg].
        endurance: Flight duration (endurance) [s].
        lift_to_drag: Lift-to-drag ratio [-].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Burned fuel mass [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_endurance(
        endurance, lift_to_drag, thrust_specific_fuel_consumption
    )
    return SiValue(m_start * (1.0 - mass_fraction), "kg")


def calc_electric_range(
    battery_energy_density: SiValue,
    eta_electric: float,
    lift_to_drag: float,
    battery_mass: SiValue,
    take_off_mass: SiValue,
) -> SiValue:
    """Calculates range for a battery-electric aircraft [m].

    Formula:
        R = e_bat * eta_el * (1 / g) * (L/D) * (m_bat / m_0)

    Args:
        battery_energy_density: Gravimetric energy density of battery e_bat [J/kg].
        eta_electric: Total powertrain efficiency eta_el [-].
        lift_to_drag: Lift-to-drag ratio L/D [-].
        battery_mass: Installed battery mass m_bat [kg].
        take_off_mass: Maximum take-off mass m_0 [kg].

    Returns:
        Flight range [m].
    """
    range_m = (
        battery_energy_density
        * eta_electric
        * (1.0 / GRAVITY)
        * lift_to_drag
        * (battery_mass / take_off_mass)
    )
    return SiValue(range_m, "m")


def calc_electric_battery_mass_from_range(
    range_m: SiValue,
    battery_energy_density: SiValue,
    eta_electric: float,
    lift_to_drag: float,
    take_off_mass: SiValue,
) -> SiValue:
    """Calculates required battery mass for a given range [kg].

    Formula:
        m_bat = (R * g * m_0) / (e_bat * eta_el * (L/D))

    Args:
        range_m: Target flight range [m].
        battery_energy_density: Gravimetric energy density of battery e_bat [J/kg].
        eta_electric: Total powertrain efficiency eta_el [-].
        lift_to_drag: Lift-to-drag ratio L/D [-].
        take_off_mass: Maximum take-off mass m_0 [kg].

    Returns:
        Required battery mass [kg].
    """
    m_bat = (range_m * GRAVITY * take_off_mass) / (
        battery_energy_density * eta_electric * lift_to_drag
    )
    return SiValue(m_bat, "kg")


def calc_electric_cruise_energy(
    range_m: SiValue,
    take_off_mass: SiValue,
    lift_to_drag: float,
    eta_electric: float,
) -> SiValue:
    """Calculates electrical battery energy required for horizontal cruise flight [J].

    Formula:
        E_el = (R * g * m_0) / (eta_el * (L/D))

    Args:
        range_m: Target cruise range [m].
        take_off_mass: Aircraft take-off mass m_0 [kg].
        lift_to_drag: Cruise lift-to-drag ratio L/D [-].
        eta_electric: Powertrain efficiency eta_el [-].

    Returns:
        Required electrical energy [J].
    """
    energy_j = (range_m * GRAVITY * take_off_mass) / (eta_electric * lift_to_drag)
    return SiValue(energy_j, "J")


def calc_electric_loiter_energy(
    loiter_time: SiValue,
    loiter_speed: SiValue,
    take_off_mass: SiValue,
    lift_to_drag_loiter: float,
    eta_electric: float,
) -> SiValue:
    """Calculates electrical battery energy required for loiter hold [J].

    Derived from steady level flight equilibrium (P_el = D * v / eta_el):
        E_el = (v * t_loiter * g * m_0) / (eta_el * (L/D)_loiter)

    Args:
        loiter_time: Loiter hold duration [s].
        loiter_speed: True airspeed during loiter [m/s].
        take_off_mass: Aircraft take-off mass m_0 [kg].
        lift_to_drag_loiter: Loiter lift-to-drag ratio [-].
        eta_electric: Powertrain efficiency eta_el [-].

    Returns:
        Required electrical energy [J].
    """
    energy_j = (loiter_speed * loiter_time * GRAVITY * take_off_mass) / (
        eta_electric * lift_to_drag_loiter
    )
    return SiValue(energy_j, "J")


if __name__ == "__main__":
    from data import (
        load_constraints,
        load_design_parameters,
        load_reference_aircraft_data,
    )

    ref = load_reference_aircraft_data()
    des = load_design_parameters()
    con = load_constraints()

    v_cr_ref = ref.mission.cruiseSpeedTAS.si
    tsfc_ref = ref.propulsion.tsfcCruise.si
    ld_cr_ref = ref.aerodynamics.liftToDragRatioCruise
    ld_loit_ref = ref.aerodynamics.liftToDragRatioLoiter

    m_start_cr_ref = SiValue(
        ref.fuel.referenceMass.si - ref.fuel.taxiOutAndTakeOff.si - ref.fuel.climb.si,
        "kg",
    )
    m_end_cr_ref = SiValue(m_start_cr_ref - ref.fuel.cruise.si, "kg")
    m_start_div_ref = SiValue(m_end_cr_ref - ref.fuel.descent.si, "kg")

    mtom_el = des.initialSizing.maximumTakeOffMass.si
    ld_cr_el = ref.aerodynamics.liftToDragRatioCruise
    ld_loit_el = des.aerodynamics.liftToDragRatioLoiter
    eta_el = des.propulsion.etaElectric
    e_pack = SiValue(
        con.battery.cellEnergyDensityMax.si / con.battery.cellToPackFactorMin,
        "J/kg",
    )
    v_cr_el = des.mission.cruiseSpeedTAS.si

    print("Reference Aircraft (Kerosene / Breguet):")
    print(
        f"  Cruise fuel mass ({ref.fuel.referenceRange}): "
        f"{calc_breguet_fuel_mass_from_range(m_start_cr_ref, ref.fuel.referenceRange.si, ld_cr_ref, v_cr_ref, tsfc_ref):.1f}"
    )
    print(
        f"  Diversion fuel mass ({con.mission.diversionDistance}): "
        f"{calc_breguet_fuel_mass_from_range(m_start_div_ref, con.mission.diversionDistance.si, ld_cr_ref, v_cr_ref, tsfc_ref):.1f}"
    )
    print(
        f"  Loiter fuel mass ({con.mission.loiterTime}): "
        f"{calc_breguet_fuel_mass_from_endurance(m_start_div_ref, con.mission.loiterTime.si, ld_loit_ref, tsfc_ref):.1f}"
    )
    r_cr_ref = calc_breguet_range(
        m_start_cr_ref, m_end_cr_ref, ld_cr_ref, v_cr_ref, tsfc_ref
    ).to("nm")
    print(f"  Cruise range (for {ref.fuel.cruise} fuel): {r_cr_ref:.1f}")

    print("\nBattery-Electric Aircraft (Breguet Electric):")
    m_bat_cr = calc_electric_battery_mass_from_range(
        des.mission.range.si, e_pack, eta_el, ld_cr_el, mtom_el
    )
    print(f"  Cruise battery pack mass ({des.mission.range}): {m_bat_cr:.1f}")
    m_bat_div = calc_electric_battery_mass_from_range(
        con.mission.diversionDistance.si, e_pack, eta_el, ld_cr_el, mtom_el
    )
    print(
        f"  Diversion battery pack mass ({con.mission.diversionDistance}): {m_bat_div:.1f}"
    )
    e_cr = calc_electric_cruise_energy(
        des.mission.range.si, mtom_el, ld_cr_el, eta_el
    ).to("kWh")
    print(f"  Cruise electric energy ({des.mission.range}): {e_cr:.1f}")
    e_loit = calc_electric_loiter_energy(
        con.mission.loiterTime.si, v_cr_el, mtom_el, ld_loit_el, eta_el
    ).to("kWh")
    print(f"  Loiter electric energy ({con.mission.loiterTime}): {e_loit:.1f}")
    r_achieved = calc_electric_range(e_pack, eta_el, ld_cr_el, m_bat_cr, mtom_el).to(
        "nm"
    )
    print(f"  Cruise range achieved ({m_bat_cr:.1f} pack): {r_achieved:.1f}")
