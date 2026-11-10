"""Aerodynamic friction coefficients, roughness cutoffs, form factors, and parasite drag buildup."""

import math
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import isa_density, isa_dynamic_viscosity, isa_speed_of_sound
from data import SiValue


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


def calc_cf_flat_plate_laminar(re: float) -> float:
    """Calculates laminar skin friction coefficient for flat plates / lifting surfaces [Strohmayer - Flugzeugentwurf 2 | p. 83].

    Args:
        re: Reynolds number Re [-].

    Returns:
        Laminar skin friction coefficient c_f,lam [-].
    """
    if re <= 0:
        raise ValueError(f"Reynolds number must be positive (got {re})")
    return 1.328 / math.sqrt(re)


def calc_cf_flat_plate_turbulent(re: float, mach: float = 0.0) -> float:
    """Calculates turbulent skin friction coefficient for flat plates / lifting surfaces.

    Uses the Prandtl-Schlichting formula with compressibility correction for Ma > 0.3 [Strohmayer - Flugzeugentwurf 2 | p. 83].

    Args:
        re: Reynolds number Re [-].
        mach: Mach number Ma [-]. Defaults to 0.0.

    Returns:
        Turbulent skin friction coefficient c_f,turb [-].
    """
    if re <= 0:
        raise ValueError(f"Reynolds number must be positive (got {re})")

    base = 0.455 / (math.log10(re) ** 2.58)
    if mach > 0.3:
        compressibility = (1.0 + 0.144 * (mach**2)) ** 0.65
        return base / compressibility
    return base


def calc_delta_cf_body_laminar(re: float, l_over_d: float) -> float:
    """Calculates additional 3D laminar skin friction increment for slender bodies [Strohmayer - Flugzeugentwurf 2 | p. 83].

    Args:
        re: Reynolds number Re [-].
        l_over_d: Fineness ratio l/d (length over diameter) [-].

    Returns:
        Additional 3D laminar friction increment Delta c_f,lam [-].
    """
    if re <= 0:
        raise ValueError(f"Reynolds number must be positive (got {re})")
    return (2.0 / re) * l_over_d


def calc_delta_cf_body_turbulent(re: float, l_over_d: float) -> float:
    """Calculates additional 3D turbulent skin friction increment for slender bodies [Strohmayer - Flugzeugentwurf 2 | p. 83].

    Args:
        re: Reynolds number Re [-].
        l_over_d: Fineness ratio l/d (length over diameter) [-].

    Returns:
        Additional 3D turbulent friction increment Delta c_f,turb [-].
    """
    if re <= 0:
        raise ValueError(f"Reynolds number must be positive (got {re})")
    return (0.0016 / (re**0.4)) * l_over_d


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


@dataclass(frozen=True)
class AerodynamicComponent:
    """Component for zero-lift drag (c_W0) buildup [Strohmayer - Flugzeugentwurf 2 | p. 88]."""

    name: str
    c_f: float
    form_factor: float
    interference_factor: float
    wetted_area: SiValue

    @property
    def drag_area(self) -> SiValue:
        """Returns component drag area [m^2]."""
        return calc_component_drag_area(
            self.c_f, self.form_factor, self.interference_factor, self.wetted_area
        )


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


def calc_zero_lift_drag_coefficient(
    components: list[AerodynamicComponent] | list[float],
    s_ref: SiValue,
    c_w_misc: float = 0.0,
) -> float:
    """Calculates total zero-lift drag coefficient c_W0 via component buildup method [Strohmayer - Flugzeugentwurf 2 | p. ?] [-].

    Args:
        components: List of AerodynamicComponent instances or precalculated component drag areas [m^2].
        s_ref: Wing reference area S_ref [m^2].
        c_w_misc: Miscellaneous drag increment c_w_misc [-]. Defaults to 0.0.

    Returns:
        Zero-lift drag coefficient c_W0 [-].
    """
    total_drag_area = sum(
        comp.drag_area if isinstance(comp, AerodynamicComponent) else comp
        for comp in components
    )
    return (total_drag_area / s_ref) + c_w_misc


if __name__ == "__main__":
    from data import load_reference_aircraft_data
    from formulas.geometry import calc_mean_aerodynamic_chord

    ref = load_reference_aircraft_data()

    s_ref_ex = ref.dimensions.wingArea.si
    l_ex = calc_mean_aerodynamic_chord(
        ref.dimensions.wingArea.si, ref.dimensions.wingspan.si
    )
    d_fus = (ref.dimensions.fuselageWidth.si + ref.dimensions.fuselageHeight.si) / 2.0
    l_d_fus = ref.dimensions.fuselageLength.si / d_fus
    t_over_c = ref.assumptions.wingRootThickness.si / l_ex
    sweep_deg = ref.assumptions.wingSweepHalfChord

    v_cruise = ref.mission.cruiseSpeedTAS.si
    h_cruise = ref.mission.cruiseAltitude.si
    mach_ex = calc_mach_number(v_cruise, h_cruise)
    re_ex = calc_reynolds_number(v_cruise, l_ex, h_cruise)

    k_ex = SiValue(6.34e-6, "m")  # smooth paint roughness

    print("--- SKIN FRICTION COEFFICIENTS (LIFTING SURFACES) ---")
    cf_lam = calc_cf_flat_plate_laminar(re_ex)
    cf_turb = calc_cf_flat_plate_turbulent(re_ex, mach_ex)
    print(f"c_f,lam (Re={re_ex:.1e}):          {cf_lam:.6f}")
    print(f"c_f,turb (Re={re_ex:.1e}, M={mach_ex:.2f}): {cf_turb:.6f}")

    print("\n--- 3D BODY INCREMENT ---")
    d_cf_lam = calc_delta_cf_body_laminar(re_ex, l_d_fus)
    d_cf_turb = calc_delta_cf_body_turbulent(re_ex, l_d_fus)
    print(f"Delta c_f,lam (l/d={l_d_fus:.2f}):    {d_cf_lam:.8f}")
    print(f"Delta c_f,turb (l/d={l_d_fus:.2f}):   {d_cf_turb:.6f}")

    print("\n--- SURFACE ROUGHNESS (CUTOFF REYNOLDS NUMBER) ---")
    re_eff = calc_effective_reynolds_number(re_ex, l_ex, k_ex, mach_ex)
    cf_turb_eff = calc_cf_flat_plate_turbulent(re_eff, mach_ex)
    print(f"Re_eff:                          {re_eff:.2e}")
    print(f"c_f,turb (with cutoff):          {cf_turb_eff:.6f}")

    print("\n--- FORM FACTORS (RAYMER / NIKOLAI) ---")
    ff_flaeche = calc_form_factor_wing(
        d_over_l=t_over_c, x_d_over_l=0.35, mach=mach_ex, sweep_d_max_deg=sweep_deg
    )
    ff_rumpf = calc_form_factor_fuselage(l_over_d=l_d_fus)
    print(f"FF_Wing (t/c={t_over_c:.2f}, M={mach_ex:.2f}):     {ff_flaeche:.4f}")
    print(f"FF_Fuselage (l/d={l_d_fus:.2f}):            {ff_rumpf:.4f}")

    print("\n--- ZERO-LIFT DRAG BUILDUP (c_W0) ---")
    components_ex = [
        AerodynamicComponent(
            "Wing",
            cf_turb_eff,
            ff_flaeche,
            1.0,  # High/mid wing with fairing
            SiValue(2.0 * ref.dimensions.wingArea.si, "m^2"),
        ),
        AerodynamicComponent(
            "Fuselage",
            cf_turb_eff + d_cf_turb,
            ff_rumpf,
            1.0,
            ref.assumptions.wettedSurface.si,
        ),
        AerodynamicComponent(
            "HorizontalTail",
            cf_turb_eff,
            1.25,
            1.04,
            SiValue(2.0 * ref.dimensions.horizontalTailArea.si, "m^2"),
        ),
        AerodynamicComponent(
            "VerticalTail",
            cf_turb_eff,
            1.25,
            1.04,
            SiValue(2.0 * ref.dimensions.verticalTailArea.si, "m^2"),
        ),
    ]
    for comp in components_ex:
        cw0_comp = calc_zero_lift_drag_coefficient([comp], s_ref=s_ref_ex)
        label = f"c_W0 ({comp.name}):"
        print(f"{label:<26} {cw0_comp:.5f}")
    cw0 = calc_zero_lift_drag_coefficient(components_ex, s_ref=s_ref_ex)
    total_label = "c_W0 (Total):"
    print(f"{total_label:<26} {cw0:.5f}")
