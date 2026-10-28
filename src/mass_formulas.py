"""Mass estimation and aerodynamic geometry formulas.

Contains empirical and physical formulas for aircraft preliminary design.
"""


def calc_landing_gear_mass(mtom: float, k_fw: float = 1.08) -> float:
    """Calculates total landing gear mass based on MTOM [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 124] for commuter/transport aircraft.

    Args:
        mtom: Maximum take-off mass [kg].
        k_fw: Wing configuration factor [-] (1.08 for high-wing aircraft, 1.0 for low-wing aircraft).

    Returns:
        Total landing gear mass (main gear + nose gear) [kg].
    """
    def calc_single_landing_gear_mass(k: float, m: float, a: float, b: float, c: float, d: float) -> float:
        """Calculates the mass of a single landing gear group (main or nose gear) [kg].

        Args:
            k: Wing configuration factor k_fw [-].
            m: Maximum take-off mass (MTOM) [kg].
            a, b, c, d: Empirical Torenbeek regression coefficients for the respective landing gear group.

        Returns:
            Mass of the single landing gear group [kg].
        """
        return k * (a + b * m**0.75 + c * m + d * m**1.5)

    coeff_main_gear = [18.1, 0.131, 0.019, 2.23e-5]
    coeff_nose_gear = [9.1, 0.082, 0.0, 2.97e-6]

    m_main_gear = calc_single_landing_gear_mass(k_fw, mtom, *coeff_main_gear)
    m_nose_gear = calc_single_landing_gear_mass(k_fw, mtom, *coeff_nose_gear)
    return m_main_gear + m_nose_gear


def calc_fuselage_mass(
    v_D: float,
    r_H: float,
    b_R: float,
    h_R: float,
    s_o: float,
    delta_m_F: float = 0.07,
) -> float:
    """Calculates fuselage mass based on diving speed, tail arm, and dimensions [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 121] for metallic fuselage.

    Args:
        v_D: Design diving speed [m/s].
        r_H: Horizontal tail lever arm [m].
        b_R: Maximum fuselage width [m].
        h_R: Maximum fuselage height [m].
        s_o: Wetted fuselage surface area S_O [m^2].
        delta_m_F: Mass penalty factor for special fuselage features [-] (e.g., 0.07 for fuselage-mounted landing gear, 0.08 for pressurized cabin).

    Returns:
        Fuselage mass [kg].
    """
    return 0.23 * ((v_D * r_H) / (b_R + h_R)) ** 0.5 * s_o ** 1.2 * (1.0 + delta_m_F)


def calc_empennage_mass(n_ult: float, s_htp: float, s_vtp: float) -> float:
    """Calculates empennage mass based on ultimate load factor and tail areas [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 120] for small aircraft (v_D < 250 kts).

    Args:
        n_ult: Ultimate load factor [-].
        s_htp: Horizontal tailplane area S_HTP [m^2].
        s_vtp: Vertical tailplane area S_VTP [m^2].

    Returns:
        Total empennage mass [kg].
    """
    return 0.64 * (n_ult * (s_htp + s_vtp) ** 2) ** 0.75


def calc_systems_mass(mtom: float) -> float:
    """Calculates systems mass based on MTOM [kg].

    Uses Torenbeek approximation [Strohmayer - Flugzeugentwurf 2 | p. 126] for multi-engine small aircraft.

    Args:
        mtom: Maximum take-off mass [kg].

    Returns:
        Systems mass [kg].
    """
    return 0.11 * mtom


def calc_mean_aerodynamic_chord(wing_area: float, wingspan: float) -> float:
    """Calculates mean aerodynamic chord c_mu [m] (geometric mean chord S / b).

    Args:
        wing_area: Wing reference area S_W [m^2].
        wingspan: Wingspan b_W [m].

    Returns:
        Mean aerodynamic chord c_mu [m].
    """
    return wing_area / wingspan


def calc_horizontal_tail_volume_coefficient(
    s_htp: float,
    r_h: float,
    wing_area: float,
    c_mu: float,
) -> float:
    """Calculates horizontal tail volume coefficient c_HT = (S_HTP * r_H) / (S_W * c_mu).

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
    s_vtp: float,
    r_v: float,
    wing_area: float,
    wingspan: float,
) -> float:
    """Calculates vertical tail volume coefficient c_VT = (S_VTP * r_V) / (S_W * b_W).

    Args:
        s_vtp: Vertical tailplane area S_VTP [m^2].
        r_v: Vertical tail lever arm r_V [m].
        wing_area: Wing reference area S_W [m^2].
        wingspan: Wingspan b_W [m].

    Returns:
        Vertical tail volume coefficient c_VT [-].
    """
    return (s_vtp * r_v) / (wing_area * wingspan)
