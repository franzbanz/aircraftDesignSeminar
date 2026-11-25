"""Root bending moment relief and wing mass correction factor for wing-mounted batteries."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from aircraft import BatteryAircraft
from constants import GRAVITY
from data import SiValue, load_constraints, load_design_parameters
from formulas.mass import calc_wing_mass
from reference_aircraft import load_reference_aircraft


@dataclass(frozen=True)
class WingBendingAnalysisResult:
    """Results of a wing root bending moment and mass relief evaluation."""

    case_name: str
    battery_wing_fraction: float
    m_bat_wing: SiValue
    eta_in: float
    eta_out: float
    eta_cg: float
    y_bat_cg: SiValue
    lever_ratio_kappa_bat: float
    lever_ratio_kappa_eng: float
    m_b_flight: SiValue
    m_b_ground: SiValue
    governing_case: str
    mzfm_eff: SiValue
    delta_m_f_eff: float
    m_wing_calibrated: SiValue
    mass_saving_vs_baseline: SiValue


def calc_wing_box_battery_volume(
    wingspan: SiValue,
    fuselage_width: SiValue,
    chord: SiValue,
    root_thickness: SiValue,
    eta_in: float,
    eta_out: float,
    spar_chord_fraction: float = 0.45,
    height_efficiency: float = 0.80,
) -> SiValue:
    """Calculates available internal wing box volume between span stations eta_in and eta_out [m^3].

    Args:
        wingspan: Total wingspan b_W [m].
        fuselage_width: Fuselage width b_R [m].
        chord: Mean aerodynamic chord c_mu [m].
        root_thickness: Wing thickness t_root [m].
        eta_in: Inner dimensionless half-span station y_in / (b/2) [-].
        eta_out: Outer dimensionless half-span station y_out / (b/2) [-].
        spar_chord_fraction: Usable chord fraction between front and rear spar [-]. Defaults to 0.45.
        height_efficiency: Usable height fraction of maximum airfoil thickness [-]. Defaults to 0.80.

    Returns:
        Total available wing box volume across both wing halves [m^3].
    """
    half_span = wingspan / 2.0
    y_root = fuselage_width / 2.0
    y_in = max(y_root, eta_in * half_span)
    y_out = eta_out * half_span
    span_length_per_side = max(0.0, y_out - y_in)

    box_cross_section = spar_chord_fraction * chord * height_efficiency * root_thickness
    return SiValue(2.0 * box_cross_section * span_length_per_side, "m^3")


def calc_ref_wing_calibration_with_physical_engine_relief(
    aircraft: BatteryAircraft,
    eta_aero: float = 0.4244,
    eta_engine: float = 0.30,
    delta_m_f_gear_only: float = -0.05,
) -> tuple[float, SiValue, float]:
    """Calculates the reference aircraft wing calibration factor using physical engine bending relief.

    Replaces Torenbeek's empirical -5% engine relief factor with the actual lever-arm-weighted
    mass relief of the reference engines + pylons on MZFM, keeping only -5% for non-wing landing gear.

    Returns:
        Tuple of (calibration_factor [-], ref_mzfm_eff [kg], ref_lever_ratio_kappa_eng [-]).
    """
    ref = aircraft.ref
    half_span_ref = ref.data.dimensions.wingspan.si / 2.0
    y_root_ref = ref.data.dimensions.fuselageWidth.si / 2.0

    r_aero_ref = max(0.0, eta_aero * half_span_ref - y_root_ref)
    r_eng_ref = max(0.0, eta_engine * half_span_ref - y_root_ref)
    kappa_eng_ref = r_eng_ref / r_aero_ref if r_aero_ref > 0 else 0.0

    m_nacelle_ref = ref.data.mass.engine.si + ref.data.mass.pylons.si
    mzfm_eff_ref = SiValue(
        ref.data.mass.zeroFuelMassMax.si - kappa_eng_ref * m_nacelle_ref,
        "kg",
    )

    raw_ref_wing = calc_wing_mass(
        mzfm=mzfm_eff_ref,
        b_s=ref.structural_wingspan,
        n_ult=ref.ultimate_load_factor,
        d_root=ref.wing_root_thickness,
        s_w=ref.data.dimensions.wingArea.si,
        delta_m_F=delta_m_f_gear_only,
    )
    cal_factor = ref.data.mass.wing.si / raw_ref_wing
    return cal_factor, mzfm_eff_ref, kappa_eng_ref


def calc_wing_bending_relief(
    aircraft: BatteryAircraft,
    battery_wing_fraction: float,
    eta_in: float,
    eta_out: float,
    physical_engine_relief: bool = True,
    eta_aero: float = 0.4244,
    eta_engine: float = 0.30,
    n_ult_ground: float = 3.0,
    delta_m_f_gear_only: float = -0.05,
) -> WingBendingAnalysisResult:
    """Calculates root bending moments, effective MZFM, and corrected wing mass.

    Supports both Torenbeek's empirical -5% engine rule (physical_engine_relief=False)
    and exact lever-arm-weighted engine + pylon bending relief (physical_engine_relief=True).

    Args:
        aircraft: Converged BatteryAircraft instance.
        battery_wing_fraction: Share of total battery mass placed in the wing m_bat,wing / m_bat [-].
        eta_in: Inner dimensionless half-span station of battery pack [-].
        eta_out: Outer dimensionless half-span station of battery pack [-].
        physical_engine_relief: If True, calculates engine + pylon relief physically via lever arm
            and recalibrates against the reference aircraft. If False, uses the empirical -5%
            engine relief included in wingMassPenaltyFactor (-10%). Defaults to True.
        eta_aero: Dimensionless half-span station of aerodynamic lift center of pressure [-].
            Defaults to 4 / (3 * pi) = 0.4244 (elliptical lift distribution).
        eta_engine: Dimensionless half-span station of wing-mounted engine [-]. Defaults to 0.30.
        n_ult_ground: Ultimate downward inertia load factor for hard landing / ground bump [-].
            Defaults to 3.0 (1.5 * 2.0g landing gear shock factor).
        delta_m_f_gear_only: Structural relief factor for non-wing-mounted landing gear [-].
            Defaults to -0.05 (-5%).

    Returns:
        WingBendingAnalysisResult with bending moments, effective correction factors, and wing mass.
    """
    half_span = aircraft.wing.span / 2.0
    y_root = aircraft.fuselage.width / 2.0

    y_in = max(y_root, eta_in * half_span)
    y_out = max(y_in, eta_out * half_span)
    y_bat_cg = SiValue(0.5 * (y_in + y_out), "m")
    eta_cg = y_bat_cg / half_span

    y_aero = SiValue(eta_aero * half_span, "m")
    y_eng = SiValue(eta_engine * half_span, "m")
    y_wing_cg = SiValue(0.38 * half_span, "m")

    # Lever arms relative to wing-fuselage root attachment y_root
    r_aero = max(0.0, y_aero - y_root)
    r_bat = max(0.0, y_bat_cg - y_root)
    r_eng = max(0.0, y_eng - y_root)
    r_wing = max(0.0, y_wing_cg - y_root)

    lever_ratio_kappa_bat = r_bat / r_aero if r_aero > 0 else 0.0
    lever_ratio_kappa_eng = r_eng / r_aero if r_aero > 0 else 0.0

    m_bat_wing = SiValue(battery_wing_fraction * aircraft.mass.battery, "kg")
    m_nacelle = SiValue(aircraft.mass.engine + aircraft.mass.pylons, "kg")
    n_ult_flight = aircraft.design.assumptions.limitLoad * 1.5

    # Root bending moment of one wing half in flight (+n_ult pull-up maneuver)
    m_b_flight_val = (
        n_ult_flight
        * GRAVITY
        * (
            0.5 * aircraft.mtom * r_aero
            - 0.5 * m_nacelle * r_eng
            - 0.5 * m_bat_wing * r_bat
            - 0.5 * aircraft.wing.mass * r_wing
        )
    )
    m_b_flight = SiValue(max(0.0, m_b_flight_val), "N*m")

    # Root bending moment on ground / hard landing (no lift, downward inertia -n_ult_ground)
    m_b_ground_val = (
        n_ult_ground
        * GRAVITY
        * (
            0.5 * m_nacelle * r_eng
            + 0.5 * m_bat_wing * r_bat
            + 0.5 * aircraft.wing.mass * r_wing
        )
    )
    m_b_ground = SiValue(m_b_ground_val, "N*m")

    governing_case = "Flight (+4.5g)" if m_b_flight >= m_b_ground else "Ground (-3.0g)"

    delta_m_f_base = aircraft.design.wing.wingMassPenaltyFactor

    if physical_engine_relief:
        mzfm_flight_eff = (
            aircraft.mtom
            - lever_ratio_kappa_eng * m_nacelle
            - lever_ratio_kappa_bat * m_bat_wing
        )
        delta_m_f_used = delta_m_f_gear_only
        cal_factor, _, _ = calc_ref_wing_calibration_with_physical_engine_relief(
            aircraft, eta_aero, eta_engine, delta_m_f_gear_only
        )
    else:
        mzfm_flight_eff = aircraft.mtom - lever_ratio_kappa_bat * m_bat_wing
        delta_m_f_used = delta_m_f_base
        cal_factor = aircraft.ref.wing_calibration_factor

    if m_b_ground > m_b_flight and m_b_flight > 0:
        mzfm_eff_val = mzfm_flight_eff * (m_b_ground / m_b_flight)
    else:
        mzfm_eff_val = mzfm_flight_eff
    mzfm_eff = SiValue(mzfm_eff_val, "kg")

    raw_wing_mass = calc_wing_mass(
        mzfm=mzfm_eff,
        b_s=aircraft.wing.span,
        n_ult=n_ult_flight,
        d_root=aircraft.wing.root_thickness,
        s_w=aircraft.wing.area,
        delta_m_F=delta_m_f_used,
    )
    m_wing_calibrated = SiValue(raw_wing_mass * cal_factor, "kg")

    # Equivalent total penalty factor delta_m_F_eff if standard calc_wing_mass(mzfm=MTOM) is used
    mass_ratio = m_wing_calibrated / aircraft.wing.mass
    delta_m_f_eff = (1.0 + delta_m_f_base) * mass_ratio - 1.0

    mass_saving_vs_baseline = SiValue(aircraft.wing.mass - m_wing_calibrated, "kg")
    case_name = (
        f"{battery_wing_fraction * 100:3.0f}% Wing Bat "
        f"(eta={eta_in:.2f}..{eta_out:.2f})"
    )

    return WingBendingAnalysisResult(
        case_name=case_name,
        battery_wing_fraction=battery_wing_fraction,
        m_bat_wing=m_bat_wing,
        eta_in=eta_in,
        eta_out=eta_out,
        eta_cg=eta_cg,
        y_bat_cg=y_bat_cg,
        lever_ratio_kappa_bat=lever_ratio_kappa_bat,
        lever_ratio_kappa_eng=lever_ratio_kappa_eng,
        m_b_flight=m_b_flight,
        m_b_ground=m_b_ground,
        governing_case=governing_case,
        mzfm_eff=mzfm_eff,
        delta_m_f_eff=delta_m_f_eff,
        m_wing_calibrated=m_wing_calibrated,
        mass_saving_vs_baseline=mass_saving_vs_baseline,
    )


def print_wing_bending_study(
    aircraft: BatteryAircraft,
    physical_engine_relief: bool | None = None,
) -> None:
    """Prints wing box volume, root bending moments, and wing mass correction factors.

    Args:
        aircraft: Converged BatteryAircraft instance.
        physical_engine_relief: Selects engine relief mode:
            - False: Empirical -5% Torenbeek engine rule
            - True: Exact physical engine + pylon bending relief
            - None: Prints both modes for direct comparison (default).
    """
    b_w = aircraft.wing.span
    c_mu = aircraft.wing.mean_aerodynamic_chord
    t_root = aircraft.wing.root_thickness
    b_r = aircraft.fuselage.width
    eta_root = b_r / b_w

    vol_inner = calc_wing_box_battery_volume(b_w, b_r, c_mu, t_root, eta_root, 0.35)
    vol_mid = calc_wing_box_battery_volume(b_w, b_r, c_mu, t_root, eta_root, 0.65)
    vol_full = calc_wing_box_battery_volume(b_w, b_r, c_mu, t_root, eta_root, 0.85)

    cal_phys, mzfm_eff_ref, kappa_eng_ref = (
        calc_ref_wing_calibration_with_physical_engine_relief(aircraft)
    )
    m_nacelle_ref = SiValue(
        aircraft.ref.data.mass.engine.si + aircraft.ref.data.mass.pylons.si, "kg"
    )
    m_nacelle_el = SiValue(aircraft.mass.engine + aircraft.mass.pylons, "kg")

    print("WING ROOT BENDING MOMENT & ENGINE + BATTERY RELIEF STUDY")
    print(
        f"Reference Do 228:  MZFM = {aircraft.ref.data.mass.zeroFuelMassMax:.1f}, "
        f"m_eng+pyl = {m_nacelle_ref:.1f} (kappa_eng = {kappa_eng_ref:.2f}) "
        f"-> MZFM_eff = {mzfm_eff_ref:.1f}, k_cal,phys = {cal_phys:.4f} (vs. k_cal,emp = {aircraft.ref.wing_calibration_factor:.4f})"
    )
    print(
        f"Electric Aircraft: MTOM = {aircraft.mtom:.1f}, m_eng+pyl = {m_nacelle_el:.1f}, "
        f"m_bat = {aircraft.mass.battery:.1f}, Baseline Wing Mass (-10% rule): {aircraft.wing.mass:.1f}"
    )
    print(f"Wing Geometry:     b = {b_w:.2f}, c_mu = {c_mu:.2f}, t_root = {t_root:.3f}")
    print(
        f"Wing Box Volume:   Inner (eta<=0.35): {vol_inner:.2f} | "
        f"Mid (eta<=0.65): {vol_mid:.2f} | Full (eta<=0.85): {vol_full:.2f}"
    )

    scenarios = [
        # (battery_wing_fraction, eta_in, eta_out)
        (0.00, eta_root, eta_root),
        (0.25, eta_root, 0.35),
        (0.50, eta_root, 0.45),
        (0.50, eta_root, 0.65),
        (0.75, eta_root, 0.65),
        (1.00, eta_root, 0.65),
        (1.00, eta_root, 0.85),
        (1.00, 0.40, 0.90),
    ]

    modes = (
        [False, True] if physical_engine_relief is None else [physical_engine_relief]
    )

    for mode in modes:
        mode_title = (
            "MODE B: EXACT PHYSICAL ENGINE + PYLON RELIEF (MZFM_eff includes engine + battery)"
            if mode
            else "MODE A: EMPIRICAL TORENBEEK ENGINE RELIEF (-5% fixed for engines, MZFM_eff only battery)"
        )
        print(f"\n--- {mode_title} ---")

        results = [
            calc_wing_bending_relief(
                aircraft, frac, e_in, e_out, physical_engine_relief=mode
            )
            for frac, e_in, e_out in scenarios
        ]

        header = (
            f"{'Scenario':<28} | {'m_bat,w':>10} | {'y_bat':>8} | {'k_bat':>5} | "
            f"{'M_B,flight':>12} | {'M_B,ground':>12} | {'Governing':<14} | "
            f"{'MZFM_eff':>10} | {'dm_F,eff':>8} | {'m_wing':>10} | {'vs. -10%':>10}"
        )
        print(header)
        print("-" * len(header))

        for r in results:
            delta_mass = SiValue(-r.mass_saving_vs_baseline, "kg")
            print(
                f"{r.case_name:<28} | "
                f"{r.m_bat_wing:>10.1f} | "
                f"{r.y_bat_cg:>8.2f} | "
                f"{r.lever_ratio_kappa_bat:5.2f} | "
                f"{r.m_b_flight.to('kN*m'):>12.1f} | "
                f"{r.m_b_ground.to('kN*m'):>12.1f} | "
                f"{r.governing_case:<14} | "
                f"{r.mzfm_eff:>10.1f} | "
                f"{r.delta_m_f_eff * 100:+7.1f}% | "
                f"{r.m_wing_calibrated:>10.1f} | "
                f"{delta_mass:>+10.1f}"
            )


if __name__ == "__main__":
    constraints_data = load_constraints()
    design_data = load_design_parameters()
    ref_ac = load_reference_aircraft()

    el_aircraft = BatteryAircraft(constraints_data, design_data, ref_ac)
    el_aircraft.converge_mtom()
    print_wing_bending_study(el_aircraft)
