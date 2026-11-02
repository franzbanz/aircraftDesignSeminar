"""Breguet range and endurance equations and their algebraic rearrangements."""

import math

from read_reference_aircraft import load_reference_aircraft

ref_aircraft = load_reference_aircraft()

GRAVITY = 9.81  # [m/s^2]
KTS_TO_MS = 1.852 / 3.6  # [m/s per kt]

DEFAULT_CRUISE_SPEED_MS = ref_aircraft.performance.cruiseSpeedTAS * KTS_TO_MS  # [m/s]
DEFAULT_TSFC_SI = ref_aircraft.propulsion.tsfcCruise / (3600.0 * GRAVITY)  # [kg/(N*s)]
DEFAULT_L_D_CRUISE = ref_aircraft.aerodynamics.liftToDragRatioCruise  # [-]
DEFAULT_L_D_LOITER = ref_aircraft.aerodynamics.liftToDragRatioLoiter  # [-]


# ==============================================================================
# 1. BREGUET RANGE EQUATION & REARRANGEMENTS
# ==============================================================================


def calc_breguet_range(
    m_start_kg: float,
    m_end_kg: float,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed_ms: float = DEFAULT_CRUISE_SPEED_MS,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates Breguet range from start and end mass [m].

    Formula:
        R = (v / (g * TSFC_SI)) * (L/D) * ln(m_start / m_end)

    Args:
        m_start_kg: Aircraft mass at the start of the segment [kg].
        m_end_kg: Aircraft mass at the end of the segment [kg].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed_ms: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Breguet range [m].
    """
    return (
        (cruise_speed_ms / (GRAVITY * thrust_specific_fuel_consumption_si))
        * lift_to_drag
        * math.log(m_start_kg / m_end_kg)
    )


def calc_breguet_mass_fraction_from_range(
    range_m: float,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed_ms: float = DEFAULT_CRUISE_SPEED_MS,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates segment mass fraction M_ff = m_end / m_start for a given range [-].

    Formula:
        M_ff = m_end / m_start = exp(-R * g * TSFC_SI / (v * (L/D)))

    Args:
        range_m: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed_ms: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Mass fraction M_ff = m_end / m_start [-].
    """
    breguet_factor_m = (cruise_speed_ms / (GRAVITY * thrust_specific_fuel_consumption_si)) * lift_to_drag
    return math.exp(-range_m / breguet_factor_m)


def calc_breguet_end_mass_from_range(
    m_start_kg: float,
    range_m: float,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed_ms: float = DEFAULT_CRUISE_SPEED_MS,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates aircraft end mass after flying a given range [kg].

    Formula:
        m_end = m_start * exp(-R * g * TSFC_SI / (v * (L/D)))

    Args:
        m_start_kg: Aircraft mass at the start of the segment [kg].
        range_m: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed_ms: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Aircraft mass at the end of the segment [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_range(
        range_m, lift_to_drag, cruise_speed_ms, thrust_specific_fuel_consumption_si
    )
    return m_start_kg * mass_fraction


def calc_breguet_start_mass_from_range(
    m_end_kg: float,
    range_m: float,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed_ms: float = DEFAULT_CRUISE_SPEED_MS,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates required aircraft start mass for a given end mass and range [kg].

    Formula:
        m_start = m_end / exp(-R * g * TSFC_SI / (v * (L/D)))

    Args:
        m_end_kg: Aircraft mass at the end of the segment [kg].
        range_m: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed_ms: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Required aircraft mass at the start of the segment [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_range(
        range_m, lift_to_drag, cruise_speed_ms, thrust_specific_fuel_consumption_si
    )
    return m_end_kg / mass_fraction


def calc_breguet_fuel_mass_from_range(
    m_start_kg: float,
    range_m: float,
    lift_to_drag: float = DEFAULT_L_D_CRUISE,
    cruise_speed_ms: float = DEFAULT_CRUISE_SPEED_MS,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates burned fuel mass for a given start mass and range [kg].

    Formula:
        m_fuel = m_start - m_end = m_start * (1 - exp(-R * g * TSFC_SI / (v * (L/D))))

    Args:
        m_start_kg: Aircraft mass at the start of the segment [kg].
        range_m: Flight range [m].
        lift_to_drag: Lift-to-drag ratio [-].
        cruise_speed_ms: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Burned fuel mass [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_range(
        range_m, lift_to_drag, cruise_speed_ms, thrust_specific_fuel_consumption_si
    )
    return m_start_kg * (1.0 - mass_fraction)


def calc_breguet_lift_to_drag_from_range(
    range_m: float,
    m_start_kg: float,
    m_end_kg: float,
    cruise_speed_ms: float = DEFAULT_CRUISE_SPEED_MS,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates required lift-to-drag ratio (L/D) from range and masses [-].

    Formula:
        L/D = (R * g * TSFC_SI) / (v * ln(m_start / m_end))

    Args:
        range_m: Flight range [m].
        m_start_kg: Aircraft mass at the start of the segment [kg].
        m_end_kg: Aircraft mass at the end of the segment [kg].
        cruise_speed_ms: True airspeed in cruise [m/s].
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Required lift-to-drag ratio [-].
    """
    return (range_m * GRAVITY * thrust_specific_fuel_consumption_si) / (
        cruise_speed_ms * math.log(m_start_kg / m_end_kg)
    )


# ==============================================================================
# 2. BREGUET ENDURANCE (TIME) EQUATION & REARRANGEMENTS
# ==============================================================================


def calc_breguet_endurance(
    m_start_kg: float,
    m_end_kg: float,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates Breguet endurance (flight time) from start and end mass [h].

    Formula:
        t = (1 / (g * TSFC_SI)) * (L/D) * ln(m_start / m_end)

    Args:
        m_start_kg: Aircraft mass at the start of the segment [kg].
        m_end_kg: Aircraft mass at the end of the segment [kg].
        lift_to_drag: Lift-to-drag ratio [-]. Defaults to reference loiter L/D.
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Breguet endurance [h].
    """
    endurance_s = (
        (1.0 / (GRAVITY * thrust_specific_fuel_consumption_si))
        * lift_to_drag
        * math.log(m_start_kg / m_end_kg)
    )
    return endurance_s / 3600.0


def calc_breguet_mass_fraction_from_endurance(
    endurance_h: float,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates segment mass fraction M_ff = m_end / m_start for a given endurance [-].

    Formula:
        M_ff = m_end / m_start = exp(-t * g * TSFC_SI / (L/D))

    Args:
        endurance_h: Flight duration (endurance) [h].
        lift_to_drag: Lift-to-drag ratio [-]. Defaults to reference loiter L/D.
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Mass fraction M_ff = m_end / m_start [-].
    """
    endurance_s = endurance_h * 3600.0
    return math.exp(-(endurance_s * GRAVITY * thrust_specific_fuel_consumption_si) / lift_to_drag)


def calc_breguet_end_mass_from_endurance(
    m_start_kg: float,
    endurance_h: float,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates aircraft end mass after loitering for a given endurance [kg].

    Formula:
        m_end = m_start * exp(-t * g * TSFC_SI / (L/D))

    Args:
        m_start_kg: Aircraft mass at the start of the segment [kg].
        endurance_h: Flight duration (endurance) [h].
        lift_to_drag: Lift-to-drag ratio [-]. Defaults to reference loiter L/D.
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Aircraft mass at the end of the segment [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_endurance(
        endurance_h, lift_to_drag, thrust_specific_fuel_consumption_si
    )
    return m_start_kg * mass_fraction


def calc_breguet_start_mass_from_endurance(
    m_end_kg: float,
    endurance_h: float,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates required aircraft start mass for a given end mass and endurance [kg].

    Formula:
        m_start = m_end / exp(-t * g * TSFC_SI / (L/D))

    Args:
        m_end_kg: Aircraft mass at the end of the segment [kg].
        endurance_h: Flight duration (endurance) [h].
        lift_to_drag: Lift-to-drag ratio [-]. Defaults to reference loiter L/D.
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Required aircraft mass at the start of the segment [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_endurance(
        endurance_h, lift_to_drag, thrust_specific_fuel_consumption_si
    )
    return m_end_kg / mass_fraction


def calc_breguet_fuel_mass_from_endurance(
    m_start_kg: float,
    endurance_h: float,
    lift_to_drag: float = DEFAULT_L_D_LOITER,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates burned fuel mass for a given start mass and endurance [kg].

    Formula:
        m_fuel = m_start - m_end = m_start * (1 - exp(-t * g * TSFC_SI / (L/D)))

    Args:
        m_start_kg: Aircraft mass at the start of the segment [kg].
        endurance_h: Flight duration (endurance) [h].
        lift_to_drag: Lift-to-drag ratio [-]. Defaults to reference loiter L/D.
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Burned fuel mass [kg].
    """
    mass_fraction = calc_breguet_mass_fraction_from_endurance(
        endurance_h, lift_to_drag, thrust_specific_fuel_consumption_si
    )
    return m_start_kg * (1.0 - mass_fraction)


def calc_breguet_lift_to_drag_from_endurance(
    endurance_h: float,
    m_start_kg: float,
    m_end_kg: float,
    thrust_specific_fuel_consumption_si: float = DEFAULT_TSFC_SI,
) -> float:
    """Calculates required lift-to-drag ratio (L/D) from endurance and masses [-].

    Formula:
        L/D = (t * g * TSFC_SI) / ln(m_start / m_end)

    Args:
        endurance_h: Flight duration (endurance) [h].
        m_start_kg: Aircraft mass at the start of the segment [kg].
        m_end_kg: Aircraft mass at the end of the segment [kg].
        thrust_specific_fuel_consumption_si: Thrust specific fuel consumption [kg/(N*s)].

    Returns:
        Required lift-to-drag ratio [-].
    """
    endurance_s = endurance_h * 3600.0
    return (endurance_s * GRAVITY * thrust_specific_fuel_consumption_si) / math.log(m_start_kg / m_end_kg)

print("Cruise fuel mass (100NM):", calc_breguet_fuel_mass_from_range(5950 - 24 - 36, 185200))
print("Cruise fuel mass (50NM):", calc_breguet_fuel_mass_from_range(5950 - 24 - 36 - 78 - 9, 185200 / 2))
print("Loiter fuel mass (30min):", calc_breguet_fuel_mass_from_endurance(5950 - 24 - 36 - 78 - 9, 0.5))
print("Cruise range (78kg):", calc_breguet_range(5950 - 24 - 36, 5950 - 24 - 36 - 78))