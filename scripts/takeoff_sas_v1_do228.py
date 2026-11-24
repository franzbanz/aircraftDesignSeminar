"""Do228-based conceptual accelerate-stop distance and balanced V1.

Default mass: BatteryAircraft.mtom after converge_mtom(), NOT the mass limit.
Run from any directory: python <project>/scripts/takeoff_sas_v1_do228.py
Test another mass: python scripts/takeoff_sas_v1_do228.py --mass 8000
Print machine-readable results: add --json
Only stdout is written. The original solver, project sources and JSON are unchanged.

New aerodynamic basis (one consistent SYMMETRIC polar):
H: Hoogreef et al. (2023), Coupled Hybrid & Electric Aircraft Design and
   Strategic Airline Planning, printed p.19, section III.B, Eq.47:
   Do228 clean CD0=.025, clean e=.80. These are model estimates, not flight data.
   https://pure.tudelft.nl/ws/portalfiles/portal/154234691/6.2023_3869.pdf
   The paper's CLEAN CLmax=1.7 is not adopted as verified takeoff CLmax.
   Takeoff CLmax is still read from the project's design configuration.

The project's computed new-aircraft CD0 is re-anchored to H as follows:
  CD0_new = CD0_project + (CD0_H - CD0_project_reference) * S_ref / S_new
This preserves the existing wing/rest-airframe drag buildup and area convention;
the re-anchoring is this implementation's modeling assumption, not H's formula.
The original project-reference CD0 and S_ref are read live from ReferenceAircraft.
  e_TO = e_clean * .939
The .939 takeoff/clean ratio comes from R Table 3; it is a generic correction,
not a Do228 measured takeoff value. --oswald overrides the effective e_TO.

Finger et al. (2020) use a DIFFERENT asymmetric Do228 polar:
  CD=.029+(CL-.17)^2/(pi*9*.63).
Those .029/.17/.63 values are deliberately not mixed into this symmetric model.
  https://pure.tudelft.nl/ws/files/68466812/6.2020_1006.pdf

CL_ground=.45, flap/gear increments, friction, transition times and the historical
equivalent-gradient correlation remain explicitly unvalidated Do228 assumptions.
Manufacturer ASD=781 m at 6400 kg, flaps 1, dry/level/no-wind/SL/ISA is recorded
as a REFERENCE ONLY; it is not used to force-fit our larger aircraft's distance:
  https://www.ga-ats.com/en/do228-nxt/the-aircraft/technical-data

Sources (numbers in comments refer to these documents):
T: Torenbeek (1976), Synthesis of Subsonic Airplane Design:
   pp. 165, 168-170, 578, 583-586; Eqs. 5-51, 5-82, 5-85, 5-87,
   5-90, K-9, K-31. The .024/.027/.030 reference gradients belong to
   the historical transport-aircraft correlation, not the project CS-23 rule.
   https://drive.google.com/file/d/1ubOLpyezKYMSQwF17a3Ucknx9cq4tq1y/view
N: NASA, Sensitivity Analysis for TOL Distance Parameters for RAM Aircraft,
   Tables 1-2: mu_roll=.02, mu_brake=.36, ground CL=.30-.60.
   https://ntrs.nasa.gov/api/citations/20240007499/downloads/Sensitivity_Analysis_for_TOL_Martinez.pdf
R: Metz et al. (2016), Appendix B, Tables 2-3, after Roskam (1989).
   https://pure.tudelft.nl/ws/files/10056382/Metz_AIAA_Aircraft_Performance_2016.pdf
G: Purdue AAE451, ground effect and reference speeds, after Gudmundsson.
   https://thiagopurdue.github.io/AAE451_Advanced_Design_Notes/drag-polar/
   https://thiagopurdue.github.io/AAE451_Advanced_Design_Notes/climb-and-field/
D: EASA.A.359, Issue 08, section 6.1: reference Do228 MT propeller D=2.5 m.
   https://www.easa.europa.eu/en/downloads/7178/en

The empirical stop allowance includes recognition; recognition is integrated
ONLY to map the balanced failure speed V_EF to V1, not added twice to distance.
This is a conceptual correlation, not a certification-performance prediction.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from cl_max import project_imports

DO228_CLEAN_CD0 = 0.025
DO228_CLEAN_OSWALD = 0.80
DO228_POLAR_SOURCE = (
    "https://pure.tudelft.nl/ws/portalfiles/portal/154234691/6.2023_3869.pdf"
)


@dataclass(frozen=True)
class Inputs:
    mass: float
    area: float
    span: float
    power: float
    eta: float
    clmax: float
    cd0: float
    rho: float
    rho0: float
    gravity: float
    engines: int
    wing_height: float
    gamma_required: float
    mass_limit: float
    field_limit: float
    project_cd0: float
    project_reference_cd0: float
    reference_area: float
    reference_cd0_used: float


@dataclass(frozen=True)
class Assumptions:
    diameter: float = 2.5  # D: reference-aircraft analogy, not a selected new prop.
    mu_roll: float = 0.02  # T / N, dry hard runway.
    mu_brake: float = 0.36  # N: baseline inferred from +/-20% bounds.
    cl_ground: float = 0.45  # N range midpoint; NOT verified Do228 ground CL.
    flap_drag: float = 0.015  # R: midpoint .010-.020, takeoff flaps.
    gear_drag: float = 0.020  # R: midpoint .015-.025.
    oswald_clean: float = DO228_CLEAN_OSWALD  # H: clean Do228 model.
    takeoff_e_ratio: float = 0.939  # R Table 3, generic takeoff/clean correction.
    oswald: float | None = None  # Optional direct override of effective takeoff e.
    oei_e_factor: float = 0.90  # T: wing-mounted engines, 10% e reduction.
    oei_drag_factor: float = 1.04  # T: 4% feathered-propeller drag allowance.
    delay: float = 3.5  # T pp.583-586: equivalent inertia time, includes recognition.
    recognition: float = 1.0  # T p.578; for failure-speed -> decision-speed mapping.
    vr_ratio: float = 1.1  # G: conceptual rotation speed / stall speed.
    v2_ratio: float = 1.2  # Project sizing_diagram.py; G.
    screen: float = 35 * 0.3048  # 35 ft, CS-23 commuter screen height.
    gamma_offset: float = 0.06  # T Eq.5-90 historical equivalent-gradient fit.
    gamma_reference: float = 0.024  # T Eq.5-91, TWO-engine correlation reference.

    @property
    def effective_oswald(self):
        if self.oswald is not None:
            return self.oswald
        return self.oswald_clean * self.takeoff_e_ratio


def read_project(
    design_path, constraints_path, mass_override=None,
    reference_cd0=DO228_CLEAN_CD0, reference_path=None,
):
    """Read live project outputs, suppressing the loader's source synchronization."""
    if not math.isfinite(reference_cd0) or reference_cd0 <= 0:
        raise ValueError("reference CD0 must be finite and positive")
    if mass_override is not None and (
        not math.isfinite(mass_override) or mass_override <= 0
    ):
        raise ValueError("mass must be finite and positive")
    with project_imports():
        from aircraft import BatteryAircraft
        from constants import GRAVITY, RHO_0, isa_density
        from data import SiValue, loader
        from landing_gear_estimation import Assumptions as GearAssumptions
        from reference_aircraft import load_reference_aircraft

    sync = loader._sync_dataclass_fields_in_source
    captured = io.StringIO()
    try:
        loader._sync_dataclass_fields_in_source = lambda cls, keys: False
        with contextlib.redirect_stdout(captured):
            design = loader.load_design_parameters(design_path)
            constraints = loader.load_constraints(constraints_path)
            reference = load_reference_aircraft(
                path=reference_path if reference_path is not None else ROOT / "reference_aircraft.json",
                design=design,
            )
            aircraft = BatteryAircraft(
                constraints, design, reference,
                mtom=SiValue(mass_override, "kg") if mass_override is not None else None,
            )
            if mass_override is None:
                history = aircraft.converge_mtom()
                if (
                    len(history) < 2
                    or not all(math.isfinite(value) and value > 0 for value in history)
                    or abs(history[-1] - history[-2]) >= 0.1
                ):
                    raise ValueError("project MTOM iteration did not converge")
            wing = aircraft.wing
            gear = GearAssumptions()
            altitude = float(constraints.performance.takeOffAltitude.si)
            if not math.isfinite(altitude) or altitude > 11000:
                raise ValueError("project ISA density model requires altitude <= 11000 m")
            area = float(wing.area)
            project_cd0 = float(wing.zero_lift_drag_coefficient)
            old_reference_cd0 = float(reference.zero_lift_drag_coefficient)
            reference_area = float(reference.data.dimensions.wingArea.si)
            corrected_cd0 = project_cd0 + (
                reference_cd0 - old_reference_cd0
            ) * reference_area / area
            inputs = Inputs(
                mass=float(aircraft.mtom), area=area, span=float(wing.span),
                power=float(aircraft.total_takeoff_power),
                eta=float(design.propulsion.etaPropTakeOff),
                clmax=float(design.wing.maxTakeOffLiftCoefficient),
                cd0=corrected_cd0,
                rho=float(isa_density(altitude)), rho0=float(RHO_0),
                gravity=float(GRAVITY),
                engines=int(design.propulsion.numberOfEngines),
                wing_height=(gear.belly_clearance + gear.fuselage_height
                             - gear.wing_mount_below_roof),
                gamma_required=float(constraints.cs23.minClimbGradient),
                mass_limit=float(constraints.performance.takeOffMassMax.si),
                field_limit=float(constraints.performance.takeOffFieldLengthMax.si),
                project_cd0=project_cd0,
                project_reference_cd0=old_reference_cd0,
                reference_area=reference_area,
                reference_cd0_used=reference_cd0,
            )
    finally:
        loader._sync_dataclass_fields_in_source = sync
    return inputs, captured.getvalue().strip()


def ground_distance(v, acceleration, quadratic):
    """Integral of v/(acceleration-quadratic*v^2), from zero to v [m]."""
    if acceleration <= 0 or acceleration - quadratic * v * v <= 0:
        raise ValueError("nonpositive acceleration/deceleration in speed interval")
    if abs(quadratic * v * v / acceleration) < 1e-10:
        return v * v / (2 * acceleration)
    return -math.log1p(-quadratic * v * v / acceleration) / (2 * quadratic)


def advance_speed(v, duration, acceleration, quadratic):
    """RK4 integration of dv/dt=A-Bv^2; negative duration gives inverse mapping."""
    steps = max(1, math.ceil(abs(duration) / 0.02))
    dt = duration / steps
    def rate(speed):
        return acceleration - quadratic * speed * speed

    for _ in range(steps):
        k1 = rate(v)
        k2 = rate(v + dt * k1 / 2)
        k3 = rate(v + dt * k2 / 2)
        k4 = rate(v + dt * k3)
        v += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        if not math.isfinite(v) or v < 0:
            raise ValueError("recognition-time speed mapping left the ground-roll domain")
    return v


def calculate(p, a, vmcg=None):
    for key, value in asdict(p).items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{key} must be finite and positive")
    for key, value in asdict(a).items():
        if key == "oswald" and value is None:
            continue
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{key} must be finite and nonnegative")
    if p.engines not in (2, 3, 4) or not 0 < p.eta <= 1:
        raise ValueError("2-4 motors and propeller efficiency in (0,1] are required")
    e_to = a.effective_oswald
    if not (0 < a.oswald_clean <= 1 and 0 < a.takeoff_e_ratio <= 1
            and 0 < e_to <= 1 and 0 < a.oei_e_factor <= 1):
        raise ValueError("Oswald factors must lie in (0,1]")
    if a.oei_drag_factor < 1 or not (0 < a.vr_ratio < a.v2_ratio):
        raise ValueError("OEI drag factor >=1 and 0<VR/VS<V2/VS are required")
    if min(a.diameter, a.mu_brake, a.vr_ratio) <= 0 or a.delay < a.recognition:
        raise ValueError("positive diameter/braking; equivalent delay >= recognition")
    if vmcg is not None and (not math.isfinite(vmcg) or vmcg < 0):
        raise ValueError("VMCG must be finite and nonnegative")

    g, weight = p.gravity, p.mass * p.gravity
    aspect = p.span**2 / p.area
    sigma = p.rho / p.rho0
    phi = 33 * (p.wing_height / p.span)**1.5
    phi /= 1 + phi
    cd0_to = p.cd0 + a.flap_drag + a.gear_drag
    cd_ground = cd0_to + phi * a.cl_ground**2 / (math.pi * e_to * aspect)
    cd_ground_oei = a.oei_drag_factor * (
        cd0_to + phi * a.cl_ground**2 / (math.pi * e_to * a.oei_e_factor * aspect)
    )
    vs = math.sqrt(2 * weight / (p.rho * p.area * p.clmax))
    vr, v2 = a.vr_ratio * vs, a.v2_ratio * vs
    # T Eq.5-82 converted from kgf and kgf*m/s to N and W.
    thrust = 0.321 * p.power * (sigma * p.engines * g * a.diameter**2 / p.power)**(1/3)
    live = (p.engines - 1) / p.engines
    factor = p.rho * p.area / (2 * p.mass)
    acc = thrust / p.mass - g * a.mu_roll
    quad = factor * (cd_ground - a.mu_roll * a.cl_ground)
    acc_oei = live * thrust / p.mass - g * a.mu_roll
    quad_oei = factor * (cd_ground_oei - a.mu_roll * a.cl_ground)
    brake_a = g * a.mu_brake  # Residual thrust zero; no reverse/regeneration credit.
    brake_c = factor * (cd_ground - a.mu_brake * a.cl_ground)
    cl2 = p.clmax / a.v2_ratio**2
    cd2 = a.oei_drag_factor * (
        p.cd0 + a.flap_drag + cl2**2 / (math.pi * e_to * a.oei_e_factor * aspect)
    )  # Second segment: gear retracted; takeoff flaps retained.
    thrust2 = live * p.eta * p.power / v2
    gamma2 = thrust2 / weight - cd2 / cl2
    gamma_equivalent = a.gamma_offset + gamma2 - a.gamma_reference
    if acc_oei <= 0 or gamma2 <= 0 or gamma_equivalent <= 0:
        raise ValueError("model has insufficient OEI acceleration or climb capability")

    def pieces(v):
        s_acc = ground_distance(v, acc, quad)
        s_brake = ground_distance(v, brake_a, -brake_c)
        s_delay = v * a.delay
        s_continue = ((v2*v2 - v*v) / (2*g) + a.screen) / gamma_equivalent
        return s_acc, s_delay, s_brake, s_continue

    def residual(v):
        _, delay, brake, go = pieces(v)
        return delay + brake - go

    lower = vmcg if vmcg is not None else 0.0
    upper = advance_speed(vr, -a.recognition, acc_oei, quad_oei)
    if not lower < upper <= vr < v2:
        raise ValueError("no candidate failure-speed interval below VR")
    if 0.5 * p.rho * upper**2 * p.area * a.cl_ground >= weight:
        raise ValueError("assumed ground CL produces nonpositive wheel load")
    ground_distance(upper, acc, quad)
    ground_distance(upper, brake_a, -brake_c)
    if residual(lower) > 0:
        vx, status = lower, "unbalanced_lower_limit"
    elif residual(upper) < 0:
        vx, status = upper, "unbalanced_rotation_limit"
    else:
        lo, hi = lower, upper
        for _ in range(80):
            mid = (lo + hi) / 2
            if residual(mid) > 0:
                hi = mid
            else:
                lo = mid
        vx, status = (lo + hi) / 2, "balanced"
    v1 = advance_speed(vx, a.recognition, acc_oei, quad_oei)
    s_acc, s_delay, s_brake, s_continue = pieces(vx)
    sas, go = s_acc + s_delay + s_brake, s_acc + s_continue
    return {
        "status": status, "V_EF_m_s": vx, "V1_m_s": v1,
        "V1_kt": v1 * 3600 / 1852, "VS_m_s": vs, "VR_m_s": vr, "V2_m_s": v2,
        "S_accelerate_m": s_acc, "S_equivalent_delay_m": s_delay,
        "S_brake_m": s_brake, "S_AS_m": sas, "S_TOEF_m": go,
        "balance_residual_m": sas - go, "mean_AEO_thrust_N": thrust,
        "ground_CD": cd_ground, "ground_effect_factor": phi,
        "aspect_ratio": aspect, "CL2": cl2, "CD2_OEI": cd2,
        "clean_CD0_used": p.cd0,
        "clean_oswald_reference": a.oswald_clean,
        "takeoff_e_ratio": a.takeoff_e_ratio,
        "effective_oswald_takeoff": e_to,
        "gamma2": gamma2, "gamma_equivalent": gamma_equivalent,
        "project_mass_limit_satisfied": p.mass <= p.mass_limit,
        "project_OEI_gradient_satisfied": gamma2 >= p.gamma_required,
        "AS_OEI_distance_limit_satisfied": max(sas, go) <= p.field_limit,
        "VMCG_checked": vmcg is not None,
        "scope": (
            "Do228-based concept estimate, not Do228-calibrated performance. "
            "Ground CL, configuration increments and historical equivalent-gradient "
            "fit remain assumptions; AEO 1.15-distance and airborne VMC not checked."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", type=Path, default=ROOT / "design_parameters.json")
    parser.add_argument("--constraints", type=Path, default=ROOT / "constraints.json")
    parser.add_argument("--reference", type=Path, default=ROOT / "reference_aircraft.json")
    parser.add_argument("--mass", "--takeoff-mass", type=float, help="override converged MTOM, kg")
    for name in ("area", "span", "eta", "clmax", "cd0", "rho", "wing_height"):
        parser.add_argument("--" + name.replace("_", "-"), type=float)
    parser.add_argument("--power-kw", type=float, help="override TOTAL installed shaft power, kW")
    parser.add_argument("--engines", type=int)
    parser.add_argument("--reference-cd0", type=float, default=DO228_CLEAN_CD0,
                        help="Do228 CLEAN reference CD0; default .025 (Hoogreef 2023)")
    for name, value in asdict(Assumptions()).items():
        default_label = "auto: clean e times takeoff ratio" if value is None else f"{value:g}"
        parser.add_argument("--" + name.replace("_", "-"), type=float, default=None,
                            help=f"override empirical assumption; default {default_label}")
    parser.add_argument("--vmcg", type=float, help="optional ground control speed, m/s")
    parser.add_argument("--json", action="store_true", help="print JSON to stdout only")
    args = parser.parse_args()
    try:
        if args.mass is not None and (not math.isfinite(args.mass) or args.mass <= 0):
            raise ValueError("mass must be finite and positive")
        p, project_messages = read_project(
            args.design, args.constraints, args.mass, reference_cd0=args.reference_cd0,
            reference_path=args.reference,
        )
        changes = {name: getattr(args, name) for name in
                   ("area", "span", "eta", "clmax", "cd0", "rho", "wing_height", "engines")
                   if getattr(args, name) is not None}
        # An area-only override preserves the project's clean equivalent drag area.
        if args.area is not None and args.area > 0:
            if args.cd0 is None:
                changes["cd0"] = p.cd0 * p.area / args.area
            changes["project_cd0"] = p.project_cd0 * p.area / args.area
        if args.power_kw is not None:
            changes["power"] = args.power_kw * 1000
        p = replace(p, **changes)
        empirical = {name: getattr(args, name) for name in asdict(Assumptions())
                     if getattr(args, name) is not None}
        if args.gamma_reference is None:
            empirical["gamma_reference"] = {2: .024, 3: .027, 4: .030}.get(p.engines, .024)
        a = replace(Assumptions(), **empirical)
        result = calculate(p, a, args.vmcg)
        output = {
            "project_files": {
                "design": str(args.design.resolve()),
                "constraints": str(args.constraints.resolve()),
                "reference": str(args.reference.resolve()),
            },
            "mass_source": "manual override" if args.mass is not None else "BatteryAircraft.converge_mtom()",
            "inputs_SI": asdict(p), "assumptions_SI": asdict(a), "results": result,
            "project_messages": project_messages,
            "aerodynamic_provenance": {
                "reference_polar": "Hoogreef et al. 2023, printed p.19, III.B, symmetric clean Do228 model",
                "source_url": DO228_POLAR_SOURCE,
                "reference_CD0_published": DO228_CLEAN_CD0,
                "reference_clean_e_published": DO228_CLEAN_OSWALD,
                "CD0_transfer": "CD0_project+(CD0_reference_used-CD0_project_reference)*S_ref/S_new",
                "takeoff_e_transfer": "e_clean * takeoff_e_ratio (.939: Metz/Roskam Table 3)",
                "manual_target_CD0": args.cd0 is not None,
                "manual_reference_CD0": args.reference_cd0 != DO228_CLEAN_CD0,
                "manual_clean_e": args.oswald_clean is not None,
                "manual_effective_takeoff_e": args.oswald is not None,
                "not_verified_Do228_data": [
                    "cl_ground", "flap_drag", "gear_drag", "takeoff_e_ratio",
                    "mu_brake", "delay", "recognition", "gamma_offset", "gamma_reference",
                ],
                "manufacturer_ASD_reference_only": {
                    "distance_m": 781.0, "mass_kg": 6400.0,
                    "conditions": "Do228 flaps 1; dry paved, level, no wind, sea level ISA",
                    "used_for_calibration": False,
                    "source_url": "https://www.ga-ats.com/en/do228-nxt/the-aircraft/technical-data",
                },
            },
        }
        if args.json:
            print(json.dumps(output, indent=2, allow_nan=False))
        else:
            print(f"Mass source: {output['mass_source']}; MTOM={p.mass:.3f} kg")
            print(f"S={p.area:.5f} m^2; b={p.span:.3f} m; total shaft power={p.power/1000:.1f} kW")
            print(f"Clean CD0: project={p.project_cd0:.7f}; active={p.cd0:.7f}; Do228 reference={p.reference_cd0_used:.5f}")
            print(f"Oswald: clean={a.oswald_clean:.5f}; effective takeoff={a.effective_oswald:.5f}")
            print("Aerodynamic basis: Hoogreef 2023 Do228 symmetric clean polar; see --json for provenance.")
            print(f"Solution: {result['status']}")
            for key in ("V_EF_m_s", "V1_m_s", "V1_kt", "VR_m_s", "V2_m_s",
                        "S_accelerate_m", "S_equivalent_delay_m", "S_brake_m",
                        "S_AS_m", "S_TOEF_m", "balance_residual_m", "gamma2"):
                print(f"  {key}: {result[key]:.6f}")
            for key in ("project_mass_limit_satisfied", "project_OEI_gradient_satisfied",
                        "AS_OEI_distance_limit_satisfied", "VMCG_checked"):
                print(f"  {key}: {result[key]}")
            print(result["scope"])
    except (ValueError, ArithmeticError, OSError) as exc:
        parser.exit(2, f"Calculation error: {exc}\n")


if __name__ == "__main__":
    main()
