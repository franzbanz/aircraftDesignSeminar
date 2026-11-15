"""Aerodynamic friction coefficients, roughness cutoffs, form factors, and parasite drag buildup."""

import math
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import GRAVITY, isa_density, isa_dynamic_viscosity, isa_speed_of_sound
from data import SiValue


def calc_dynamic_pressure(velocity: SiValue, altitude: SiValue) -> SiValue:
    """Calculates dynamic pressure q = 0.5 * rho(h) * v^2 from true airspeed and ISA altitude [Pa].

    Args:
        velocity: True airspeed (TAS) [m/s].
        altitude: Flight altitude [m].

    Returns:
        Dynamic pressure q [Pa].
    """
    rho = isa_density(altitude)
    return SiValue(0.5 * rho * (velocity**2), "Pa")


def calc_cruise_lift_coefficient(
    wing_loading: float,
    velocity: SiValue,
    altitude: SiValue,
) -> float:
    """Calculates lift coefficient in steady horizontal flight c_A = (m / S) * g / q [-].

    Args:
        wing_loading: Wing loading m / S [kg/m^2].
        velocity: True airspeed (TAS) [m/s].
        altitude: Flight altitude [m].

    Returns:
        Cruise lift coefficient c_A [-].
    """
    q = calc_dynamic_pressure(velocity, altitude)
    return (wing_loading * GRAVITY) / q


def calc_mach_number(velocity: SiValue, altitude: SiValue) -> float:
    """Calculates flight Mach number from true airspeed and ISA flight altitude [-].

    Args:
        velocity: True airspeed (TAS) [m/s].
        altitude: Flight altitude [m].

    Returns:
        Flight Mach number Ma [-].
    """
    a = isa_speed_of_sound(altitude)
    return velocity / a


def calc_reynolds_number(
    velocity: SiValue,
    length: SiValue,
    altitude: SiValue,
) -> float:
    """Calculates flight Reynolds number from flight conditions and characteristic length [-].

    Args:
        velocity: True airspeed (TAS) [m/s].
        length: Characteristic reference length (e.g. mean aerodynamic chord or fuselage length) [m].
        altitude: Flight altitude [m].

    Returns:
        Flight Reynolds number Re [-].
    """
    rho = isa_density(altitude)
    mu = isa_dynamic_viscosity(altitude)
    return (rho * velocity * length) / mu


def calc_cf_flat_plate(
    re: float,
    mach: float = 0.0,
    laminar_fraction: float = 0.0,
) -> float:
    """Calculates mixed laminar/turbulent skin friction coefficient for flat plates [Strohmayer - Flugzeugentwurf 2 | p. 83].

    Combines Blasius laminar friction and Prandtl-Schlichting turbulent friction
    (with compressibility correction for Ma > 0.3) weighted by `laminar_fraction`.
    Typical Raymer rules of thumb: 0.05-0.10 for conventional aluminum wings/tails,
    0.0-0.05 for fuselages, up to 0.30-0.50 for smooth composite NLF wings.

    Args:
        re: Reynolds number Re [-].
        mach: Mach number Ma [-]. Defaults to 0.0.
        laminar_fraction: Fraction of wetted surface with laminar boundary layer [0..1]. Defaults to 0.0.

    Returns:
        Skin friction coefficient c_f [-].
    """
    if re <= 0:
        raise ValueError(f"Reynolds number must be positive (got {re})")
    if not 0.0 <= laminar_fraction <= 1.0:
        raise ValueError(f"laminar_fraction must be in [0, 1] (got {laminar_fraction})")

    cf_lam = 1.328 / math.sqrt(re)
    cf_turb_base = 0.455 / (math.log10(re) ** 2.58)
    cf_turb = (
        cf_turb_base / ((1.0 + 0.144 * (mach**2)) ** 0.65)
        if mach > 0.3
        else cf_turb_base
    )
    return laminar_fraction * cf_lam + (1.0 - laminar_fraction) * cf_turb


def calc_delta_cf_body(
    re: float,
    l_over_d: float,
    laminar_fraction: float = 0.0,
) -> float:
    """Calculates additional 3D skin friction increment for slender bodies [Strohmayer - Flugzeugentwurf 2 | p. 83].

    Args:
        re: Reynolds number Re [-].
        l_over_d: Fineness ratio l/d (length over diameter) [-].
        laminar_fraction: Fraction of body surface with laminar boundary layer [0..1]. Defaults to 0.0.

    Returns:
        Additional 3D friction increment Delta c_f [-].
    """
    if re <= 0:
        raise ValueError(f"Reynolds number must be positive (got {re})")
    if not 0.0 <= laminar_fraction <= 1.0:
        raise ValueError(f"laminar_fraction must be in [0, 1] (got {laminar_fraction})")

    d_cf_lam = (2.0 / re) * l_over_d
    d_cf_turb = (0.0016 / (re**0.4)) * l_over_d
    return laminar_fraction * d_cf_lam + (1.0 - laminar_fraction) * d_cf_turb


def calc_effective_reynolds_number(
    re: float,
    length: SiValue,
    k: SiValue,
    mach: float = 0.0,
) -> float:
    """Calculates effective Reynolds number considering surface roughness cutoff [Strohmayer - Flugzeugentwurf 2 | p. 85].

    Uses the compressible cutoff formula for Ma > 0.3 and the incompressible formula for Ma <= 0.3.

    Args:
        re: Actual flight Reynolds number Re [-].
        length: Characteristic length (e.g. chord or body length) [m].
        k: Equivalent sand grain roughness height [m].
        mach: Mach number Ma [-]. Defaults to 0.0 (incompressible).

    Returns:
        Effective Reynolds number min(Re, Re_cutoff) [-].
    """
    ratio = length / k
    if mach > 0.3:
        re_cutoff = 44.62 * (ratio**1.053) * (mach**1.16)
    else:
        re_cutoff = 38.21 * (ratio**1.053)
    return min(re, re_cutoff)


def calc_form_factor_wing(
    d_over_l: float,
    x_d_over_l: float,
    mach: float,
    sweep_d_max_deg: float = 0.0,
) -> float:
    """Calculates form factor for lifting surfaces (wing, tailplane).

    Based on Raymer / Nikolai formulation [Strohmayer - Flugzeugentwurf 2 | p. 89].

    Args:
        d_over_l: Relative airfoil thickness d/l = t/c [-].
        x_d_over_l: Chordwise location of maximum thickness x_d/l = (x/c)_tmax [-] (typically 0.3 - 0.4).
        mach: Flight Mach number M [-].
        sweep_d_max_deg: Sweep angle at maximum thickness line phi_d_max [deg]. Defaults to 0.0.

    Returns:
        Form factor FF_Fl [-].
    """
    if x_d_over_l <= 0:
        raise ValueError(f"x_d/l must be positive (got {x_d_over_l})")
    if mach <= 0:
        raise ValueError(
            f"Mach number must be positive for Raymer form factor (got {mach})"
        )

    thickness_term = 1.0 + (0.6 / x_d_over_l) * d_over_l + 100.0 * (d_over_l**4)
    cos_sweep = math.cos(math.radians(sweep_d_max_deg))
    mach_sweep_term = 1.34 * (mach**0.18) * (cos_sweep**0.28)
    return thickness_term * mach_sweep_term


def calc_form_factor_fuselage(l_over_d: float) -> float:
    """Calculates form factor for fuselage / 3D body of revolution.

    Based on Raymer / Nikolai formulation [Strohmayer - Flugzeugentwurf 2 | p. 89].

    Args:
        l_over_d: Fineness ratio l/d (fuselage length over diameter) [-].

    Returns:
        Form factor FF_Rumpf [-].
    """
    if l_over_d <= 0:
        raise ValueError(f"Fineness ratio l/d must be positive (got {l_over_d})")
    return 1.0 + (60.0 / (l_over_d**3)) + (l_over_d / 400.0)


def calc_component_drag_area(
    c_f: float,
    form_factor: float,
    interference_factor: float,
    wetted_area: SiValue,
) -> SiValue:
    """Calculates component parasite drag area [Strohmayer - Flugzeugentwurf 2 | p. 88] [m^2].

    Args:
        c_f: Skin friction coefficient [-].
        form_factor: Component form factor FF [-].
        interference_factor: Component aerodynamic interference factor IF_i [Strohmayer - Flugzeugentwurf 2 | p. 91] [-]:
            - High/mid wing with fairing: 1.0
            - Low wing without fairing: 1.1 - 1.4 (typical: 1.25)
            - Conventional winglet: 1.04
            - Blended winglet: 1.01
            - Tip tank: 1.25
            - Aerodynamic strut: 1.1
            - Nacelle directly under fuselage: 1.5
            - Nacelle < 1 engine diameter: 1.3
            - Nacelle > 1 engine diameter: 1.0
        wetted_area: Component wetted area S_wet [m^2].

    Returns:
        Component drag area [m^2].
    """
    return SiValue(c_f * form_factor * interference_factor * wetted_area, "m^2")


def calc_wing_zero_lift_drag_coefficient(
    velocity: SiValue,
    altitude: SiValue,
    mean_aerodynamic_chord: SiValue,
    rel_thickness: float,
    sweep_deg: float = 0.0,
    x_d_over_l: float = 0.35,
    interference_factor: float = 1.0,
    k_roughness: SiValue = SiValue(6.34e-6, "m"),
    laminar_fraction: float = 0.0,
) -> float:
    """Calculates wing zero-lift drag coefficient c_W0,wing = 2 * c_f * FF_wing * IF_wing [Strohmayer - Flugzeugentwurf 2 | p. 88] [-].

    Args:
        velocity: True airspeed (TAS) [m/s].
        altitude: Flight altitude [m].
        mean_aerodynamic_chord: Mean aerodynamic chord c_mu [m].
        rel_thickness: Relative airfoil thickness t/c [-].
        sweep_deg: Sweep angle at maximum thickness / half-chord line [deg]. Defaults to 0.0.
        x_d_over_l: Chordwise location of maximum thickness (x/c)_tmax [-]. Defaults to 0.35.
        interference_factor: Wing interference factor IF_wing [-]. Defaults to 1.0.
        k_roughness: Equivalent sand grain surface roughness [m]. Defaults to 6.34e-6 m (smooth paint).
        laminar_fraction: Laminar boundary layer fraction [0..1]. Defaults to 0.0.

    Returns:
        Wing zero-lift drag coefficient c_W0,wing [-].
    """
    mach = calc_mach_number(velocity, altitude)
    re_wing = calc_reynolds_number(velocity, mean_aerodynamic_chord, altitude)
    re_eff = calc_effective_reynolds_number(
        re_wing, mean_aerodynamic_chord, k_roughness, mach
    )
    cf_wing = calc_cf_flat_plate(re_eff, mach, laminar_fraction)
    ff_wing = calc_form_factor_wing(
        d_over_l=rel_thickness,
        x_d_over_l=x_d_over_l,
        mach=mach,
        sweep_d_max_deg=sweep_deg,
    )
    return 2.0 * cf_wing * ff_wing * interference_factor


def calc_fuselage_drag_area(
    velocity: SiValue,
    altitude: SiValue,
    length: SiValue,
    slenderness_ratio: float,
    wetted_area: SiValue,
    interference_factor: float = 1.0,
    k_roughness: SiValue = SiValue(6.34e-6, "m"),
    laminar_fraction: float = 0.0,
) -> SiValue:
    """Calculates fuselage parasite drag area [Strohmayer - Flugzeugentwurf 2 | p. 88] [m^2].

    Args:
        velocity: True airspeed (TAS) [m/s].
        altitude: Flight altitude [m].
        length: Fuselage length l_R [m].
        slenderness_ratio: Fuselage slenderness ratio l_R / d_equiv [-].
        wetted_area: Fuselage wetted surface area S_O [m^2].
        interference_factor: Fuselage interference factor IF_fuse [-]. Defaults to 1.0.
        k_roughness: Equivalent sand grain surface roughness [m]. Defaults to 6.34e-6 m.
        laminar_fraction: Laminar boundary layer fraction [0..1]. Defaults to 0.0.

    Returns:
        Fuselage parasite drag area [m^2].
    """
    mach = calc_mach_number(velocity, altitude)
    re_fuse = calc_reynolds_number(velocity, length, altitude)
    re_eff = calc_effective_reynolds_number(re_fuse, length, k_roughness, mach)
    cf_fuse = calc_cf_flat_plate(re_eff, mach, laminar_fraction) + calc_delta_cf_body(
        re_eff, slenderness_ratio, laminar_fraction
    )
    ff_fuse = calc_form_factor_fuselage(slenderness_ratio)
    return calc_component_drag_area(cf_fuse, ff_fuse, interference_factor, wetted_area)


def calc_tailplane_drag_area(
    velocity: SiValue,
    altitude: SiValue,
    area: SiValue,
    aspect_ratio: float,
    rel_thickness: float = 0.12,
    sweep_deg: float = 0.0,
    x_d_over_l: float = 0.30,
    interference_factor: float = 1.04,
    k_roughness: SiValue = SiValue(6.34e-6, "m"),
    laminar_fraction: float = 0.0,
) -> SiValue:
    """Calculates tailplane parasite drag area [Strohmayer - Flugzeugentwurf 2 | p. 88] [m^2].

    Args:
        velocity: True airspeed (TAS) [m/s].
        altitude: Flight altitude [m].
        area: Tailplane reference area S_HTP or S_VTP [m^2].
        aspect_ratio: Tailplane aspect ratio [-].
        rel_thickness: Relative airfoil thickness t/c [-]. Defaults to 0.12.
        sweep_deg: Sweep angle at maximum thickness / half-chord line [deg]. Defaults to 0.0.
        x_d_over_l: Chordwise location of maximum thickness (x/c)_tmax [-]. Defaults to 0.30.
        interference_factor: Tailplane interference factor IF_tail [-]. Defaults to 1.04.
        k_roughness: Equivalent sand grain surface roughness [m]. Defaults to 6.34e-6 m.
        laminar_fraction: Laminar boundary layer fraction [0..1]. Defaults to 0.0.

    Returns:
        Tailplane parasite drag area [m^2].
    """
    mean_chord = SiValue(math.sqrt(area / aspect_ratio), "m")
    c_w0_tail = calc_wing_zero_lift_drag_coefficient(
        velocity=velocity,
        altitude=altitude,
        mean_aerodynamic_chord=mean_chord,
        rel_thickness=rel_thickness,
        sweep_deg=sweep_deg,
        x_d_over_l=x_d_over_l,
        interference_factor=interference_factor,
        k_roughness=k_roughness,
        laminar_fraction=laminar_fraction,
    )
    return SiValue(c_w0_tail * area, "m^2")
