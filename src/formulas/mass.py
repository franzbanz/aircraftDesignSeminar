"""Mass estimation and aerodynamic geometry formulas.

Contains empirical and physical formulas for aircraft preliminary design.
"""

import math

from data import SiValue


def calc_wing_mass(
    mzfm: SiValue,
    b_s: SiValue,
    n_ult: float,
    d_root: SiValue,
    s_w: SiValue,
    delta_m_F: float = 0.0,
) -> SiValue:
    """Calculates wing mass based on MZFM, structural span, load factor, and geometry [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 116] for aircraft with MTOM > 5670 kg.

    Args:
        mzfm: Maximum zero-fuel mass MZFM [kg]. In Torenbeek's formula, MZFM is used because
            fuel stored in the wing relieves the wing root bending moment, making the zero-fuel
            state the critical sizing case. For battery-electric aircraft (especially with
            fuselage-mounted batteries and no consumable fuel), MZFM equals MTOM.
        b_s: Structural wingspan b_s = b / cos(phi_50) [m].
        n_ult: Ultimate load factor n_ult = 1.5 * n_max [-].
        d_root: Wing root thickness d_root [m].
        s_w: Wing reference area S [m^2].
        delta_m_F: Mass penalty/relief factor for wing design features [-]:
            - High-lift devices & ailerons: 0.00 (included)
            - Spoilers / speedbrakes: +0.02 (+2%)
            - 2 wing-mounted engines: -0.05 (-5%)
            - 4 wing-mounted engines: -0.10 (-10%)
            - Landing gear not wing-mounted: -0.05 (-5%)
            - Braced / strutted wing: -0.30 (-30%)

    Returns:
        Wing mass m_F [kg].
    """
    base_mass = mzfm * (
        6.67e-3
        * b_s**0.75
        * (1.0 + (1.905 / b_s) ** 0.5)
        * n_ult**0.55
        * ((b_s / d_root) / (mzfm / s_w)) ** 0.3
    )
    return SiValue(base_mass * (1.0 + delta_m_F), "kg")


def calc_landing_gear_mass_breakdown(
    mtom: SiValue, k_fw: float = 1.08
) -> tuple[SiValue, SiValue]:
    """Calculates main and nose landing gear masses separately based on MTOM [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 124] for commuter/transport aircraft.

    Args:
        mtom: Maximum take-off mass [kg].
        k_fw: Wing configuration factor [-] (1.08 for high-wing aircraft, 1.0 for low-wing aircraft).

    Returns:
        Tuple of (main_gear_mass, nose_gear_mass) [kg].
    """

    def calc_single_landing_gear_mass(
        k: float, m: float, a: float, b: float, c: float, d: float
    ) -> float:
        return k * (a + b * m**0.75 + c * m + d * m**1.5)

    coeff_main_gear = [18.1, 0.131, 0.019, 2.23e-5]
    coeff_nose_gear = [9.1, 0.082, 0.0, 2.97e-6]

    m_main_gear = SiValue(
        calc_single_landing_gear_mass(k_fw, mtom, *coeff_main_gear), "kg"
    )
    m_nose_gear = SiValue(
        calc_single_landing_gear_mass(k_fw, mtom, *coeff_nose_gear), "kg"
    )
    return m_main_gear, m_nose_gear


def calc_landing_gear_mass(mtom: SiValue, k_fw: float = 1.08) -> SiValue:
    """Calculates total landing gear mass based on MTOM [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 124] for commuter/transport aircraft.

    Args:
        mtom: Maximum take-off mass [kg].
        k_fw: Wing configuration factor [-] (1.08 for high-wing aircraft, 1.0 for low-wing aircraft).

    Returns:
        Total landing gear mass (main gear + nose gear) [kg].
    """
    m_main_gear, m_nose_gear = calc_landing_gear_mass_breakdown(mtom, k_fw)
    return SiValue(m_main_gear + m_nose_gear, "kg")


def calc_fuselage_mass(
    v_D: SiValue,
    r_H: SiValue,
    b_R: SiValue,
    h_R: SiValue,
    s_o: SiValue,
    delta_m_F: float,
) -> SiValue:
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
    base_mass = 0.23 * ((v_D * r_H) / (b_R + h_R)) ** 0.5 * s_o**1.2
    return SiValue(base_mass * (1.0 + delta_m_F), "kg")


def calc_empennage_mass(n_ult: float, s_htp: SiValue, s_vtp: SiValue) -> SiValue:
    """Calculates empennage mass based on ultimate load factor and tail areas [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 120] for small aircraft (v_D < 250 kts).

    Args:
        n_ult: Ultimate load factor [-].
        s_htp: Horizontal tailplane area S_HTP [m^2].
        s_vtp: Vertical tailplane area S_VTP [m^2].

    Returns:
        Total empennage mass [kg].
    """
    return SiValue(0.64 * (n_ult * (s_htp + s_vtp) ** 2) ** 0.75, "kg")


def calc_tailplane_mass(
    v_D: SiValue,
    surface_area: SiValue,
    phi_50_deg: float = 0.0,
    k: float = 1.0,
) -> SiValue:
    """Calculates mass of a single tailplane surface (horizontal or vertical) for transport aircraft [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 120]

    Args:
        v_D: Design diving speed [m/s].
        surface_area: Tailplane aerodynamic area (S_H or S_S) [m^2].
        phi_50_deg: Tailplane sweep angle at 50% chord line phi_50 [deg]. Defaults to 0.0.
        k: Configuration or trimming factor [-]:
            - Horizontal tail: k_H = 1.0 (fixed stabilizer), 1.1 (trimmable stabilizer).
            - Vertical tail: k_S = 1.0 (fuselage-mounted tail), 1.0 + 0.15 * (S_H * h_H) / (S_S * b_S) (T-tail).

    Returns:
        Tailplane mass [kg].
    """
    cos_phi = math.cos(math.radians(phi_50_deg))
    bracket = (
        11.9119 * (surface_area**0.2 * v_D) / (1000.0 * math.sqrt(cos_phi)) - 0.287
    )
    return SiValue(4.882 * surface_area * k * bracket, "kg")


def calc_empennage_mass_transport(
    v_D: SiValue,
    s_htp: SiValue,
    s_vtp: SiValue,
    phi_50_h_deg: float = 0.0,
    phi_50_v_deg: float = 0.0,
    k_h: float = 1.0,
    k_s: float = 1.0,
) -> SiValue:
    """Calculates total empennage mass for transport aircraft based on diving speed and tail areas [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 120] for transport aircraft

    Args:
        v_D: Design diving speed [m/s].
        s_htp: Horizontal tailplane area S_H [m^2].
        s_vtp: Vertical tailplane area S_S [m^2].
        phi_50_h_deg: Horizontal tail sweep angle at 50% chord phi_50,H [deg]. Defaults to 0.0.
        phi_50_v_deg: Vertical tail sweep angle at 50% chord phi_50,S [deg]. Defaults to 0.0.
        k_h: Trimming factor for horizontal tail [-]:
            - 1.0 for fixed stabilizer with elevator (festes HLW)
            - 1.1 for trimmable horizontal stabilizer (Flossentrimmung)
        k_s: Configuration factor for vertical tail [-]:
            - 1.0 for fuselage-mounted horizontal tail (HLW am Rumpf)
            - 1.0 + 0.15 * (S_H * h_H) / (S_S * b_S) for T-tail / cruciform tail (HLW am SLW)

    Returns:
        Total empennage mass m_empennage = m_HLW + m_SLW [kg].
    """
    m_hlw = calc_tailplane_mass(v_D, s_htp, phi_50_deg=phi_50_h_deg, k=k_h)
    m_slw = calc_tailplane_mass(v_D, s_vtp, phi_50_deg=phi_50_v_deg, k=k_s)
    return SiValue(m_hlw + m_slw, "kg")


def calc_pylons_mass(p_to: SiValue) -> SiValue:
    """Calculates cowling/nacelle and pylon mass based on total take-off shaft power [kg].

    Uses Torenbeek formula [Strohmayer - Flugzeugentwurf 2 | p. 123] for
    turboprop aircraft: m_C = 0.0635 * ESHP (includes engine mounts/pylons, firewall,
    and acoustic insulation). The turboprop correlation is chosen because the reference
    aircraft (Do 228) is a twin-engine turboprop and the wing-mounted electric propeller
    nacelles/pylons scale analogously with installed shaft power (whereas Torenbeek's
    small-aircraft formulas apply to piston engines).

    Args:
        p_to: Total take-off shaft power across all engines P_TO [W].

    Returns:
        Total cowling/nacelle and pylon mass m_C [kg].
    """
    eshp = p_to.to("hp")
    return SiValue(0.0635 * eshp, "kg")


def calc_systems_mass(mtom: SiValue) -> SiValue:
    """Calculates systems mass based on MTOM [kg].

    Uses Torenbeek approximation [Strohmayer - Flugzeugentwurf 2 | p. 126] for multi-engine small aircraft.

    Args:
        mtom: Maximum take-off mass [kg].

    Returns:
        Systems mass [kg].
    """
    return SiValue(0.11 * mtom, "kg")
