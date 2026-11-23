"""Four landing-gear concepts for the project's high-wing aircraft.

Run with the existing Anaconda Python 3.9 environment:
    python scripts/landing_gear_estimation.py
    python scripts/landing_gear_estimation.py --mass 8946.28 --track 3.6

The default MTOM is BatteryAircraft.mtom after converge_mtom(), following
the same default workflow as cl_max.py. Wing area and span are read from
that aircraft's WingDesign properties. The constraints MTOM is reported
as a limit, while the design JSON MTOM supplies the iteration seed.
The fuselage section is the user-specified 1.72 m x 2.25 m rectangle.
Geometry, ground loads and material properties absent from the project data
remain explicit assumptions, printed with their sources on each run.

Torenbeek coefficients: Strohmayer, Flugzeugentwurf II, PDF p.124 in
Literature-20261115T203837Z-1-001.zip. Main gear includes BOTH sides.
Geometry correction:
    gear_mass = Torenbeek_mass + 2*(tube_mass_mount - tube_mass_fuselage)
The empirical baseline is anchored to the assumed fuselage installation.
This anchoring is a modeling assumption, not part of the Torenbeek formula.
The fixed/retractable regression difference represents the complete
configuration difference; no additional actuator mass is added.

The tube is an equivalent straight, unbraced, circular cantilever from
attachment to axle. It is sized for axial+bending stress, Euler buckling
and transverse deflection. This differential model does not size an oleo,
a spring leg, pivots, brakes, tire compliance, fatigue or retraction motion.
It excludes airframe reinforcement, wheel bays, doors and fairings.

Only this new file needs editing to change assumptions. Project model
imports use the existing cl_max.project_imports compatibility context.
No project files are written by this entry point.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, replace
from math import hypot, isfinite, pi, sqrt
from pathlib import Path

# Suppress bytecode writes when loading the shared project modules.
sys.dont_write_bytecode = True
from cl_max import project_imports


ROOT = Path(__file__).resolve().parent.parent
HIGH_WING_FACTOR = 1.08
FIXED_MAIN = (9.1, 0.082, 0.019, 0.0)
FIXED_NOSE = (11.3, 0.0, 0.0024, 0.0)
RETRACT_MAIN = (18.1, 0.131, 0.019, 2.23e-5)
RETRACT_NOSE = (9.1, 0.082, 0.0, 2.97e-6)


@dataclass(frozen=True)
class Assumptions:
    # Geometry in meters, referenced to the ground plane.
    fuselage_width: float = 1.72
    fuselage_height: float = 2.25
    belly_clearance: float = 0.65
    wheel_radius: float = 0.30
    track: float = 3.20
    fuselage_mount_above_belly: float = 0.15
    fuselage_mount_inset: float = 0.10
    wing_mount_below_roof: float = 0.20
    # Wing mount is vertically above each main wheel at track/2.
    # Both concepts have zero longitudinal offset from attachment to axle.
    main_static_load_fraction: float = 0.90
    vertical_limit_factor: float = 2.0
    braking_static_weight_fraction: float = 0.80
    side_static_weight_fraction: float = 0.50
    ultimate_factor: float = 1.50
    # Illustrative equivalent steel tube, not a selected alloy specification.
    density: float = 7850.0
    young_modulus_pa: float = 210e9
    allowable_stress_pa: float = 600e6
    wall_to_diameter: float = 0.08
    minimum_wall_m: float = 0.003
    effective_length_factor: float = 2.0
    maximum_deflection_fraction: float = 0.02
    mass_multiplier: float = 1.35


@dataclass(frozen=True)
class Leg:
    height: float
    lateral_offset: float
    length: float
    diameter: float
    wall: float
    mass: float
    axial_force: float
    bending_moment: float
    governing: str


@dataclass(frozen=True)
class GearEstimate:
    mounting: str
    gear_type: str
    empirical_main: float
    empirical_nose: float
    structural_delta: float

    @property
    def main(self):
        return self.empirical_main + self.structural_delta

    @property
    def total(self):
        return self.main + self.empirical_nose


@dataclass(frozen=True)
class ProjectInputs:
    mass: float
    gravity: float
    wing_area: float
    wingspan: float
    mass_limit: float
    initial_sizing_mass: float
    mass_source: str


def empirical_group(mass_kg, coefficients):
    a, b, c, d = coefficients
    return HIGH_WING_FACTOR * (
        a + b * mass_kg**0.75 + c * mass_kg + d * mass_kg**1.5
    )


def size_leg(height, lateral_offset, mass_kg, gravity, assumptions):
    """Size one equivalent tube under conservative combined ground loads."""
    a = assumptions
    if height <= 0:
        raise ValueError("attachment must be above the main wheel axle")
    length = hypot(height, lateral_offset)
    static_load = mass_kg * gravity * a.main_static_load_fraction / 2
    fz = static_load * a.vertical_limit_factor * a.ultimate_factor
    fx = static_load * a.braking_static_weight_fraction * a.ultimate_factor
    fy = static_load * a.side_static_weight_fraction * a.ultimate_factor
    # Envelope of adverse force signs. Axial and bending maxima are combined
    # conservatively, rather than selecting one signed vector load case.
    axial = (fz * height + fy * abs(lateral_offset)) / length
    moment = hypot(fz * abs(lateral_offset) + fy * height, fx * length)
    shear = moment / length

    def utilization(diameter):
        wall = a.wall_to_diameter * diameter
        inner = diameter - 2 * wall
        area = pi / 4 * (diameter**2 - inner**2)
        inertia = pi / 64 * (diameter**4 - inner**4)
        section_modulus = 2 * inertia / diameter
        # Normal stress plus a conservative transverse shear allowance.
        stress = sqrt(
            (axial / area + moment / section_modulus)**2 + 3 * (2 * shear / area)**2
        )
        euler_load = pi**2 * a.young_modulus_pa * inertia / (
            a.effective_length_factor * length
        )**2
        deflection = shear * length**3 / (3 * a.young_modulus_pa * inertia)
        ratios = (
            stress / a.allowable_stress_pa,
            axial / euler_load,
            deflection / (a.maximum_deflection_fraction * length),
        )
        return ratios, wall, area

    low = a.minimum_wall_m / a.wall_to_diameter
    high = 1.0
    if low >= high or max(utilization(high)[0]) > 1:
        raise ValueError("equivalent tube needs a diameter beyond the 1 m search bound")
    # Fixed wall/diameter ratio makes all three checks monotonic in diameter.
    if max(utilization(low)[0]) <= 1:
        high = low
    else:
        for _ in range(70):
            middle = (low + high) / 2
            if max(utilization(middle)[0]) > 1:
                low = middle
            else:
                high = middle
    ratios, wall, area = utilization(high)
    governing = ("stress", "Euler buckling", "deflection")[
        max(range(3), key=lambda i: ratios[i])
    ]
    return Leg(
        height, lateral_offset, length, high, wall,
        a.density * area * length * a.mass_multiplier,
        axial, moment, governing,
    )


def estimate_concepts(mass_kg, gravity, assumptions):
    a = assumptions
    nonnegative = {
        "fuselage_mount_above_belly", "fuselage_mount_inset",
        "wing_mount_below_roof", "braking_static_weight_fraction",
        "side_static_weight_fraction",
    }
    for field in a.__dataclass_fields__:
        value = getattr(a, field)
        if not isfinite(value) or value < 0 or (value == 0 and field not in nonnegative):
            raise ValueError(f"assumption {field} is outside its finite physical range")
    if a.ultimate_factor < 1 or a.mass_multiplier < 1:
        raise ValueError("ultimate factor and mass multiplier must be at least 1")
    if not isfinite(mass_kg) or mass_kg <= 0:
        raise ValueError("mass must be finite and positive")
    if not 0 < a.main_static_load_fraction < 1:
        raise ValueError("main static load fraction must lie between 0 and 1")
    if not 0 < a.wall_to_diameter < 0.5:
        raise ValueError("tube wall/diameter must lie between 0 and 0.5")
    if a.fuselage_mount_inset >= a.fuselage_width / 2:
        raise ValueError("fuselage mount inset must be less than half the fuselage width")
    if a.wing_mount_below_roof >= a.fuselage_height:
        raise ValueError("high-wing mount must lie above the belly")
    if a.track / 2 <= a.fuselage_width / 2:
        raise ValueError("main wheels and wing attachments must be outboard of the fuselage")

    fuselage_mount_y = a.fuselage_width / 2 - a.fuselage_mount_inset
    fuselage_height = a.belly_clearance + a.fuselage_mount_above_belly - a.wheel_radius
    wing_height = (
        a.belly_clearance + a.fuselage_height - a.wing_mount_below_roof - a.wheel_radius
    )
    fuselage_leg = size_leg(
        fuselage_height, a.track / 2 - fuselage_mount_y, mass_kg, gravity, a
    )
    wing_leg = size_leg(wing_height, 0.0, mass_kg, gravity, a)
    results = []
    for mounting, leg in (("fuselage", fuselage_leg), ("high wing", wing_leg)):
        delta = 2 * (leg.mass - fuselage_leg.mass)
        for gear_type, main, nose in (
            ("fixed", FIXED_MAIN, FIXED_NOSE),
            ("retractable", RETRACT_MAIN, RETRACT_NOSE),
        ):
            results.append(GearEstimate(
                mounting, gear_type, empirical_group(mass_kg, main),
                empirical_group(mass_kg, nose), delta,
            ))
    return fuselage_leg, wing_leg, results


def load_project(design_path, constraints_path, mass_override):
    with project_imports():
        from aircraft import BatteryAircraft
        from constants import GRAVITY
        from data import SiValue, loader
        from reference_aircraft import load_reference_aircraft
    sync = loader._sync_dataclass_fields_in_source
    try:
        loader._sync_dataclass_fields_in_source = lambda cls, keys: False
        design = loader.load_design_parameters(design_path)
        constraints = loader.load_constraints(constraints_path)
        reference = load_reference_aircraft(design=design)
    finally:
        loader._sync_dataclass_fields_in_source = sync
    # Follow cl_max.py: the configured mass seeds the shared aircraft mass
    # iteration. Use one converged aircraft state for all four gear concepts.
    mass_limit = float(constraints.performance.takeOffMassMax.si)
    initial_mass = float(design.initialSizing.maximumTakeOffMass.si)
    if mass_override is not None and (
        not isfinite(mass_override) or mass_override <= 0
    ):
        raise ValueError("mass override must be finite and positive")
    model_mass = SiValue(mass_override, "kg") if mass_override is not None else None
    aircraft = BatteryAircraft(constraints, design, reference, mtom=model_mass)
    mass_source = "explicit --mass override"
    if mass_override is None:
        history = aircraft.converge_mtom()
        if (
            len(history) < 2
            or not all(isfinite(value) and value > 0 for value in history)
            or abs(history[-1] - history[-2]) >= 0.1
        ):
            raise ValueError("project MTOM iteration did not converge within 0.1 kg")
        mass_source = "aircraft.BatteryAircraft.converge_mtom() -> aircraft.mtom"
    mass = float(aircraft.mtom)
    # Read the shared model's results directly. Preserve its area and span
    # constraints rather than introducing a second geometry calculation.
    wing = aircraft.wing
    area = float(wing.area)
    span = float(wing.span)
    if any(not isfinite(value) or value <= 0 for value in (mass, area, span)):
        raise ValueError("project mass, wing area and span must be finite and positive")
    return ProjectInputs(
        mass, float(GRAVITY), area, span, mass_limit, initial_mass, mass_source
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--design", type=Path, default=ROOT / "config" / "design_parameters.json"
    )
    parser.add_argument(
        "--constraints", type=Path, default=ROOT / "config" / "constraints.json"
    )
    parser.add_argument(
        "--mass", type=float,
        help="optional MTOM override, kg; default from the converged project aircraft model"
    )
    parser.add_argument("--belly-clearance", type=float, default=0.65, help="belly height above ground, m")
    parser.add_argument("--wheel-radius", type=float, default=0.30, help="loaded main tire radius, m")
    parser.add_argument("--track", type=float, default=3.20, help="main wheel center-to-center track, m")
    parser.add_argument("--wing-mount-below-roof", type=float, default=0.20, help="assumed wing attachment below fuselage roof, m")
    args = parser.parse_args()
    try:
        assumptions = replace(
            Assumptions(), belly_clearance=args.belly_clearance,
            wheel_radius=args.wheel_radius, track=args.track,
            wing_mount_below_roof=args.wing_mount_below_roof,
        )
        project = load_project(
            args.design, args.constraints, args.mass
        )
        fuselage_leg, wing_leg, results = estimate_concepts(
            project.mass, project.gravity, assumptions
        )
        if args.track >= project.wingspan:
            raise ValueError("wing attachment track must be less than the project wingspan")
    except (ValueError, OSError, ImportError, KeyError, TypeError) as error:
        parser.error(str(error))

    print(
        f"Common MTOM: {project.mass:.1f} kg; project wing area: "
        f"{project.wing_area:.3f} m^2; span: {project.wingspan:.3f} m"
    )
    print(f"MTOM source: {project.mass_source}")
    print(f"Design input: {args.design.resolve()}")
    print(f"Constraints input: {args.constraints.resolve()}")
    print(
        f"Design iteration seed: {project.initial_sizing_mass:.1f} kg; "
        f"specified MTOM limit: {project.mass_limit:.1f} kg"
    )
    print("Wing area/span source: aircraft.BatteryAircraft.wing -> wing.WingDesign.")
    print("Wing area/span are read directly from the same aircraft state as the MTOM.")
    print("The shared WingDesign retains its configured mass and span constraints.")
    print(f"Gravity source: constants.GRAVITY = {project.gravity:g} m/s^2")
    print(f"Landing mass assumption: equal to the selected MTOM, {project.mass:.1f} kg")
    if project.mass > project.mass_limit:
        print("The selected mass exceeds the project mass limit.")
    print("Empirical masses use uncalibrated Torenbeek regressions (high-wing factor 1.08).")
    print("Fuselage geometry is the user-specified rectangular 1.72 m x 2.25 m section.")
    print("Assumptions below are user dimensions or values absent from project inputs.")
    print("Ground load factors are separate from the project's flight limitLoad.")
    print("Assumptions (SI units; coefficients and fractions are dimensionless):")
    for field in assumptions.__dataclass_fields__:
        print(f"  {field}: {getattr(assumptions, field):g}")
    print("Wing attachment: roof minus offset, directly above each main wheel.")
    print("Tube checks combine ultimate vertical, braking and side load envelopes.")
    print("Fuselage empirical baseline anchors the structural correction.")
    print("\nOne main leg, equivalent unbraced tube:")
    for name, leg in (("fuselage", fuselage_leg), ("high wing", wing_leg)):
        print(
            f"  {name:10s} height={leg.height:.3f} m; lateral={leg.lateral_offset:.3f} m; "
            f"length={leg.length:.3f} m; D={leg.diameter*1000:.1f} mm; "
            f"wall={leg.wall*1000:.1f} mm; mass={leg.mass:.1f} kg"
        )
        print(f"    axial={leg.axial_force/1000:.1f} kN; bending={leg.bending_moment/1000:.1f} kNm; governing={leg.governing}")
    print("\nAll gear masses include BOTH main legs and the nose gear.")
    print(f"{'Mount':12s} {'Type':12s} {'Base main':>10s} {'Strut delta':>12s} {'Main':>10s} {'Nose':>10s} {'Total kg':>10s}")
    for result in results:
        print(
            f"{result.mounting:12s} {result.gear_type:12s} "
            f"{result.empirical_main:10.1f} {result.structural_delta:12.1f} "
            f"{result.main:10.1f} {result.empirical_nose:10.1f} {result.total:10.1f}"
        )
    difference = results[1].total - results[0].total
    print(f"\nRetractable minus fixed regression difference: {difference:.1f} kg.")
    print("This difference includes the statistical configuration effects; actuator mass is not separately resolved.")
    print(f"High-wing minus fuselage main-strut correction: {2*(wing_leg.mass-fuselage_leg.mass):.1f} kg.")
    print("Airframe reinforcement, wheel bays, doors, fairings and drag/energy effects need separate budgets.")
    print("Tube dimensions and loads are conceptual assumptions for the geometry correction.")


if __name__ == "__main__":
    main()
