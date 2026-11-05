"""Physical constants and standard atmospheric reference values."""

from data import SiValue

GRAVITY = SiValue(9.81, "m/s^2")  # Standard gravitational acceleration
RHO_0 = SiValue(1.225, "kg/m^3")  # Sea level air density


def isa_density(h: SiValue) -> SiValue:
    """Calculates ambient air density according to ISA troposphere model [kg/m^3].

    Args:
        h: Geopotential altitude [m].

    Returns:
        Ambient air density at altitude h [kg/m^3].
    """
    return SiValue(RHO_0 * (1 - 2.25577e-5 * h) ** 4.2559, "kg/m^3")
