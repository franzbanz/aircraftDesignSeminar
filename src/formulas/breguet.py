"""Breguet range and endurance equations and their algebraic rearrangements."""

import math
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data import SiValue
from constants import GRAVITY


DEFAULT_CRUISE_SPEED = SiValue(200.0, "kts")  # [m/s] (Do 228 reference TAS: 200 kts)
DEFAULT_TSFC = SiValue(0.46, "lb/(h*lbf)")  # [kg/(N*s)] (Do 228 reference TSFC: 0.46 lb/(h*lbf))
DEFAULT_L_D_CRUISE = 12.1  # [-] (Do 228 reference cruise L/D)
DEFAULT_L_D_LOITER = 15.7  # [-] (Do 228 reference loiter L/D)


# ==============================================================================
# 1. BREGUET RANGE EQUATION & REARRANGEMENTS
# ==============================================================================


def calc_breguet_range(
    m_start: SiValue,
    m_end: SiValue,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed: SiValue = DEFAULT_CRUISE_SPEED,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
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
    range_ = (
        (cruise_speed / (GRAVITY * thrust_specific_fuel_consumption))
        * lift_to_drag
        * math.log(m_start / m_end)
    )
    return SiValue(range_, "m")


def calc_breguet_mass_fraction_from_range(
    range_: SiValue,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed: SiValue = DEFAULT_CRUISE_SPEED,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> float:
    """Calculates segment mass fraction M_ff = m_end / m_start for a given range [-].

    Formula:
        M_ff = m_end / m_start = exp(-R * g * TSFC / (v * (L/D)))

    Args:
        range_: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Mass fraction M_ff = m_end / m_start [-].
    """
    breguet_factor = (cruise_speed / (GRAVITY * thrust_specific_fuel_consumption)) * lift_to_drag
    return math.exp(-range_ / breguet_factor)


def calc_breguet_end_mass_from_range(
    m_start: SiValue,
    range_: SiValue,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed: SiValue = DEFAULT_CRUISE_SPEED,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> SiValue:
    """Calculates aircraft end mass after flying a given range [kg].

    Formula:
        m_end = m_start * exp(-R * g * TSFC / (v * (L/D)))

    Args:
        m_start: Aircraft mass at the start of the segment [kg].
        range_: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Aircraft mass at the end of the segment [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_range(
        range_, lift_to_drag, cruise_speed, thrust_specific_fuel_consumption
    )
    return SiValue(m_start * mass_fraction, "kg")


def calc_breguet_start_mass_from_range(
    m_end: SiValue,
    range_: SiValue,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed: SiValue = DEFAULT_CRUISE_SPEED,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> SiValue:
    """Calculates required aircraft start mass for a given end mass and range [kg].

    Formula:
        m_start = m_end / exp(-R * g * TSFC / (v * (L/D)))

    Args:
        m_end: Aircraft mass at the end of the segment [kg].
        range_: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Required aircraft mass at the start of the segment [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_range(
        range_, lift_to_drag, cruise_speed, thrust_specific_fuel_consumption
    )
    return SiValue(m_end / mass_fraction, "kg")


def calc_breguet_fuel_mass_from_range(
    m_start: SiValue,
    range_: SiValue,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed: SiValue = DEFAULT_CRUISE_SPEED,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> SiValue:
    """Calculates burned fuel mass for a given start mass and range [kg].

    Formula:
        m_fuel = m_start - m_end = m_start * (1 - exp(-R * g * TSFC / (v * (L/D))))

    Args:
        m_start: Aircraft mass at the start of the segment [kg].
        range_: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Burned fuel mass [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_range(
        range_, lift_to_drag, cruise_speed, thrust_specific_fuel_consumption
    )
    return SiValue(m_start * (1.0 - mass_fraction), "kg")


def calc_breguet_lift_to_drag_from_range(
    range_: SiValue,
    m_start: SiValue,
    m_end: SiValue,
    cruise_speed: SiValue = DEFAULT_CRUISE_SPEED,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> float:
    """Calculates required lift-to-drag ratio (L/D) from range and masses [-].

    Formula:
        L/D = (R * g * TSFC) / (v * ln(m_start / m_end))

    Args:
        range_: Flight range [m].
        m_start: Aircraft mass at the start of the segment [kg].
        m_end: Aircraft mass at the end of the segment [kg].
        cruise_speed: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Required lift-to-drag ratio [-].
    """
    return (range_ * GRAVITY * thrust_specific_fuel_consumption) / (
        cruise_speed * math.log(m_start / m_end)
    )


# ==============================================================================
# 2. BREGUET ENDURANCE (TIME) EQUATION & REARRANGEMENTS
# ==============================================================================


def calc_breguet_endurance(
    m_start: SiValue,
    m_end: SiValue,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> SiValue:
    """Calculates Breguet endurance (flight time) from start and end mass [s].

    Formula:
        t = (1 / (g * TSFC)) * (L/D) * ln(m_start / m_end)

    Args:
        m_start: Aircraft mass at the start of the segment [kg].
        m_end: Aircraft mass at the end of the segment [kg].
        lift_to_drag: Lift-to-drag ratio [-].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Breguet endurance [s].
    """
    endurance = (
        (1.0 / (GRAVITY * thrust_specific_fuel_consumption))
        * lift_to_drag
        * math.log(m_start / m_end)
    )
    return SiValue(endurance, "s")


def calc_breguet_mass_fraction_from_endurance(
    endurance: SiValue,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
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
    return math.exp(-(endurance * GRAVITY * thrust_specific_fuel_consumption) / lift_to_drag)


def calc_breguet_end_mass_from_endurance(
    m_start: SiValue,
    endurance: SiValue,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> SiValue:
    """Calculates aircraft end mass after loitering for a given endurance [kg].

    Formula:
        m_end = m_start * exp(-t * g * TSFC / (L/D))

    Args:
        m_start: Aircraft mass at the start of the segment [kg].
        endurance: Flight duration (endurance) [s].
        lift_to_drag: Lift-to-drag ratio [-].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Aircraft mass at the end of the segment [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_endurance(
        endurance, lift_to_drag, thrust_specific_fuel_consumption
    )
    return SiValue(m_start * mass_fraction, "kg")


def calc_breguet_start_mass_from_endurance(
    m_end: SiValue,
    endurance: SiValue,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> SiValue:
    """Calculates required aircraft start mass for a given end mass and endurance [kg].

    Formula:
        m_start = m_end / exp(-t * g * TSFC / (L/D))

    Args:
        m_end: Aircraft mass at the end of the segment [kg].
        endurance: Flight duration (endurance) [s].
        lift_to_drag: Lift-to-drag ratio [-].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Required aircraft mass at the start of the segment [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_endurance(
        endurance, lift_to_drag, thrust_specific_fuel_consumption
    )
    return SiValue(m_end / mass_fraction, "kg")


def calc_breguet_fuel_mass_from_endurance(
    m_start: SiValue,
    endurance: SiValue,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
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


def calc_breguet_lift_to_drag_from_endurance(
    endurance: SiValue,
    m_start: SiValue,
    m_end: SiValue,
    thrust_specific_fuel_consumption: SiValue = DEFAULT_TSFC,
) -> float:
    """Calculates required lift-to-drag ratio (L/D) from endurance and masses [-].

    Formula:
        L/D = (t * g * TSFC) / ln(m_start / m_end)

    Args:
        endurance: Flight duration (endurance) [s].
        m_start: Aircraft mass at the start of the segment [kg].
        m_end: Aircraft mass at the end of the segment [kg].
        thrust_specific_fuel_consumption: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Required lift-to-drag ratio [-].
    """
    return (endurance * GRAVITY * thrust_specific_fuel_consumption) / math.log(m_start / m_end)


# ==============================================================================
# 3. BATTERY-ELECTRIC RANGE & ENDURANCE EQUATIONS
# ==============================================================================


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
    range_ = (
        battery_energy_density
        * eta_electric
        * (1.0 / GRAVITY)
        * lift_to_drag
        * (battery_mass / take_off_mass)
    )
    return SiValue(range_, "m")


def calc_electric_battery_mass_from_range(
    range_: SiValue,
    battery_energy_density: SiValue,
    eta_electric: float,
    lift_to_drag: float,
    take_off_mass: SiValue,
) -> SiValue:
    """Calculates required battery mass for a given range [kg].

    Formula:
        m_bat = (R * g * m_0) / (e_bat * eta_el * (L/D))

    Args:
        range_: Target flight range [m].
        battery_energy_density: Gravimetric energy density of battery e_bat [J/kg].
        eta_electric: Total powertrain efficiency eta_el [-].
        lift_to_drag: Lift-to-drag ratio L/D [-].
        take_off_mass: Maximum take-off mass m_0 [kg].

    Returns:
        Required battery mass [kg].
    """
    m_bat = (range_ * GRAVITY * take_off_mass) / (
        battery_energy_density * eta_electric * lift_to_drag
    )
    return SiValue(m_bat, "kg")


if __name__ == "__main__":
    print("Cruise fuel mass (100NM):", calc_breguet_fuel_mass_from_range(SiValue(5950 - 24 - 36, "kg"), SiValue(100, "nm")))
    print("Cruise fuel mass (50NM):", calc_breguet_fuel_mass_from_range(SiValue(5950 - 24 - 36 - 78 - 9, "kg"), SiValue(50, "nm")))
    print("Total mission battery mass (100NM):", calc_electric_battery_mass_from_range(SiValue(215, "nm"), SiValue(420, "Wh/kg"), 0.85, 12.1, SiValue(8618, "kg")))
    print("Cruise battery mass (100NM):", calc_electric_battery_mass_from_range(SiValue(100, "nm"), SiValue(420, "Wh/kg"), 0.85, 12.1, SiValue(8618, "kg")))
    print("Cruise battery mass (50NM):", calc_electric_battery_mass_from_range(SiValue(50, "nm"), SiValue(420, "Wh/kg"), 0.85, 12.1, SiValue(8618, "kg")))
    print("Loiter fuel mass (30min):", calc_breguet_fuel_mass_from_endurance(SiValue(5950 - 24 - 36 - 78 - 9, "kg"), SiValue(0.5, "h")))
    print("Cruise range (78kg):", calc_breguet_range(SiValue(5950 - 24 - 36, "kg"), SiValue(5950 - 24 - 36 - 78, "kg")).to("nm"))
