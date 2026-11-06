"""Propulsion and thrust loading (T/G) formulas for propeller aircraft."""

from constants import GRAVITY
from data import SiValue


def calc_thrust_loading_from_power(
    power: SiValue,
    speed: SiValue,
    mtom: SiValue,
    eta_prop: float,
) -> float:
    """Calculates available thrust loading T/G from shaft power and flight speed [-].

    Formula:
        T/G = (P_shaft * eta_prop) / (MTOM * g * v)

    Args:
        power: Available mechanical shaft power P_shaft [W].
        speed: True flight speed v [m/s] (e.g. v_TO for take-off or v_cruise for cruise).
        mtom: Aircraft take-off mass [kg].
        eta_prop: Propeller efficiency at the given speed [-].

    Returns:
        Available thrust-to-weight ratio T/G [-].
    """
    return float((power.si * eta_prop) / (mtom.si * GRAVITY.si * speed.si))


def calc_cruise_thrust_and_power(
    mtom: SiValue,
    speed: SiValue,
    lift_to_drag: float,
    eta_prop: float,
) -> tuple[SiValue, SiValue]:
    """Calculates required aerodynamic thrust [N] and shaft power [W] in steady horizontal cruise.

    Formulas:
        T_cruise = (MTOM * g) / (L/D)
        P_shaft = (T_cruise * v) / eta_prop

    Args:
        mtom: Aircraft mass in cruise [kg].
        speed: True airspeed in cruise v_cruise [m/s].
        lift_to_drag: Cruise lift-to-drag ratio L/D [-].
        eta_prop: Propeller cruise efficiency [-].

    Returns:
        Tuple of (required cruise thrust [N], required mechanical shaft power [W]).
    """
    thrust = SiValue((mtom.si * GRAVITY.si) / lift_to_drag, "N")
    power = SiValue((thrust.si * speed.si) / eta_prop, "W")
    return thrust, power
