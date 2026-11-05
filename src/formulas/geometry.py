"""Aerodynamic and geometric formulas for preliminary aircraft design."""

from data import SiValue


def calc_mean_aerodynamic_chord(wing_area: SiValue, wingspan: SiValue) -> SiValue:
    """Calculates mean aerodynamic chord c_mu [m] (geometric mean chord S / b).

    Args:
        wing_area: Wing reference area S_W [m^2].
        wingspan: Wingspan b_W [m].

    Returns:
        Mean aerodynamic chord c_mu [m].
    """
    return SiValue(wing_area / wingspan, "m")


def calc_horizontal_tail_volume_coefficient(
    s_htp: SiValue,
    r_h: SiValue,
    wing_area: SiValue,
    c_mu: SiValue,
) -> float:
    """Calculates horizontal tail volume coefficient c_HT = (S_HTP * r_H) / (S_W * c_mu) [-].

    Args:
        s_htp: Horizontal tailplane area S_HTP [m^2].
        r_h: Horizontal tail lever arm r_H [m].
        wing_area: Wing reference area S_W [m^2].
        c_mu: Mean aerodynamic chord c_mu [m].

    Returns:
        Horizontal tail volume coefficient c_HT [-].
    """
    return (s_htp * r_h) / (wing_area * c_mu)


def calc_vertical_tail_volume_coefficient(
    s_vtp: SiValue,
    r_v: SiValue,
    wing_area: SiValue,
    wingspan: SiValue,
) -> float:
    """Calculates vertical tail volume coefficient c_VT = (S_VTP * r_V) / (S_W * b_W) [-].

    Args:
        s_vtp: Vertical tailplane area S_VTP [m^2].
        r_v: Vertical tail lever arm r_V [m].
        wing_area: Wing reference area S_W [m^2].
        wingspan: Wingspan b_W [m].

    Returns:
        Vertical tail volume coefficient c_VT [-].
    """
    return (s_vtp * r_v) / (wing_area * wingspan)
