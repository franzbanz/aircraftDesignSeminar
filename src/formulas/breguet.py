"""Breguet range and endurance equations and their algebraic rearrangements."""

import math
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import GRAVITY
from data import SiValue

# ==============================================================================
# 1. BREGUET RANGE EQUATION & REARRANGEMENTS
# ==============================================================================


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
    range_ = (
        (cruise_speed / (GRAVITY * thrust_specific_fuel_consumption))
        * lift_to_drag
        * math.log(m_start / m_end)
    )
    return SiValue(range_, "m")


def calc_breguet_mass_fraction_from_range(
    range_: SiValue,
    lift_to_drag: float,
    cruise_speed: SiValue,
    thrust_specific_fuel_consumption: SiValue,
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
    breguet_factor = (
        cruise_speed / (GRAVITY * thrust_specific_fuel_consumption)
    ) * lift_to_drag
    return math.exp(-range_ / breguet_factor)


def calc_breguet_fuel_mass_from_range(
    m_start: SiValue,
    range_: SiValue,
    lift_to_drag: float,
    cruise_speed: SiValue,
    thrust_specific_fuel_consumption: SiValue,
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


# ==============================================================================
# 2. BREGUET ENDURANCE (TIME) EQUATIONS
# ==============================================================================


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


def calc_electric_cruise_energy(
    range_: SiValue,
    take_off_mass: SiValue,
    lift_to_drag: float,
    eta_electric: float,
) -> SiValue:
    """Calculates electrical battery energy required for horizontal cruise flight [J].

    Formula:
        E_el = (R * g * m_0) / (eta_el * (L/D))

    Args:
        range_: Target cruise range [m].
        take_off_mass: Aircraft take-off mass m_0 [kg].
        lift_to_drag: Cruise lift-to-drag ratio L/D [-].
        eta_electric: Powertrain efficiency eta_el [-].

    Returns:
        Required electrical energy [J].
    """
    energy_j = (range_ * GRAVITY * take_off_mass) / (eta_electric * lift_to_drag)
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
    from data import load_reference_aircraft

    ref = load_reference_aircraft()
    v_cr = ref.mission.cruiseSpeedTAS.si
    tsfc = ref.propulsion.tsfcCruise.si
    ld_cr = ref.aerodynamics.liftToDragRatioCruise
    ld_loit = ref.aerodynamics.liftToDragRatioLoiter

    print(
        "Cruise fuel mass (100NM):",
        calc_breguet_fuel_mass_from_range(
            SiValue(5950 - 24 - 36, "kg"), SiValue(100, "nm"), ld_cr, v_cr, tsfc
        ),
    )
    print(
        "Cruise fuel mass (50NM):",
        calc_breguet_fuel_mass_from_range(
            SiValue(5950 - 24 - 36 - 78 - 9, "kg"), SiValue(50, "nm"), ld_cr, v_cr, tsfc
        ),
    )
    print(
        "Total mission battery mass (285NM):",
        calc_electric_battery_mass_from_range(
            SiValue(285, "nm"), SiValue(420, "Wh/kg"), 0.85, 12.1, SiValue(8618, "kg")
        ),
    )
    print(
        "Cruise battery mass (100NM):",
        calc_electric_battery_mass_from_range(
            SiValue(100, "nm"), SiValue(420, "Wh/kg"), 0.85, 12.1, SiValue(8618, "kg")
        ),
    )
    print(
        "Cruise battery mass (50NM):",
        calc_electric_battery_mass_from_range(
            SiValue(50, "nm"), SiValue(420, "Wh/kg"), 0.85, 12.1, SiValue(8618, "kg")
        ),
    )
    print(
        "Loiter fuel mass (30min):",
        calc_breguet_fuel_mass_from_endurance(
            SiValue(5950 - 24 - 36 - 78 - 9, "kg"), SiValue(0.5, "h"), ld_loit, tsfc
        ),
    )
    print(
        "Cruise range (78kg):",
        calc_breguet_range(
            SiValue(5950 - 24 - 36, "kg"),
            SiValue(5950 - 24 - 36 - 78, "kg"),
            ld_cr,
            v_cr,
            tsfc,
        ).to("nm"),
    )
