"""Mission and design requirement parameter loader.

Loads target aircraft requirements and design parameters from parameters.json
into typed Python dataclasses with unit-aware Parameter values.
"""

import json
from dataclasses import dataclass
from pathlib import Path


class Parameter(float):
    """Numeric parameter value with an associated physical unit.

    Subclasses ``float`` so instances can be used directly in standard arithmetic
    expressions while preserving the original raw value and physical unit string.

    Attributes:
        _raw: Original numeric value (int or float) as loaded from JSON.
        unit: Physical unit string (e.g., ``"kg"``, ``"m"``, ``""``).
    """

    _raw: int | float
    unit: str

    def __new__(cls, value: int | float, unit: str):
        """Creates a new Parameter instance with a numeric value and unit.

        Args:
            value: Numeric value of the parameter.
            unit: Physical unit string associated with the value.
        """
        obj = float.__new__(cls, value)
        obj._raw = value
        obj.unit = unit
        return obj

    @property
    def value(self) -> int | float:
        """Returns the original numeric value without unit formatting."""
        return self._raw

    def __str__(self) -> str:
        """Returns a formatted string combining the value and unit (e.g., ``'8618 kg'``)."""
        return f"{self._raw} {self.unit}".strip() if self.unit else str(self._raw)

    def __repr__(self) -> str:
        """Returns the unambiguous developer representation of the Parameter."""
        return f"Parameter({self._raw}, {self.unit!r})"


@dataclass(frozen=True)
class PayloadParameters:
    """Payload and passenger specification parameters."""

    numberOfPassengers: Parameter
    weightPerPassenger: Parameter
    maxStructuralPayloadPerPassenger: Parameter
    luggageVolumePerPassenger: Parameter


@dataclass(frozen=True)
class MissionParameters:
    """Mission profile, range, reserve, and turnaround parameters."""

    range: Parameter
    routeReserve: Parameter
    diversionDistance: Parameter
    loiterTime: Parameter
    turnaroundTimeMax: Parameter


@dataclass(frozen=True)
class PerformanceParameters:
    """Take-off, landing, atmospheric, and cruise performance requirements."""

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
    """Battery cell energy density and packaging parameters."""

    cellEnergyDensityMax: Parameter
    cellToPackFactorMin: Parameter


@dataclass(frozen=True)
class Parameters:
    """Top-level container for all design requirement parameters from parameters.json."""

    payload: PayloadParameters
    mission: MissionParameters
    performance: PerformanceParameters
    battery: BatteryParameters


def _parameter_group(values: dict[str, list[object]]) -> dict[str, Parameter]:
    """Converts a raw JSON dictionary of ``[value, unit]`` pairs into Parameter objects.

    Args:
        values: Mapping of parameter names to two-element ``[numeric_value, unit_str]`` lists.

    Returns:
        Dictionary mapping parameter names to initialized Parameter instances.

    Raises:
        ValueError: If any entry is not a valid ``[int | float, str]`` pair.
    """
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
    """Loads parameter values and units from parameters.json into typed, nested Python objects."""
    parameters_path = Path(__file__).parent.parent / "parameters.json"
    with parameters_path.open(encoding="utf-8") as file:
        data = json.load(file)

    return Parameters(
        payload=PayloadParameters(**_parameter_group(data["payload"])),
        mission=MissionParameters(**_parameter_group(data["mission"])),
        performance=PerformanceParameters(**_parameter_group(data["performance"])),
        battery=BatteryParameters(**_parameter_group(data["battery"])),
    )


if __name__ == "__main__":
    parameters = load_parameters()
    print(f"Range: {parameters.mission.range}")
