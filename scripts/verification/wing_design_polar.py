"""Verification script for WingDesign geometry and drag polar scaling against ReferenceAircraft."""

import math
import sys
from dataclasses import replace
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from aerodynamics import AerodynamicDesign
from aircraft import BatteryAircraft
from data import UnitValue, load_constraints, load_design_parameters
from empennage_sizing import EmpennageDesign
from fuselage_sizing import FuselageDesign
from reference_aircraft import load_reference_aircraft
from wing import WingDesign


def verify_wing_design_polar() -> None:
    """Verifies exact reference identity of WingDesign and prints step-by-step parameter influence."""
    constraints = load_constraints()
    design = load_design_parameters()
    ref = load_reference_aircraft()

    # 1. Exact identity check with ReferenceAircraft parameters
    ref_wing_loading = ref.data.fuel.referenceMass.si / ref.data.dimensions.wingArea.si
    constraints_as_ref = replace(
        constraints,
        performance=replace(
            constraints.performance,
            wingSpanMax=ref.data.dimensions.wingspan,
        ),
    )
    design_as_ref = replace(
        design,
        aerodynamics=replace(
            design.aerodynamics,
            oswaldFactor=ref.data.assumptions.oswaldFactor,
            liftToDragRatioCruise=None,
        ),
        wing=replace(
            design.wing,
            aspectRatio=UnitValue(ref.aspect_ratio, ""),
            relWingThickness=ref.data.assumptions.relWingThickness,
            wingSweepHalfChord=ref.data.assumptions.wingSweepHalfChord,
            wingMassPenaltyFactor=ref.data.assumptions.wingMassPenaltyFactor,
            bendingReliefFactor=UnitValue(0.0, ""),
        ),
        mission=replace(
            design.mission,
            cruiseSpeedTAS=ref.data.mission.cruiseSpeedTAS,
            cruiseAltitude=ref.data.mission.cruiseAltitude,
        ),
        assumptions=replace(
            design.assumptions,
            limitLoad=ref.data.assumptions.limitLoad,
        ),
    )

    wing_ref_check = WingDesign(
        constraints=constraints_as_ref,
        design=design_as_ref,
        ref=ref,
        mtom=ref.data.fuel.referenceMass.si,
        wing_loading_design=ref_wing_loading,
    )
    fuse_ref_check = FuselageDesign(constraints_as_ref, design_as_ref, ref)
    emp_ref_check = EmpennageDesign(design_as_ref, ref, wing_ref_check)
    aero_ref_check = AerodynamicDesign(
        design_as_ref, ref, wing_ref_check, fuse_ref_check, emp_ref_check
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
    wing_checks = [
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
            "Cruise Lift Coeff C_L [-]",
            ref.cruise_lift_coefficient,
            aero_ref_check.cruise_lift_coefficient,
        ),
        (
            "Induced Drag Coeff c_Wi [-]",
            ref.induced_drag_coefficient,
            aero_ref_check.induced_drag_coefficient,
        ),
    ]
    for label, v_ref, v_wd in wing_checks:
        diff = v_wd - v_ref
        print(f"{label:<35} | {v_ref:18.6f} | {v_wd:18.6f} | {diff:+12.2e}")
        assert math.isclose(v_ref, v_wd, rel_tol=1e-12, abs_tol=1e-12)

    aero_checks = [
        (
            "Total Zero-Lift Drag c_W0 [-]",
            ref.zero_lift_drag_coefficient,
            aero_ref_check.zero_lift_drag_coefficient,
        ),
        (
            "Total Cruise Drag Coeff C_D [-]",
            ref_cd,
            aero_ref_check.cruise_drag_coefficient,
        ),
        ("Cruise L/D [-]", ref_ld, aero_ref_check.lift_to_drag_cruise),
    ]
    for label, v_ref, v_wd in aero_checks:
        diff = v_wd - v_ref
        print(f"{label:<35} | {v_ref:18.6f} | {v_wd:18.6f} | {diff:+12.2e}")
        assert math.isclose(v_ref, v_wd, rel_tol=0.02, abs_tol=1e-4)

    # 2. Step-by-step transition from Reference Aircraft to converged Electric Aircraft
    ac = BatteryAircraft(constraints, design, ref)
    ac.converge_mtom()

    step0 = aero_ref_check
    step1_design = replace(design_as_ref, mission=design.mission)
    step1_wing = WingDesign(
        constraints_as_ref,
        step1_design,
        ref,
        ref.data.fuel.referenceMass.si,
        ref_wing_loading,
    )
    step1 = AerodynamicDesign(
        step1_design,
        ref,
        step1_wing,
        FuselageDesign(constraints_as_ref, step1_design, ref),
        EmpennageDesign(step1_design, ref, step1_wing),
    )

    step2_design = replace(
        step1_design,
        aerodynamics=replace(
            step1_design.aerodynamics,
            oswaldFactor=design.aerodynamics.oswaldFactor,
        ),
        wing=replace(
            step1_design.wing,
            aspectRatio=design.wing.aspectRatio,
        ),
    )
    step2_wing = WingDesign(
        constraints, step2_design, ref, ref.data.fuel.referenceMass.si, ref_wing_loading
    )
    step2 = AerodynamicDesign(
        step2_design,
        ref,
        step2_wing,
        FuselageDesign(constraints, step2_design, ref),
        EmpennageDesign(step2_design, ref, step2_wing),
    )

    step3 = ac.aerodynamics

    steps = [
        ("0. Do 228 Reference (200 kts)", step0),
        ("1. + Cruise Speed (184.4 kts)", step1),
        ("2. + AR (10.5) & Oswald (0.85)", step2),
        (f"3. + Wing Area ({step3.wing.area:.2f})", step3),
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
    for name, a in steps:
        print(
            f"{name:<30} | {a.wing.area.value:8.2f} | {a.wing.aspect_ratio:6.2f} | "
            f"{a.cruise_lift_coefficient:6.4f} | {a.wing.wing_zero_lift_drag_coefficient:7.5f} | "
            f"{a.zero_lift_drag_coefficient:7.5f} | {a.induced_drag_coefficient:7.5f} | "
            f"{a.cruise_drag_coefficient:7.5f} | {a.lift_to_drag_cruise:6.2f}"
        )
    print("=" * 98)


if __name__ == "__main__":
    verify_wing_design_polar()
