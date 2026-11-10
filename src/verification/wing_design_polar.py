"""Verification script for WingDesign geometry and drag polar scaling against ReferenceAircraft."""

import math
import sys
from dataclasses import replace
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aircraft import BatteryAircraft
from data import UnitValue, load_constraints, load_design_parameters
from reference_aircraft import load_reference_aircraft
from wing_design import WingDesign


def verify_wing_design_polar() -> None:
    """Verifies exact reference identity of WingDesign and prints step-by-step parameter influence."""
    constraints = load_constraints()
    design = load_design_parameters()
    ref = load_reference_aircraft()

    # 1. Exact identity check with ReferenceAircraft parameters
    ref_wing_loading = ref.data.fuel.referenceMass.si / ref.data.dimensions.wingArea.si
    design_as_ref = replace(
        design,
        aerodynamics=replace(
            design.aerodynamics,
            aspectRatio=UnitValue(ref.aspect_ratio, ""),
            oswaldFactor=ref.data.assumptions.oswaldFactor,
            relWingThickness=ref.data.assumptions.relWingThickness,
            maxWingSpan=ref.data.dimensions.wingspan,
        ),
        mission=replace(
            design.mission,
            cruiseSpeedTAS=ref.data.mission.cruiseSpeedTAS,
            cruiseAltitude=ref.data.mission.cruiseAltitude,
        ),
        assumptions=replace(
            design.assumptions,
            limitLoad=ref.data.assumptions.limitLoad,
            wingSweepHalfChord=ref.data.assumptions.wingSweepHalfChord,
            wingMassPenaltyFactor=ref.data.assumptions.wingMassPenaltyFactor,
        ),
    )

    wing_ref_check = WingDesign(
        constraints=constraints,
        design=design_as_ref,
        ref=ref,
        mtom=ref.data.fuel.referenceMass.si,
        wing_loading_design=ref_wing_loading,
    )

    ref_cd = ref.drag_coefficient_from_polar(ref.cruise_lift_coefficient)
    ref_ld = ref.lift_to_drag_from_polar(ref.cruise_lift_coefficient)

    print("=" * 98)
    print(
        "            1. IDENTITY CHECK: WingDesign WITH DORNIER 228 REFERENCE PARAMETERS"
    )
    print("=" * 98)
    print(
        f"{'Parameter':<35} | {'ReferenceAircraft':>18} | {'WingDesign':>18} | {'Diff':>12}"
    )
    print("-" * 98)
    checks = [
        ("Wing Area S_W [m^2]", ref.data.dimensions.wingArea.si, wing_ref_check.area),
        ("Wingspan b_W [m]", ref.data.dimensions.wingspan.si, wing_ref_check.span),
        ("Aspect Ratio AR [-]", ref.aspect_ratio, wing_ref_check.aspect_ratio),
        (
            "Mean Aerodynamic Chord c_mu [m]",
            ref.mean_aerodynamic_chord,
            wing_ref_check.mean_aerodynamic_chord,
        ),
        (
            "Wing Root Thickness t_root [m]",
            ref.wing_root_thickness,
            wing_ref_check.root_thickness,
        ),
        (
            "Wing Zero-Lift Drag c_W0,wing [-]",
            ref.wing_zero_lift_drag_coefficient,
            wing_ref_check.wing_zero_lift_drag_coefficient,
        ),
        (
            "Total Zero-Lift Drag c_W0 [-]",
            ref.zero_lift_drag_coefficient,
            wing_ref_check.zero_lift_drag_coefficient,
        ),
        (
            "Cruise Lift Coeff C_L [-]",
            ref.cruise_lift_coefficient,
            wing_ref_check.cruise_lift_coefficient,
        ),
        (
            "Induced Drag Coeff c_Wi [-]",
            ref.induced_drag_coefficient,
            wing_ref_check.induced_drag_coefficient,
        ),
        (
            "Total Cruise Drag Coeff C_D [-]",
            ref_cd,
            wing_ref_check.cruise_drag_coefficient,
        ),
        ("Cruise L/D [-]", ref_ld, wing_ref_check.lift_to_drag_cruise),
    ]
    for label, v_ref, v_wd in checks:
        diff = v_wd - v_ref
        print(f"{label:<35} | {v_ref:18.6f} | {v_wd:18.6f} | {diff:+12.2e}")
        assert math.isclose(v_ref, v_wd, rel_tol=1e-12, abs_tol=1e-12)

    # 2. Step-by-step transition from Reference Aircraft to converged Electric Aircraft
    ac = BatteryAircraft(constraints, design, ref)
    ac.converge_mtom()

    step0 = wing_ref_check
    step1_design = replace(design_as_ref, mission=design.mission)
    step1 = WingDesign(
        constraints, step1_design, ref, ref.data.fuel.referenceMass.si, ref_wing_loading
    )

    step2_design = replace(
        step1_design,
        aerodynamics=replace(
            step1_design.aerodynamics,
            aspectRatio=design.aerodynamics.aspectRatio,
            oswaldFactor=design.aerodynamics.oswaldFactor,
            maxWingSpan=design.aerodynamics.maxWingSpan,
        ),
    )
    step2 = WingDesign(
        constraints, step2_design, ref, ref.data.fuel.referenceMass.si, ref_wing_loading
    )

    step3 = ac.wing

    steps = [
        ("0. Do 228 Reference (200 kts)", step0),
        ("1. + Cruise Speed (184.4 kts)", step1),
        ("2. + AR (10.5) & Oswald (0.85)", step2),
        (f"3. + Wing Area ({step3.area:.2f})", step3),
    ]

    print("\n" + "=" * 98)
    print(
        "            2. STEP-BY-STEP TRANSITION FROM DO 228 TO ELECTRIC AIRCRAFT WING"
    )
    print("=" * 98)
    print(
        f"{'Step':<30} | {'S_W [m²]':>8} | {'AR [-]':>6} | {'C_L':>6} | "
        f"{'c_W0,w':>7} | {'c_W0':>7} | {'c_Wi':>7} | {'C_D':>7} | {'L/D':>6}"
    )
    print("-" * 98)
    for name, w in steps:
        print(
            f"{name:<30} | {w.area.value:8.2f} | {w.aspect_ratio:6.2f} | "
            f"{w.cruise_lift_coefficient:6.4f} | {w.wing_zero_lift_drag_coefficient:7.5f} | "
            f"{w.zero_lift_drag_coefficient:7.5f} | {w.induced_drag_coefficient:7.5f} | "
            f"{w.cruise_drag_coefficient:7.5f} | {w.lift_to_drag_cruise:6.2f}"
        )
    print("=" * 98)


if __name__ == "__main__":
    verify_wing_design_polar()
