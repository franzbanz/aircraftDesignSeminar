import json
from dataclasses import dataclass
from pathlib import Path


class Parameter(float):
    _raw: int | float
    unit: str

    def __new__(cls, value: int | float, unit: str):
        obj = float.__new__(cls, value)
        obj._raw = value
        obj.unit = unit
        return obj

    @property
    def value(self) -> int | float:
        return self._raw

    def __str__(self) -> str:
        return f"{self._raw} {self.unit}".strip() if self.unit else str(self._raw)

    def __repr__(self) -> str:
        return f"Parameter({self._raw}, {self.unit!r})"


@dataclass(frozen=True)
class PayloadParameters:
    numberOfPassengers: Parameter
    weightPerPassenger: Parameter
    maxStructuralPayloadPerPassenger: Parameter
    luggageVolumePerPassenger: Parameter


@dataclass(frozen=True)
class MissionParameters:
    range: Parameter
    routeReserve: Parameter
    diversionDistance: Parameter
    loiterTime: Parameter
    turnaroundTimeMax: Parameter


@dataclass(frozen=True)
class PerformanceParameters:
    takeOffFieldLengthMax: Parameter
    landingFieldLengthMax: Parameter
    takeOffMassMax: Parameter
    takeOffAltitude: Parameter
    takeOffTemperature: Parameter
    takeOffPressure: Parameter
    takeOffDensity: Parameter
    cruiseSpeedMin: Parameter


@dataclass(frozen=True)
class BatteryParameters:
    cellEnergyDensityMax: Parameter
    cellToPackFactorMin: Parameter


@dataclass(frozen=True)
class MassReferenceParameters:
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
class Parameters:
    payload: PayloadParameters
    mission: MissionParameters
    performance: PerformanceParameters
    battery: BatteryParameters
    massReferences: MassReferenceParameters | None = None

    @property
    def referenceMasses(self) -> MassReferenceParameters | None:
        return self.massReferences


def _parameter_group(values: dict[str, list[object]]) -> dict[str, Parameter]:
    parameters = {}
    for name, value_and_unit in values.items():
        if (
            len(value_and_unit) != 2
            or not isinstance(value_and_unit[0], (int, float))
            or not isinstance(value_and_unit[1], str)
        ):
            raise ValueError(f"Invalid parameter entry for {name!r}")
        parameters[name] = Parameter(
            value=value_and_unit[0],
            unit=value_and_unit[1],
        )
    return parameters


def load_parameters() -> Parameters:
    """Load parameter values and units into typed, nested Python objects."""
    parameters_path = Path(__file__).parent.parent / "parameters.json"
    with parameters_path.open(encoding="utf-8") as file:
        data = json.load(file)

    mass_ref_data = data.get("massReferences") or data.get("referenceMasses")
    mass_references = (
        MassReferenceParameters(**_parameter_group(mass_ref_data))
        if mass_ref_data is not None
        else None
    )

    return Parameters(
        payload=PayloadParameters(**_parameter_group(data["payload"])),
        mission=MissionParameters(**_parameter_group(data["mission"])),
        performance=PerformanceParameters(**_parameter_group(data["performance"])),
        battery=BatteryParameters(**_parameter_group(data["battery"])),
        massReferences=mass_references,
    )


if __name__ == "__main__":
    parameters = load_parameters()
    print(f"Range: {parameters.mission.range}")
