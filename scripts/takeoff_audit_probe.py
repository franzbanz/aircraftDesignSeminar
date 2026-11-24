"""Audit shared sizing inputs and verification outputs; no S_AS or V1 solver.

Run from any working directory:
    python <project>/scripts/takeoff_audit_probe.py

Print JSON to stdout by default. Save a snapshot only when --output is supplied.
The default audit compares the current and baseline design configurations.
Importing this module does not run an audit or write files.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from cl_max import project_imports

with project_imports():
    from aircraft import BatteryAircraft
    from data import SiValue, loader
    from formulas.propulsion import calc_thrust_loading_from_power
    from reference_aircraft import load_reference_aircraft
    from sizing_diagram import calc_takeoff_safety_speed


def snapshot(design_name, constraints_path=None, reference_path=None):
    """Read one converged aircraft state using explicit project input paths."""
    design_path = Path(design_name)
    if not design_path.is_absolute():
        design_path = ROOT / design_path
    design = loader.load_design_parameters(design_path)
    constraints_path = (
        Path(constraints_path) if constraints_path is not None else ROOT / "constraints.json"
    )
    reference_path = (
        Path(reference_path) if reference_path is not None else ROOT / "reference_aircraft.json"
    )
    constraints = loader.load_constraints(constraints_path)
    ref = load_reference_aircraft(path=reference_path, design=design)
    aircraft = BatteryAircraft(constraints, design, ref)
    with contextlib.redirect_stdout(io.StringIO()) as captured:
        history = aircraft.converge_mtom()
        if (
            len(history) < 2
            or not all(math.isfinite(value) and value > 0 for value in history)
            or abs(history[-1] - history[-2]) >= 0.1
        ):
            raise ValueError(f"{design_path.name}: shared MTOM iteration did not converge")
        wing = aircraft.wing
        diag = aircraft.sizing_diagram()
        power_diag = aircraft.sizing_diagram(mode="power")
    mass, area = float(aircraft.mtom), float(wing.area)
    v2 = float(calc_takeoff_safety_speed(
        diag.design_wing_loading, diag.rho_takeoff, diag.c_a_max_to
    ))
    v2_actual_loading = float(calc_takeoff_safety_speed(
        mass / area, diag.rho_takeoff, diag.c_a_max_to
    ))
    installed_power = float(aircraft.total_takeoff_power)
    eta = float(design.propulsion.etaPropTakeOff)
    equivalent_thrust = installed_power * eta / v2
    idx = int(abs(diag.wing_loadings - diag.design_wing_loading).argmin())
    return {
        "design": design_path.name,
        "input_files": {
            "design": str(design_path.resolve()),
            "constraints": str(constraints_path.resolve()),
            "reference": str(reference_path.resolve()),
        },
        "mass_kg": mass,
        "iteration_count": len(history) - 1,
        "last_delta_kg": float(history[-1] - history[-2]),
        "mass_limit_kg": float(constraints.performance.takeOffMassMax.si),
        "mass_limit_satisfied": mass <= constraints.performance.takeOffMassMax.si,
        "wing_area_m2": area,
        "span_m": float(wing.span),
        "aspect_ratio": float(wing.aspect_ratio),
        "sizing_wing_loading_kg_m2": float(diag.design_wing_loading),
        "mass_over_area_kg_m2": mass / area,
        "v2_from_sizing_loading_m_s": v2,
        "v2_from_actual_mass_over_area_m_s": v2_actual_loading,
        "v2_from_actual_mass_over_area_kt": v2_actual_loading * 3600 / 1852,
        "installed_shaft_power_kw": installed_power / 1000,
        "number_of_engines": int(design.propulsion.numberOfEngines),
        "takeoff_propeller_efficiency": eta,
        "required_takeoff_thrust_N": float(aircraft.total_takeoff_thrust),
        "required_shaft_power_kw": float(aircraft.required_takeoff_power) / 1000,
        "equivalent_available_thrust_at_model_v2_N": equivalent_thrust,
        "single_motor_equivalent_at_same_v2_N": (
            equivalent_thrust / design.propulsion.numberOfEngines
        ),
        "reference_C_D0": float(ref.zero_lift_drag_coefficient),
        "reference_oswald": float(ref.data.assumptions.oswaldFactor),
        "design_oswald": float(design.aerodynamics.oswaldFactor),
        "wing_C_D0_cruise": float(wing.wing_zero_lift_drag_coefficient),
        "whole_aircraft_C_D0_cruise": float(wing.zero_lift_drag_coefficient),
        "C_L_cruise": float(wing.cruise_lift_coefficient),
        "C_D_cruise": float(wing.cruise_drag_coefficient),
        "L_D_cruise": float(wing.lift_to_drag_cruise),
        "oei_eps_used_to_build_curve": float(diag.eps),
        "oei_L_D_used_to_build_curve": 1 / float(diag.eps),
        "displayed_reference_L_D_at_final_point": float(diag.l_d_cruise),
        "oei_climb_min": float(diag.gamma_min_oei),
        "thrust_mode_constraint_values": {
            "takeoff": float(diag.y_takeoff[idx]),
            "OEI": float(diag.y_climb[idx]),
            "cruise": float(diag.y_cruise[idx]),
        },
        "thrust_mode_active": diag.active_constraint,
        "thrust_mode_feasible": diag.within_max_power,
        "power_mode_wing_loading": float(power_diag.design_wing_loading),
        "power_mode_active": power_diag.active_constraint,
        "power_mode_feasible": power_diag.within_max_power,
        "warnings": captured.getvalue().strip(),
    }


def build_audit(design_paths, constraints_path=None, reference_path=None):
    """Collect current shared-model outputs without changing loader source files."""
    sync_fields = loader._sync_dataclass_fields_in_source
    try:
        loader._sync_dataclass_fields_in_source = lambda cls, keys: False
        with project_imports():
            results = [
                snapshot(path, constraints_path, reference_path) for path in design_paths
            ]
            first = results[0]
            try:
                zero_speed = calc_thrust_loading_from_power(
                    SiValue(first["installed_shaft_power_kw"], "kW"),
                    SiValue(0, "m/s"),
                    SiValue(first["mass_kg"], "kg"),
                    first["takeoff_propeller_efficiency"],
                )
            except ZeroDivisionError:
                zero_speed = "ZeroDivisionError"
            verification = {}
            for script in ("polar_oswald.py", "wing_design_polar.py"):
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    runpy.run_path(
                        str(ROOT / "scripts" / "verification" / script),
                        run_name="__main__",
                    )
                verification[script] = {
                    "completed": True,
                    "selected_output": [
                        line for line in captured.getvalue().splitlines()
                        if "Fitted Oswald" in line or "Configured JSON" in line
                    ],
                }
        return {
            "note": (
                "Existing-model outputs; no S_AS or V1 prediction. "
                "Source synchronization disabled. Zero-speed power/thrust division "
                "is an intentional diagnostic, not an audit failure."
            ),
            "snapshots": results,
            "power_to_thrust_at_zero_speed": zero_speed,
            "existing_verification": verification,
        }
    finally:
        loader._sync_dataclass_fields_in_source = sync_fields


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--design", type=Path, action="append",
        help="design JSON to audit; repeat for multiple designs; default: current and baseline",
    )
    parser.add_argument("--constraints", type=Path, default=ROOT / "constraints.json")
    parser.add_argument("--reference", type=Path, default=ROOT / "reference_aircraft.json")
    parser.add_argument(
        "--output", type=Path,
        help="optional snapshot JSON path; without this option, only stdout is written",
    )
    args = parser.parse_args()
    designs = [path.resolve() for path in args.design] if args.design else [
        ROOT / "design_parameters.json", ROOT / "design_parameters_baseline.json"
    ]
    try:
        output = build_audit(designs, args.constraints, args.reference)
        text = json.dumps(output, indent=2, allow_nan=False)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
    except (OSError, ImportError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.error(str(error))
    print(text)


if __name__ == "__main__":
    main()
