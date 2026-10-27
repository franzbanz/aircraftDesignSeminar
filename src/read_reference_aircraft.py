import json
from dataclasses import dataclass
from pathlib import Path

from read_parameters import Parameter, _parameter_group


@dataclass(frozen=True)
class ReferenceMassParameters:
    takeOffMass: Parameter
    wing: Parameter
    fuselage: Parameter
    horizontalEmpennage: Parameter
    verticalEmpennage: Parameter
    landingGear: Parameter
    pylons: Parameter
    engine: Parameter
    systems: Parameter
    furnishings: Parameter
    operatorItems: Parameter

    @property
    def empennage(self) -> Parameter:
        return Parameter(
            value=self.horizontalEmpennage.value + self.verticalEmpennage.value,
            unit=self.horizontalEmpennage.unit,
        )

    @property
    def mtom(self) -> Parameter:
        return self.takeOffMass


@dataclass(frozen=True)
class ReferenceDimensionsParameters:
    wingArea: Parameter
    wingspan: Parameter
    fuselageLength: Parameter
    fuselageHeight: Parameter
    horizontalTailArea: Parameter
    verticalTailArea: Parameter


@dataclass(frozen=True)
class ReferenceFlightLoadsParameters:
    ultimateLoadFactor: Parameter


@dataclass(frozen=True)
class ReferenceAerodynamicParameters:
    liftToDragRatioCruise: Parameter
    maxTakeOffLiftCoefficient: Parameter
    maxLandingLiftCoefficient: Parameter

    @property
    def liftToDragRatio(self) -> Parameter:
        return self.liftToDragRatioCruise

    @property
    def L_D(self) -> Parameter:
        return self.liftToDragRatioCruise

    @property
    def CA_MAX_TO(self) -> Parameter:
        return self.maxTakeOffLiftCoefficient

    @property
    def CA_MAX_LDG(self) -> Parameter:
        return self.maxLandingLiftCoefficient


@dataclass(frozen=True)
class ReferencePropulsionParameters:
    engineTakeOffPower: Parameter
    numberOfEngines: Parameter

    @property
    def totalTakeOffPower(self) -> Parameter:
        return Parameter(
            value=self.engineTakeOffPower.value * self.numberOfEngines.value,
            unit=self.engineTakeOffPower.unit,
        )


@dataclass(frozen=True)
class ReferenceAircraft:
    mass: ReferenceMassParameters
    dimensions: ReferenceDimensionsParameters
    flightLoads: ReferenceFlightLoadsParameters
    aerodynamics: ReferenceAerodynamicParameters
    propulsion: ReferencePropulsionParameters


def _find_reference_file() -> Path:
    base_dir = Path(__file__).parent.parent
    for filename in ("reference_aircraft.json", "referenceAircraft.json"):
        path = base_dir / filename
        if path.exists():
            return path
    return base_dir / "reference_aircraft.json"


def load_reference_aircraft(path: Path | str | None = None) -> ReferenceAircraft:
    """Load reference aircraft parameter values and units into typed Python objects."""
    file_path = Path(path) if path else _find_reference_file()
    with file_path.open(encoding="utf-8") as file:
        data = json.load(file)

    return ReferenceAircraft(
        mass=ReferenceMassParameters(**_parameter_group(data["mass"])),
        dimensions=ReferenceDimensionsParameters(**_parameter_group(data["dimensions"])),
        flightLoads=ReferenceFlightLoadsParameters(**_parameter_group(data["flightLoads"])),
        aerodynamics=ReferenceAerodynamicParameters(**_parameter_group(data["aerodynamics"])),
        propulsion=ReferencePropulsionParameters(**_parameter_group(data["propulsion"])),
    )


if __name__ == "__main__":
    ref = load_reference_aircraft()
    print(f"Reference MTOM: {ref.mass.takeOffMass}")
    print(f"Wing area: {ref.dimensions.wingArea}")
    print(f"Wingspan: {ref.dimensions.wingspan}")
    print(f"Fuselage length: {ref.dimensions.fuselageLength}")
    print(f"Fuselage height: {ref.dimensions.fuselageHeight}")
    print(f"Horizontal tail area: {ref.dimensions.horizontalTailArea}")
    print(f"Vertical tail area: {ref.dimensions.verticalTailArea}")
    print(f"Ultimate load factor: {ref.flightLoads.ultimateLoadFactor}")
