"""Compare four landing-gear concepts using a sourced equivalent oleo model.

Run from any working directory:
    python D:/document/aircraftDesignSeminar/scripts/landing_gear_estimation.py

Equations and parameter references are cited in this file's comments and
function docstrings. Cylinder mass is calculated explicitly as density *
annulus area * extended length. The high-wing/fuselage material-mass ratio
scales that same model's fuselage-cylinder mass, not the entire gear mass.
This ratio calculation is algebraically equivalent to the previous mass
difference; it does not calibrate the material model against Torenbeek.
This is a conceptual model, not a detailed Do228 reconstruction.
It never writes project inputs, source files, reports or bytecode.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, fields, replace
from math import cos, hypot, inf, isclose, isfinite, pi, sqrt
from pathlib import Path

sys.dont_write_bytecode = True
# Resolve paths from this file, never from the terminal's working directory.
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from cl_max import project_imports


PSI_TO_PA = 6894.757293168
HIGH_WING_FACTOR = 1.08
# Both main legs form ONE group. [Strohmayer - Flugzeugentwurf 2 | PDF p.124]
FIXED_MAIN = (9.1, 0.082, 0.019, 0.0)
FIXED_NOSE = (11.3, 0.0, 0.0024, 0.0)
RETRACT_MAIN = (18.1, 0.131, 0.019, 2.23e-5)
RETRACT_NOSE = (9.1, 0.082, 0.0, 2.97e-6)


@dataclass(frozen=True)
class Assumptions:
    # User dimensions; other geometry is a retained layout choice, not Do228 data.
    fuselage_width: float = 1.72
    fuselage_height: float = 2.25
    belly_clearance: float = 0.65
    wheel_radius: float = 0.30  # Loaded radius, NOT nominal tire diameter / 2.
    track: float = 3.20
    fuselage_mount_above_belly: float = 0.15
    fuselage_mount_inset: float = 0.10
    wing_mount_below_roof: float = 0.20
    # Both concepts use the same oleo architecture and piston bore family.
    main_static_fraction: float = 0.90  # Raymer 2018, p.343; provisional until CG.
    ground_reaction_factor: float = 3.0  # Raymer p.356, Table 11.5; chosen value.
    safety_factor: float = 1.50  # CS 23.303 / CS 23.2230; applied once to loads.
    oleo_static_pressure_pa: float = 1800.0 * PSI_TO_PA  # Raymer pp.357-358.
    minimum_outer_to_bore: float = 1.30  # Raymer p.358; selected starting size.
    oleo_efficiency: float = 0.80  # Raymer p.356, metered orifice range .75-.90.
    landing_lift_fraction: float = 2.0 / 3.0  # CS 23.473(e).
    stroke_margin: float = 0.03  # Raymer p.357, rounded SI recommendation.
    minimum_vertical_stroke: float = 0.20  # Raymer p.357.
    static_stroke_fraction: float = 2.0 / 3.0  # Raymer pp.353,357.
    # Selected 4340 normalized steel; NOT a verified Do228 material/allowable.
    # Tech Steel & Materials, "Steel 4340", normalized at 870 degrees C.
    density: float = 7850.0
    young_modulus_pa: float = 205e9
    yield_stress_pa: float = 860e6
    # Fixed-free equivalent column: K=2, AFFDL 1986 section 2.3.1.4.
    # An actual braced or hinged installation requires a different load model.
    effective_length_factor: float = 2.0
    # AFFDL section 2.3.1.8 gives equivalent ec/r_g^2 between .10 and .25.
    imperfection_ec_over_rg2: float = 0.25


@dataclass(frozen=True)
class ProjectInputs:
    mass: float
    gravity: float
    wing_area: float
    wingspan: float
    mass_limit: float
    initial_mass: float
    shared_raw_retractable_mass: float
    shared_calibrated_gear_mass: float
    reference_calibration: float
    mass_source: str


@dataclass(frozen=True)
class LoadCase:
    name: str
    fx: float  # Limit force on one wheel, N; aft positive.
    fy: float  # Outboard positive on the right-hand gear.
    fz: float  # Upward positive.


@dataclass(frozen=True)
class Geometry:
    name: str
    static_height: float
    static_lateral_offset: float
    static_length: float
    axial_stroke: float
    extended_length: float

    @property
    def height(self):
        return self.static_height * self.extended_length / self.static_length

    @property
    def lateral_offset(self):
        return self.static_lateral_offset * self.extended_length / self.static_length


@dataclass(frozen=True)
class CaseCheck:
    name: str
    compression_limit: float
    bending_limit: float
    pressure_limit: float
    euler_load: float
    column_load: float
    slenderness: float
    column_method: str
    stress_ratio: float
    buckling_ratio: float

    @property
    def utilization(self):
        return max(self.stress_ratio, self.buckling_ratio)


@dataclass(frozen=True)
class LegResult:
    geometry: Geometry
    bore: float
    diameter: float
    wall: float
    equivalent_mass: float
    checks: tuple[CaseCheck, ...]


@dataclass(frozen=True)
class Concept:
    mounting: str
    gear_type: str
    baseline_main: float
    baseline_nose: float
    fuselage_cylinder_pair_mass: float
    cylinder_mass_ratio: float

    @property
    def cylinder_pair_mass(self):
        """Mass of BOTH model cylinders after proportional scaling, kg."""
        return self.fuselage_cylinder_pair_mass * self.cylinder_mass_ratio

    @property
    def structural_delta(self):
        """Additional cylinder mass only: B * (k - 1), kg, for BOTH sides."""
        return self.fuselage_cylinder_pair_mass * (self.cylinder_mass_ratio - 1.0)

    @property
    def total(self):
        return self.baseline_main + self.baseline_nose + self.structural_delta


def validate_assumptions(a):
    """Reject nonphysical input before numerical sizing."""
    zero_allowed = {
        "fuselage_mount_above_belly", "fuselage_mount_inset",
        "wing_mount_below_roof", "stroke_margin", "imperfection_ec_over_rg2",
        "landing_lift_fraction",
    }
    for field in fields(a):
        value = getattr(a, field.name)
        if not isfinite(value) or value < 0 or (value == 0 and field.name not in zero_allowed):
            raise ValueError(f"invalid assumption: {field.name}")
    for name in ("main_static_fraction", "oleo_efficiency", "static_stroke_fraction"):
        if not 0 < getattr(a, name) < 1:
            raise ValueError(f"{name} must be between zero and one")
    if not 0 <= a.landing_lift_fraction <= 2.0 / 3.0:
        raise ValueError("landing lift fraction must lie in [0, 2/3]")
    if a.safety_factor < 1.5 or a.ground_reaction_factor < 2.0:
        raise ValueError("selected safety factor >= 1.5 and ground reaction factor >= 2 required")
    if a.ground_reaction_factor + a.landing_lift_fraction < 2.67:
        raise ValueError("ground plus lift factor must meet the CS 23.473(g) inertia floor")
    if a.minimum_outer_to_bore < 1.3:
        raise ValueError("outer/bore lower envelope must be at least the selected Raymer 1.30")
    if a.effective_length_factor != 2.0:
        raise ValueError("this cantilever load model requires K=2; braces need a new model")
    if a.fuselage_mount_inset >= a.fuselage_width / 2:
        raise ValueError("fuselage attachment inset exceeds half the fuselage width")
    if a.wing_mount_below_roof >= a.fuselage_height:
        raise ValueError("wing attachment must be above the fuselage belly")
    if a.track <= a.fuselage_width:
        raise ValueError("wheel track must be outside the fuselage width")
    if a.oleo_efficiency * a.ground_reaction_factor <= 1 - a.landing_lift_fraction:
        raise ValueError("selected energy absorption capacity is nonpositive")


def calc_stroke(project, a):
    """Energy screen: CS 23.473(d,e); Raymer 2018 pp.355-357.

    Ignore tire energy, include gravity minus residual lift, and add the cited
    stroke margin. This preliminary screen is not a drop-test simulation.
    W/S in the CS descent-speed expression is lbf/ft^2, not kg/m^2.
    """
    loading_psf = project.mass * project.gravity / project.wing_area / 47.88025898
    sink_speed = min(3.0, max(2.1, 4.4 * loading_psf**0.25 * 0.3048))
    net_energy_factor = (
        a.oleo_efficiency * a.ground_reaction_factor - 1 + a.landing_lift_fraction
    )
    stroke = sink_speed**2 / (2 * project.gravity * net_energy_factor)
    return sink_speed, max(a.minimum_vertical_stroke, stroke + a.stroke_margin)


def calc_geometries(a, vertical_stroke):
    """Construct common-wheel-track layouts using user fuselage dimensions."""
    fus_y = a.fuselage_width / 2 - a.fuselage_mount_inset
    layouts = (
        ("fuselage", a.belly_clearance + a.fuselage_mount_above_belly - a.wheel_radius,
         a.track / 2 - fus_y),
        ("high-wing", a.belly_clearance + a.fuselage_height
         - a.wing_mount_below_roof - a.wheel_radius, 0.0),
    )
    geometries = []
    for name, height, lateral in layouts:
        if height <= 0:
            raise ValueError(f"{name} attachment must be above the wheel axle")
        length = hypot(height, lateral)
        # The common requirement is vertical wheel travel, not axial oleo travel.
        axial_stroke = vertical_stroke * length / height
        extended = length + a.static_stroke_fraction * axial_stroke
        if extended < 2.5 * axial_stroke:
            raise ValueError(
                f"{name}: straight oleo cannot fit Raymer's approximately 2.5*stroke "
                "length screen; revise layout or select a levered architecture"
            )
        geometries.append(Geometry(name, height, lateral, length, axial_stroke, extended))
    return tuple(geometries)


def calc_load_cases(weight, a):
    """Separate limit cases; CS-23 Amdt 4, 23.479, 23.481, 23.485, 23.493.

    Landing and braking cases envelope main-only contact (no 90% multiplier).
    Spin-up/spring-back use the 25% minimum, pending Appendix D analysis.
    Side reactions .50W inboard and .33W outboard refer to AIRCRAFT weight.
    """
    landing_z = a.ground_reaction_factor * weight / 2
    roll_z = 1.33 * weight / 2
    return (
        LoadCase("tail-down vertical", 0.0, 0.0, landing_z),
        LoadCase("level spin-up minimum", 0.25 * landing_z, 0.0, landing_z),
        LoadCase("level spring-back envelope", -0.25 * landing_z, 0.0, landing_z),
        LoadCase("braked roll", 0.80 * roll_z, 0.0, roll_z),
        LoadCase("side inboard", 0.0, -0.50 * weight, roll_z),
        LoadCase("side outboard", 0.0, 0.33 * weight, roll_z),
    )


def calc_section(diameter, bore):
    """Exact circular-annulus area and bending second moment."""
    if not diameter > bore > 0:
        raise ValueError("outer diameter must exceed the positive bore")
    area = pi * (diameter**2 - bore**2) / 4
    inertia = pi * (diameter**4 - bore**4) / 64
    return area, inertia


def calc_column_capacity(area, inertia, length, a):
    """Euler/Johnson column capacity; AFFDL 1986 2.3.1.3, 2.3.1.11.4.

    F_co is approximated by the selected steel's typical yield stress.
    This is an explicit conceptual-material assumption, not a test curve.
    """
    slenderness = a.effective_length_factor * length / sqrt(inertia / area)
    euler = pi**2 * a.young_modulus_pa * inertia / (a.effective_length_factor * length)**2
    transition = sqrt(2 * pi**2 * a.young_modulus_pa / a.yield_stress_pa)
    if slenderness >= transition:
        return euler, euler, slenderness, "Euler"
    critical_stress = a.yield_stress_pa * (
        1 - a.yield_stress_pa * slenderness**2 / (4 * pi**2 * a.young_modulus_pa)
    )
    return euler, area * critical_stress, slenderness, "Johnson"


def calc_case_check(case, geometry, diameter, bore, a):
    """Check one ultimate-load envelope without a prescribed deflection limit.

    Mechanical actions: NASA CR-205551 pp.86-89; beam-column amplification:
    AFFDL 1986 2.3.1.7-8. Pressure: AFFDL 8.4.1, Eqs.8-35 to 8-39.
    All forces/pressures receive the same safety factor ONCE.
    """
    area, inertia = calc_section(diameter, bore)
    radius = diameter / 2
    h, y, length = geometry.height, geometry.lateral_offset, geometry.extended_length
    # Upward unit vector along the leg, from axle to attachment.
    ey, ez = -y / length, h / length
    axial_limit = case.fy * ey + case.fz * ez
    compression_limit = max(0.0, axial_limit)
    transverse_limit = sqrt(max(0.0, case.fx**2 + case.fy**2 + case.fz**2 - axial_limit**2))
    # r x F at the attachment. Use GROUND contact, including tire-radius arm.
    mx = y * case.fz + (h + a.wheel_radius) * case.fy
    my = -(h + a.wheel_radius) * case.fx
    mz = -y * case.fx
    torsion_limit = my * ey + mz * ez
    bending_limit = sqrt(max(0.0, mx**2 + my**2 + mz**2 - torsion_limit**2))
    euler, critical, slenderness, method = calc_column_capacity(area, inertia, length, a)
    sf = a.safety_factor
    compression = sf * compression_limit
    stability_ratio = compression / critical
    pressure_limit = max(
        a.oleo_static_pressure_pa, compression_limit / (pi * bore**2 / 4)
    )
    if compression >= euler:
        stress_ratio = inf
    else:
        # Secant amplification bounds both tip-moment and tip-shear amplification
        # for the selected fixed-free prismatic model. No 2%-of-length criterion.
        amplification = 1 / cos(pi / 2 * sqrt(compression / euler))
        eccentricity = a.imperfection_ec_over_rg2 * (inertia / area) / radius
        moment = (sf * bending_limit + compression * eccentricity) * amplification
        normal = sf * abs(axial_limit) / area + moment * radius / inertia
        # 2 V/A bounds solid-to-annular circular-section transverse shear.
        shear = 2 * sf * transverse_limit / area + sf * abs(torsion_limit) * radius / (2 * inertia)
        mechanical_vm = sqrt(normal**2 + 3 * shear**2)
        # Closed-cylinder Lame maximum VM at the bore. Adding VM norms is a
        # conservative upper bound, with no favorable pressure/load cancellation.
        pressure_vm = sqrt(3) * sf * pressure_limit * diameter**2 / (diameter**2 - bore**2)
        # Deliberately require no yield even at factored loads. This is stricter
        # than interpreting the regulatory ultimate requirement as no rupture.
        stress_ratio = (mechanical_vm + pressure_vm) / a.yield_stress_pa
    return CaseCheck(
        case.name, compression_limit, bending_limit, pressure_limit, euler,
        critical, slenderness, method, stress_ratio, stability_ratio,
    )


def calc_leg(geometry, bore, cases, a):
    """Solve outer diameter, with bore fixed by load/pressure, not t/D guessed.

    Mass is explicitly rho*A*L for ONE equivalent carrying cylinder. It is
    a material-model estimate, not the complete shock absorber or gear mass.
    """
    def checks(diameter):
        return tuple(calc_case_check(c, geometry, diameter, bore, a) for c in cases)

    lower = a.minimum_outer_to_bore * bore
    upper = lower
    for _ in range(100):
        if max(check.utilization for check in checks(upper)) <= 1:
            break
        upper *= 1.25  # Numerical bracket expansion, not a physical coefficient.
    else:
        raise ValueError("could not bracket a feasible equivalent-cylinder diameter")
    if upper > lower:
        for _ in range(70):
            middle = (lower + upper) / 2
            if max(check.utilization for check in checks(middle)) > 1:
                lower = middle
            else:
                upper = middle
    area, _ = calc_section(upper, bore)
    return LegResult(
        geometry, bore, upper, (upper - bore) / 2,
        a.density * area * geometry.extended_length, checks(upper),
    )


def calc_empirical_group(mass, coefficients):
    """Torenbeek civil-gear group mass; Strohmayer II PDF p.124, kg."""
    c0, c1, c2, c3 = coefficients
    return HIGH_WING_FACTOR * (c0 + c1 * mass**0.75 + c2 * mass + c3 * mass**1.5)


def calc_concepts(project, a):
    """Scale cylinder mass by its model ratio at one common converged MTOM.

    B = 2 * fuselage cylinder material mass; k = selected / fuselage cylinder
    material mass. The extra mass is B*(k-1); the empirical main/nose groups
    are NOT multiplied by k. Because B comes from the same material model,
    this equals the former direct difference and is not an independent
    calibration. A measured/calibrated B would be required to change scale.
    """
    validate_assumptions(a)
    if any(not isfinite(v) or v <= 0 for v in (
        project.mass, project.gravity, project.wing_area, project.wingspan
    )):
        raise ValueError("project mass, gravity, wing area and span must be positive")
    if a.track >= project.wingspan:
        raise ValueError("wing attachment track must be below the project wingspan")
    weight = project.mass * project.gravity
    sink_speed, stroke = calc_stroke(project, a)
    geometries = calc_geometries(a, stroke)
    # Same nominal piston family in both layouts; Raymer pp.357-358, F=p*A.
    # 90% is used ONLY here for static piston sizing, never on landing reactions.
    bore = sqrt(4 * (a.main_static_fraction * weight / 2) / (pi * a.oleo_static_pressure_pa))
    cases = calc_load_cases(weight, a)
    legs = tuple(calc_leg(geometry, bore, cases, a) for geometry in geometries)
    fuselage_cylinder_pair_mass = 2 * legs[0].equivalent_mass
    concepts = []
    for leg in legs:
        cylinder_mass_ratio = leg.equivalent_mass / legs[0].equivalent_mass
        for gear_type, main, nose in (
            ("fixed", FIXED_MAIN, FIXED_NOSE),
            ("retractable", RETRACT_MAIN, RETRACT_NOSE),
        ):
            concepts.append(Concept(
                mounting=leg.geometry.name,
                gear_type=gear_type,
                baseline_main=calc_empirical_group(project.mass, main),
                baseline_nose=calc_empirical_group(project.mass, nose),
                fuselage_cylinder_pair_mass=fuselage_cylinder_pair_mass,
                cylinder_mass_ratio=cylinder_mass_ratio,
            ))
    # Keep the independent fixed/retractable table consistent with the current
    # shared retractable formula; fail explicitly if the shared formula changes.
    if not isclose(
        concepts[1].total, project.shared_raw_retractable_mass, rel_tol=1e-9, abs_tol=1e-6
    ):
        raise ValueError("shared landing-gear regression changed; review the coefficients in this file")
    return sink_speed, stroke, cases, legs, tuple(concepts)


def load_project(design_path, constraints_path, reference_path, mass_override=None):
    """Read the shared model without invoking its source-file auto-update."""
    with project_imports():
        from aircraft import BatteryAircraft
        from constants import GRAVITY
        from data import SiValue, loader
        from formulas.mass import calc_landing_gear_mass
        from reference_aircraft import load_reference_aircraft

    if mass_override is not None and (not isfinite(mass_override) or mass_override <= 0):
        raise ValueError("--mass must be finite and positive")
    sync = loader._sync_dataclass_fields_in_source
    try:
        loader._sync_dataclass_fields_in_source = lambda cls, keys: False
        design = loader.load_design_parameters(design_path)
        constraints = loader.load_constraints(constraints_path)
        reference = load_reference_aircraft(path=reference_path, design=design)
        override = SiValue(mass_override, "kg") if mass_override is not None else None
        aircraft = BatteryAircraft(constraints, design, reference, mtom=override)
        source = "explicit --mass override (iteration bypassed)"
        if mass_override is None:
            history = aircraft.converge_mtom()
            if (
                len(history) < 2
                or not all(isfinite(value) and value > 0 for value in history)
                or abs(history[-1] - history[-2]) >= 0.1
            ):
                raise ValueError("shared MTOM iteration did not converge within 0.1 kg")
            source = "BatteryAircraft.converge_mtom() -> aircraft.mtom"
        wing = aircraft.wing
        # Explicit numerical boundary: convert shared unit-aware objects once
        # to plain SI scalars for the independent structural mechanics model.
        return ProjectInputs(
            float(aircraft.mtom), float(GRAVITY), float(wing.area), float(wing.span),
            float(constraints.performance.takeOffMassMax.si),
            float(design.initialSizing.maximumTakeOffMass.si),
            float(calc_landing_gear_mass(aircraft.mtom)), float(aircraft.m_landing_gear),
            float(reference.landing_gear_calibration_factor), source,
        )
    finally:
        loader._sync_dataclass_fields_in_source = sync


def print_results(project, assumptions, calculation, paths, verbose=False):
    """Print input provenance, governing checks and all four mass estimates."""
    sink_speed, stroke, cases, legs, concepts = calculation
    print("Conceptual comparison: equivalent cantilever oleo carrying cylinder")
    print(f"MTOM: {project.mass:.2f} kg | wing area: {project.wing_area:.4f} m^2 | span: {project.wingspan:.3f} m")
    print(f"MTOM source: {project.mass_source}")
    print("Wing source: same aircraft.wing -> wing.WingDesign.area/span; read directly.")
    for label, path in zip(("Design", "Constraints", "Reference"), paths):
        print(f"{label}: {path.resolve()}")
    print(f"Iteration seed: {project.initial_mass:.2f} kg | constraint limit: {project.mass_limit:.2f} kg")
    if project.mass > project.mass_limit:
        print("Selected MTOM exceeds the configured project mass limit.")
    print("All concepts use this common MTOM; no new gear mass is fed back into iteration.")
    print("Selected material: normalized 4340; typical supplier properties, not Do228 allowables.")
    print("Geometry below is a layout proposal; only the 1.72 x 2.25 m section is user specified.")
    if verbose:
        for field in fields(assumptions):
            print(f"  {field.name}: {getattr(assumptions, field.name):g}")
    print(f"Descent-speed screen: {sink_speed:.3f} m/s | common vertical stroke: {stroke:.4f} m")
    if verbose:
        print("Limit loads for ONE main wheel (SF not yet applied):")
        for case in cases:
            print(f"  {case.name:30s} Fx={case.fx/1000:8.2f} Fy={case.fy/1000:8.2f} Fz={case.fz/1000:8.2f} kN")
    print("Load arms and buckling length envelope the fully extended position in every case.")
    print("The 3.0 ground factor is selected, not drop-test derived; spin-up uses only the regulatory minimum.")
    print("Ultimate loads = SF * limit loads once; buckling capacity/limit compression >= SF.")
    print("Each equivalent cylinder is checked for factored-load yield and Euler/Johnson stability.")
    print("No prescribed 2%-length deflection, fixed t/D, 3 mm wall or 1.35 mass multiplier.")
    for leg in legs:
        g = leg.geometry
        area, _ = calc_section(leg.diameter, leg.bore)
        print(f"\n{g.name}: static L={g.static_length:.4f} m; extended L={g.extended_length:.4f} m; axial stroke={g.axial_stroke:.4f} m")
        print(f"  bore={leg.bore*1000:.2f} mm; outside D={leg.diameter*1000:.2f} mm; solved wall={leg.wall*1000:.2f} mm")
        print(
            f"  ONE cylinder material mass = rho*A*L = {assumptions.density:g} * "
            f"{area:.7f} * {g.extended_length:.4f} = {leg.equivalent_mass:.2f} kg"
        )
        print(f"  BOTH cylinders: {2*leg.equivalent_mass:.2f} kg (not complete shock absorbers)")
        if verbose:
            for check in leg.checks:
                reserve = check.column_load / check.compression_limit if check.compression_limit > 0 else inf
                print(
                    f"  {check.name:30s} N_limit={check.compression_limit/1000:7.2f} kN; "
                    f"M_limit={check.bending_limit/1000:7.2f} kNm; p_limit={check.pressure_limit/1e6:6.2f} MPa; "
                    f"P_cr={check.column_load/1000:8.2f} kN ({check.column_method}, lambda={check.slenderness:.1f}); "
                    f"P_cr/N_limit={reserve:.2f}; U_stress={check.stress_ratio:.3f}; U_buckle={check.buckling_ratio:.3f}"
                )
        governing = max(leg.checks, key=lambda c: c.utilization)
        print(f"  Governing: {governing.name}; utilization={governing.utilization:.4f}")
        print(f"  Maximum factored stress ratio={max(c.stress_ratio for c in leg.checks):.4f}; buckling ratio={max(c.buckling_ratio for c in leg.checks):.4f}")
    wing_concept = next(c for c in concepts if c.mounting == "high-wing")
    print("\nCylinder proportional scaling (B includes BOTH fuselage cylinders):")
    print(f"  Baseline B = {wing_concept.fuselage_cylinder_pair_mass:.2f} kg, from the material model.")
    print(f"  Ratio k = high-wing/fuselage cylinder material mass = {wing_concept.cylinder_mass_ratio:.6f}")
    print(f"  High-wing cylinder pair B*k = {wing_concept.cylinder_pair_mass:.2f} kg.")
    print(f"  Cylinder increment B*(k-1) = {wing_concept.structural_delta:.2f} kg ({100*(wing_concept.cylinder_mass_ratio-1):.2f}%).")
    print("The same cylinder pair and increment are used for fixed and retractable concepts.")
    print("The empirical main/nose masses and retraction equipment are NOT multiplied by k.")
    print("\nMasses in kg; base main includes BOTH legs. Nose gear is unchanged between mounts.")
    print(f"{'Mount':12s} {'Type':12s} {'Base main':>11s} {'Base nose':>11s} {'Strut delta':>12s} {'Total':>11s}")
    for concept in concepts:
        print(f"{concept.mounting:12s} {concept.gear_type:12s} {concept.baseline_main:11.2f} {concept.baseline_nose:11.2f} {concept.structural_delta:12.2f} {concept.total:11.2f}")
    print("Totals = uncalibrated Torenbeek group masses + B*(k-1), for each mounting.")
    print("Because B comes from the SAME material model, proportional scaling equals the previous mass difference.")
    print("Changing the arithmetic to a ratio does not independently calibrate the material model to the regression.")
    print("This combination remains a project hybrid assumption, not a published Torenbeek correction.")
    print(f"Shared project's calibrated gear budget: {project.shared_calibrated_gear_mass:.2f} kg; reference calibration={project.reference_calibration:.5f}.")
    print("Calibration is reported separately; a retractable Do228 calibration is not validated for fixed gear.")
    print("Retraction difference uses the COMPLETE regression difference, not an added actuator percentage.")
    print("Included change: equivalent main-leg carrying-cylinder material due to geometry and resizing.")
    print("Unresolved: airframe attachment reinforcement, doors/bays, braces, fatigue, local details and gear kinematics.")
    print("Source locations are cited in this file's parameter comments and function docstrings.")


def make_parser():
    """Create the command-line interface without loading the aircraft model."""
    a = Assumptions()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", type=Path, default=ROOT / "config" / "design_parameters.json")
    parser.add_argument("--constraints", type=Path, default=ROOT / "config" / "constraints.json")
    parser.add_argument("--reference", type=Path, default=ROOT / "config" / "reference_aircraft.json")
    parser.add_argument("--mass", type=float, help="optional kg override; default is converged shared MTOM")
    parser.add_argument("--belly-clearance", type=float, default=a.belly_clearance)
    parser.add_argument("--wheel-radius", type=float, default=a.wheel_radius, help="loaded radius, m")
    parser.add_argument("--track", type=float, default=a.track, help="main wheel track, m")
    parser.add_argument("--wing-mount-below-roof", type=float, default=a.wing_mount_below_roof)
    parser.add_argument("--ground-factor", type=float, default=a.ground_reaction_factor)
    parser.add_argument("--safety-factor", type=float, default=a.safety_factor)
    parser.add_argument("--static-pressure-mpa", type=float, default=a.oleo_static_pressure_pa / 1e6)
    parser.add_argument("--verbose", action="store_true", help="show every assumption and ground-load check")
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()
    a = replace(
        Assumptions(), belly_clearance=args.belly_clearance, wheel_radius=args.wheel_radius,
        track=args.track, wing_mount_below_roof=args.wing_mount_below_roof,
        ground_reaction_factor=args.ground_factor, safety_factor=args.safety_factor,
        oleo_static_pressure_pa=args.static_pressure_mpa * 1e6,
    )
    paths = args.design, args.constraints, args.reference
    try:
        validate_assumptions(a)
        project = load_project(*paths, mass_override=args.mass)
        calculation = calc_concepts(project, a)
    except (ValueError, OSError, ImportError, KeyError, TypeError, AttributeError, OverflowError) as error:
        parser.error(str(error))
    print_results(project, a, calculation, paths, verbose=args.verbose)


if __name__ == "__main__":
    main()
