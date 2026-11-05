"""Propulsion, thrust, and electric power formulas."""

from constants import GRAVITY
from data import SiValue


def calc_electric_power_from_shaft_power(
    p_shaft: SiValue,
    eta_electric: float = 0.85,
) -> SiValue:
    """Calculates required electrical power from mechanical shaft power [W].

    P_el = P_shaft / eta_el

    Args:
        p_shaft: Mechanical shaft power P_shaft [W].
        eta_electric: Electric powertrain efficiency (inverter, motor, wiring) [-].

    Returns:
        Required electrical power P_el [W].
    """
    return SiValue(p_shaft.si / eta_electric, "W")


def calc_shaft_power_from_electric_power(
    p_electric: SiValue,
    eta_electric: float = 0.85,
) -> SiValue:
    """Calculates available mechanical shaft power from electrical power [W].

    P_shaft = P_el * eta_el

    Args:
        p_electric: Available electrical power P_el [W].
        eta_electric: Electric powertrain efficiency [-].

    Returns:
        Available mechanical shaft power P_shaft [W].
    """
    return SiValue(p_electric.si * eta_electric, "W")


def calc_thrust_from_thrust_loading(
    thrust_loading: float,
    mtom: SiValue,
    g: SiValue = GRAVITY,
) -> SiValue:
    """Calculates total aerodynamic thrust from thrust loading T/G [N].

    T = (T/G) * MTOM * g

    Args:
        thrust_loading: Thrust-to-weight ratio T/G [-].
        mtom: Aircraft take-off mass [kg].
        g: Gravitational acceleration [m/s^2]. Defaults to GRAVITY.

    Returns:
        Total thrust T [N].
    """
    return SiValue(thrust_loading * mtom.si * g.si, "N")


def calc_thrust_loading_from_thrust(
    thrust: SiValue,
    mtom: SiValue,
    g: SiValue = GRAVITY,
) -> float:
    """Calculates thrust loading T/G from aerodynamic thrust [-].

    T/G = T / (MTOM * g)

    Args:
        thrust: Aerodynamic thrust T [N].
        mtom: Aircraft take-off mass [kg].
        g: Gravitational acceleration [m/s^2]. Defaults to GRAVITY.

    Returns:
        Thrust-to-weight ratio T/G [-].
    """
    return float(thrust.si / (mtom.si * g.si))


def calc_electric_power_from_thrust(
    thrust: SiValue,
    speed: SiValue,
    eta_prop: float,
    eta_electric: float = 0.85,
) -> SiValue:
    """Calculates required electrical power from aerodynamic thrust and flight speed [W].

    P_el = (T * v) / (eta_prop * eta_el)

    Args:
        thrust: Aerodynamic thrust T [N].
        speed: True airspeed v [m/s].
        eta_prop: Propeller efficiency [-].
        eta_electric: Electric powertrain efficiency [-].

    Returns:
        Required electrical power P_el [W].
    """
    p_prop = thrust.si * speed.si
    return SiValue(p_prop / (eta_prop * eta_electric), "W")


def calc_thrust_from_electric_power(
    p_electric: SiValue,
    speed: SiValue,
    eta_prop: float,
    eta_electric: float = 0.85,
) -> SiValue:
    """Calculates aerodynamic thrust available from electrical power [N].

    T = (P_el * eta_prop * eta_el) / v

    Args:
        p_electric: Available electrical power P_el [W].
        speed: True airspeed v [m/s].
        eta_prop: Propeller efficiency [-].
        eta_electric: Electric powertrain efficiency [-].

    Returns:
        Available aerodynamic thrust T [N].
    """
    return SiValue((p_electric.si * eta_prop * eta_electric) / speed.si, "N")


def calc_electric_power_from_thrust_loading(
    thrust_loading: float,
    mtom: SiValue,
    speed: SiValue,
    eta_prop: float,
    eta_electric: float = 0.85,
    g: SiValue = GRAVITY,
) -> SiValue:
    """Calculates required electrical power from thrust loading T/G [W].

    P_el = ((T/G) * MTOM * g * v) / (eta_prop * eta_el)

    Args:
        thrust_loading: Thrust-to-weight ratio T/G [-].
        mtom: Aircraft take-off mass [kg].
        speed: True airspeed v [m/s].
        eta_prop: Propeller efficiency [-].
        eta_electric: Electric powertrain efficiency [-]. Defaults to 0.85.
        g: Gravitational acceleration [m/s^2]. Defaults to GRAVITY.

    Returns:
        Required electrical power P_el [W].
    """
    thrust = calc_thrust_from_thrust_loading(thrust_loading, mtom, g)
    return calc_electric_power_from_thrust(thrust, speed, eta_prop, eta_electric)


def calc_thrust_loading_from_electric_power(
    p_electric: SiValue,
    mtom: SiValue,
    speed: SiValue,
    eta_prop: float,
    eta_electric: float = 0.85,
    g: SiValue = GRAVITY,
) -> float:
    """Calculates achievable thrust loading T/G from electrical power [-].

    T/G = (P_el * eta_prop * eta_el) / (MTOM * g * v)

    Args:
        p_electric: Available electrical power P_el [W].
        mtom: Aircraft take-off mass [kg].
        speed: True airspeed v [m/s].
        eta_prop: Propeller efficiency [-].
        eta_electric: Electric powertrain efficiency [-]. Defaults to 0.85.
        g: Gravitational acceleration [m/s^2]. Defaults to GRAVITY.

    Returns:
        Thrust-to-weight ratio T/G [-].
    """
    thrust = calc_thrust_from_electric_power(p_electric, speed, eta_prop, eta_electric)
    return calc_thrust_loading_from_thrust(thrust, mtom, g)
