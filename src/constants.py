"""Physical constants and standard atmospheric reference values."""

import math

from data import SiValue

GRAVITY = SiValue(9.81, "m/s^2")  # Standard gravitational acceleration
RHO_0 = SiValue(1.225, "kg/m^3")  # Sea level air density
T_0 = SiValue(288.15, "K")  # Sea level standard temperature
GAMMA_AIR = 1.4  # Heat capacity ratio of dry air
R_AIR = 287.05  # Specific gas constant for dry air [J/(kg*K)]


def isa_temperature(h: SiValue) -> SiValue:
    """Calculates ambient air temperature according to ISA troposphere model [K].

    Args:
        h: Geopotential altitude [m].

    Returns:
        Ambient temperature at altitude h [K].
    """
    return SiValue(T_0 - 0.0065 * h, "K")


def isa_density(h: SiValue) -> SiValue:
    """Calculates ambient air density according to ISA troposphere model [kg/m^3].

    Args:
        h: Geopotential altitude [m].

    Returns:
        Ambient air density at altitude h [kg/m^3].
    """
    return SiValue(RHO_0 * (1 - 2.25577e-5 * h) ** 4.2559, "kg/m^3")


def isa_speed_of_sound(h: SiValue) -> SiValue:
    """Calculates ambient speed of sound according to ISA troposphere model [m/s].

    Args:
        h: Geopotential altitude [m].

    Returns:
        Ambient speed of sound at altitude h [m/s].
    """
    t = isa_temperature(h)
    return SiValue(math.sqrt(GAMMA_AIR * R_AIR * t), "m/s")


def isa_dynamic_viscosity(h: SiValue) -> SiValue:
    """Calculates dynamic viscosity of air using Sutherland's law [Pa*s].

    Args:
        h: Geopotential altitude [m].

    Returns:
        Dynamic viscosity at altitude h [Pa*s].
    """
    t = isa_temperature(h)
    mu = 1.789e-5 * ((t / 288.15) ** 1.5) * ((288.15 + 110.4) / (t + 110.4))
    return SiValue(mu, "Pa*s")
