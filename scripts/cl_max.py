"""Invert the project's takeoff, landing-distance and stall constraints.

Run from the project root:
    python scripts/cl_max.py

The default wing area and takeoff mass come from the project aircraft model.
Use --wing-area to evaluate a separately selected reference area.
"""

from __future__ import annotations

import __future__
import argparse
import sys
import typing
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.machinery import PathFinder, SourceFileLoader
from math import isfinite, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "src"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))


class ProjectSourceLoader(SourceFileLoader):
    """Postpone project type annotations when importing from this script."""

    def get_code(self, fullname):
        filename = self.get_filename(fullname)
        return compile(
            self.get_data(filename),
            filename,
            "exec",
            flags=__future__.annotations.compiler_flag,
            dont_inherit=True,
        )


class ProjectSourceFinder:
    def find_spec(self, fullname, path=None, target=None):
        spec = PathFinder.find_spec(fullname, path, target)
        if (
            spec is not None
            and isinstance(spec.loader, SourceFileLoader)
            and Path(spec.origin).resolve().is_relative_to(SOURCE_DIR)
        ):
            spec.loader = ProjectSourceLoader(fullname, spec.origin)
            return spec
        return None


@contextmanager
def project_imports():
    """Scope the legacy Python annotation compatibility to project imports."""
    finder = ProjectSourceFinder()
    needs_self = not hasattr(typing, "Self")
    if needs_self:
        typing.Self = typing.TypeVar("Self")
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        if needs_self:
            del typing.Self


with project_imports():
    from constants import GRAVITY, RHO_0, isa_density

# Coefficients from sizing_diagram.py. Kept here so the requirement
# calculation remains independent of how the reference wing area was obtained.
TAKEOFF_FACTORS = {2: 2.45, 3: 2.26, 4: 2.06}
TAKEOFF_SAFETY_SPEED_RATIO = 1.2
LANDING_AIR_DISTANCE_M = 183.0
LANDING_DISTANCE_FACTOR = 0.51  # Wheel-braking factor A = 1.0.


@dataclass(frozen=True)
class LiftRequirements:
    takeoff_field_length: float
    landing_field_length: float
    landing_stall_speed: float

    @property
    def landing_governing(self) -> float:
        return max(self.landing_field_length, self.landing_stall_speed)


def required_cl_max(
    mass_kg: float, area_m2: float, speed_mps: float, rho: float
) -> float:
    """Return the aircraft lift coefficient needed for a 1-g stall limit."""
    return 2 * mass_kg * GRAVITY / (rho * area_m2 * speed_mps**2)


def calculate_requirements(
    *,
    wing_area_m2: float,
    takeoff_mass_kg: float,
    landing_mass_kg: float,
    airfield_density: float,
    takeoff_field_length_m: float,
    landing_field_length_m: float,
    stall_speed_mps: float,
    engine_count: float,
    engine_takeoff_power_w: float,
    takeoff_propeller_efficiency: float,
) -> LiftRequirements:
    """Return three lower bounds on the aircraft lift coefficients."""
    positive_inputs = {
        "wing area": wing_area_m2,
        "takeoff mass": takeoff_mass_kg,
        "landing mass": landing_mass_kg,
        "airfield density": airfield_density,
        "takeoff field length": takeoff_field_length_m,
        "landing field length": landing_field_length_m,
        "stall speed": stall_speed_mps,
        "takeoff power per motor": engine_takeoff_power_w,
    }
    for name, value in positive_inputs.items():
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if not 0 < takeoff_propeller_efficiency <= 1:
        raise ValueError("takeoff propeller efficiency must be in (0, 1]")
    if landing_mass_kg > takeoff_mass_kg:
        raise ValueError("landing mass must not exceed takeoff mass")
    if engine_count not in TAKEOFF_FACTORS:
        raise ValueError("the project takeoff model defines factors for 2, 3 or 4 motors")
    if landing_field_length_m <= LANDING_AIR_DISTANCE_M:
        raise ValueError("landing field length must exceed the model's 183 m air segment")

    density_ratio = airfield_density / RHO_0
    takeoff_wing_loading = takeoff_mass_kg / wing_area_m2
    landing_wing_loading = landing_mass_kg / wing_area_m2

    # In the matching chart, T/W scales as CL_max^(-1) and V2 as
    # CL_max^(-1/2). With P/m = (T/W) * g * V2 / eta, invert at rated power.
    thrust_loading_at_unit_cl = (
        TAKEOFF_FACTORS[engine_count] * takeoff_wing_loading
        / (density_ratio * takeoff_field_length_m)
    )
    safety_speed_at_unit_cl = TAKEOFF_SAFETY_SPEED_RATIO * sqrt(
        2 * GRAVITY * takeoff_wing_loading / airfield_density
    )
    required_power_loading_at_unit_cl = (
        thrust_loading_at_unit_cl * GRAVITY * safety_speed_at_unit_cl
        / takeoff_propeller_efficiency
    )
    available_power_loading = engine_count * engine_takeoff_power_w / takeoff_mass_kg
    takeoff_cl = (required_power_loading_at_unit_cl / available_power_loading) ** (2 / 3)

    # Same as inverting the matching chart's landing relation with
    # mlw_ratio = takeoff_mass / landing_mass.
    landing_distance_cl = (
        LANDING_DISTANCE_FACTOR * GRAVITY * landing_wing_loading
        / ((landing_field_length_m - LANDING_AIR_DISTANCE_M) * density_ratio)
    )
    landing_stall_cl = required_cl_max(
        landing_mass_kg, wing_area_m2, stall_speed_mps, RHO_0
    )
    return LiftRequirements(takeoff_cl, landing_distance_cl, landing_stall_cl)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--wing-area", type=float, help="override the project reference wing area, m^2"
    )
    design_files = parser.add_mutually_exclusive_group()
    design_files.add_argument("--design", type=Path, help="custom design JSON")
    design_files.add_argument("--baseline", action="store_true", help="use baseline design JSON")
    parser.add_argument(
        "--constraints", type=Path, default=ROOT / "config" / "constraints.json"
    )
    parser.add_argument(
        "--takeoff-mass", type=float, help="override the converged project takeoff mass, kg"
    )
    parser.add_argument(
        "--landing-mass", type=float, help="landing mass, kg; defaults to takeoff mass"
    )
    args = parser.parse_args()

    design_name = (
        "design_parameters_baseline.json" if args.baseline else "design_parameters.json"
    )
    try:
        with project_imports():
            from aircraft import BatteryAircraft
            from data import SiValue, loader
            from reference_aircraft import load_reference_aircraft

        # The shared loader can synchronize dataclass source files. Keep this
        # entry point read-only even when configuration keys change.
        sync_fields = loader._sync_dataclass_fields_in_source
        try:
            loader._sync_dataclass_fields_in_source = lambda cls, keys: False
            design = loader.load_design_parameters(
                args.design or ROOT / "config" / design_name
            )
            constraints = loader.load_constraints(args.constraints)
            reference = load_reference_aircraft(design=design)
        finally:
            loader._sync_dataclass_fields_in_source = sync_fields

        if args.takeoff_mass is not None and (
            not isfinite(args.takeoff_mass) or args.takeoff_mass <= 0
        ):
            raise ValueError("takeoff mass must be finite and positive")
        mass_override = (
            SiValue(args.takeoff_mass, "kg") if args.takeoff_mass is not None else None
        )
        aircraft = BatteryAircraft(constraints, design, reference, mtom=mass_override)
        if mass_override is None:
            aircraft.converge_mtom()
        takeoff_mass = float(aircraft.mtom)
        wing_area = args.wing_area if args.wing_area is not None else float(aircraft.wing.area)
        landing_mass = args.landing_mass if args.landing_mass is not None else takeoff_mass
        performance = constraints.performance
        propulsion = design.propulsion
        airfield_altitude = performance.takeOffAltitude.si
        if not isfinite(airfield_altitude) or airfield_altitude > 11_000:
            raise ValueError("the project ISA model requires a finite altitude <= 11000 m")
        results = calculate_requirements(
            wing_area_m2=wing_area,
            takeoff_mass_kg=takeoff_mass,
            landing_mass_kg=landing_mass,
            airfield_density=isa_density(airfield_altitude),
            takeoff_field_length_m=performance.takeOffFieldLengthMax.si,
            landing_field_length_m=performance.landingFieldLengthMax.si,
            stall_speed_mps=constraints.cs23.maxStallSpeed.si,
            engine_count=propulsion.numberOfEngines.si,
            engine_takeoff_power_w=propulsion.engineTakeOffPower.si,
            takeoff_propeller_efficiency=propulsion.etaPropTakeOff.si,
        )
    except ImportError as error:
        parser.error(f"could not import the project aircraft model: {error}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))

    area_source = "manual override" if args.wing_area is not None else "project wing model"
    mass_source = "manual override" if mass_override is not None else "project mass iteration"
    print(
        f"Wing area: {wing_area:g} m^2 ({area_source}) | "
        f"Takeoff mass: {takeoff_mass:g} kg ({mass_source}) | "
        f"Landing mass: {landing_mass:g} kg | Airfield altitude: {airfield_altitude:g} m"
    )
    mass_limit = performance.takeOffMassMax.si
    if takeoff_mass > mass_limit:
        print(f"Takeoff mass exceeds the project limit of {mass_limit:g} kg.")
    print(f"Required takeoff CL_max (field length):        {results.takeoff_field_length:.3f}")
    print(f"Required landing CL_max (field length):        {results.landing_field_length:.3f}")
    print(f"Required landing CL_max (sea-level stall):      {results.landing_stall_speed:.3f}")
    print(f"Governing required landing CL_max:             {results.landing_governing:.3f}")


if __name__ == "__main__":
    main()
