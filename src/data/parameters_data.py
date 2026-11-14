"""Dataclass definitions and auto-sync utilities for target aircraft parameters.

Defines the unit-aware ``Parameter`` float subclass, auto-sync instantiation helper,
and frozen dataclasses representing ``parameters.json``.
"""

import dataclasses
import inspect
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


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

    _CONVERSIONS: dict[tuple[str, str], float] = {
        # Length
        ("m", "km"): 1e-3,
        ("km", "m"): 1e3,
        ("m", "nm"): 1.0 / 1852.0,
        ("nm", "m"): 1852.0,
        ("km", "nm"): 1.0 / 1.852,
        ("nm", "km"): 1.852,
        ("m", "ft"): 1.0 / 0.3048,
        ("ft", "m"): 0.3048,
        ("km", "ft"): 1e3 / 0.3048,
        ("ft", "km"): 0.3048 / 1e3,
        ("ft", "nm"): 0.3048 / 1852.0,
        ("nm", "ft"): 1852.0 / 0.3048,
        # Speed
        ("kt", "m/s"): 1852.0 / 3600.0,
        ("m/s", "kt"): 3600.0 / 1852.0,
        ("kts", "m/s"): 1852.0 / 3600.0,
        ("m/s", "kts"): 3600.0 / 1852.0,
        ("kt", "km/h"): 1.852,
        ("km/h", "kt"): 1.0 / 1.852,
        ("kts", "km/h"): 1.852,
        ("km/h", "kts"): 1.0 / 1.852,
        ("km/h", "m/s"): 1.0 / 3.6,
        ("m/s", "km/h"): 3.6,
        # Mass
        ("kg", "t"): 1e-3,
        ("t", "kg"): 1e3,
        ("kg", "lb"): 2.20462262185,
        ("lb", "kg"): 1.0 / 2.20462262185,
        ("kg", "lbs"): 2.20462262185,
        ("lbs", "kg"): 1.0 / 2.20462262185,
        # Time
        ("s", "min"): 1.0 / 60.0,
        ("min", "s"): 60.0,
        ("min", "h"): 1.0 / 60.0,
        ("h", "min"): 60.0,
        ("s", "h"): 1.0 / 3600.0,
        ("h", "s"): 3600.0,
        # Power
        ("w", "kw"): 1e-3,
        ("kw", "w"): 1e3,
        ("kw", "mw"): 1e-3,
        ("mw", "kw"): 1e3,
        ("w", "mw"): 1e-6,
        ("mw", "w"): 1e6,
        ("kw", "hp"): 1.0 / 0.745699872,
        ("hp", "kw"): 0.745699872,
        ("w", "hp"): 1.0 / 745.699872,
        ("hp", "w"): 745.699872,
        # Energy
        ("j", "kj"): 1e-3,
        ("kj", "j"): 1e3,
        ("j", "mj"): 1e-6,
        ("mj", "j"): 1e6,
        ("kj", "mj"): 1e-3,
        ("mj", "kj"): 1e3,
        ("j", "wh"): 1.0 / 3600.0,
        ("wh", "j"): 3600.0,
        ("j", "kwh"): 1.0 / 3.6e6,
        ("kwh", "j"): 3.6e6,
        ("wh", "kwh"): 1e-3,
        ("kwh", "wh"): 1e3,
        ("mj", "kwh"): 1.0 / 3.6,
        ("kwh", "mj"): 3.6,
        # Energy Density
        ("wh/kg", "kwh/kg"): 1e-3,
        ("kwh/kg", "wh/kg"): 1e3,
        ("mj/kg", "kwh/kg"): 1.0 / 3.6,
        ("kwh/kg", "mj/kg"): 3.6,
        ("j/kg", "kwh/kg"): 1.0 / 3.6e6,
        ("kwh/kg", "j/kg"): 3.6e6,
        ("j/kg", "mj/kg"): 1e-6,
        ("mj/kg", "j/kg"): 1e6,
        ("wh/kg", "j/kg"): 3600.0,
        ("j/kg", "wh/kg"): 1.0 / 3600.0,
        # Volume
        ("l", "m^3"): 1e-3,
        ("m^3", "l"): 1e3,
        ("liters", "m^3"): 1e-3,
        ("m^3", "liters"): 1e3,
        ("l", "liters"): 1.0,
        ("liters", "l"): 1.0,
        # Pressure
        ("pa", "kpa"): 1e-3,
        ("kpa", "pa"): 1e3,
        ("pa", "bar"): 1e-5,
        ("bar", "pa"): 1e5,
        ("pa", "mbar"): 1e-2,
        ("mbar", "pa"): 1e2,
        ("pa", "hpa"): 1e-2,
        ("hpa", "pa"): 1e2,
        # Fuel consumption (TSFC)
        ("lb/(h*lbf)", "kg/(n*s)"): 1.0 / (3600.0 * 9.80665),
        ("kg/(n*s)", "lb/(h*lbf)"): 3600.0 * 9.80665,
    }

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

    def to(self, target_unit: str) -> "Parameter":
        """Converts the parameter to another compatible physical unit.

        Args:
            target_unit: Target unit string (e.g. 'm', 'km', 'kts', 'kwh', 'degC', 'K').

        Returns:
            A new Parameter instance with the converted value and target_unit.

        Raises:
            ValueError: If conversion between the units is not supported.
        """
        src = self.unit.strip().lower()
        dst = target_unit.strip().lower()

        if src == dst:
            return Parameter(self._raw, target_unit)

        temp_units = {"degc", "c", "k", "degf", "f"}
        if src in temp_units or dst in temp_units:
            return Parameter(self._convert_temperature(float(self._raw), src, dst), target_unit)

        if (src, dst) in self._CONVERSIONS:
            factor = self._CONVERSIONS[(src, dst)]
            return Parameter(float(self._raw) * factor, target_unit)

        for (u1, u2), f1 in self._CONVERSIONS.items():
            if u1 == src and (u2, dst) in self._CONVERSIONS:
                f2 = self._CONVERSIONS[(u2, dst)]
                return Parameter(float(self._raw) * f1 * f2, target_unit)

        raise ValueError(f"Unsupported unit conversion from '{self.unit}' to '{target_unit}'")

    @staticmethod
    def _convert_temperature(val: float, src: str, dst: str) -> float:
        """Converts temperature between degC/C, K, and degF/F."""
        if src in ("degc", "c"):
            k = val + 273.15
        elif src == "k":
            k = val
        elif src in ("degf", "f"):
            k = (val - 32.0) * (5.0 / 9.0) + 273.15
        else:
            raise ValueError(f"Unknown source temperature unit: '{src}'")

        if dst in ("degc", "c"):
            return k - 273.15
        if dst == "k":
            return k
        if dst in ("degf", "f"):
            return (k - 273.15) * 1.8 + 32.0
        raise ValueError(f"Unknown target temperature unit: '{dst}'")

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


def _parameter_group(raw_group: dict[str, list]) -> dict[str, Parameter]:
    """Converts a JSON dictionary of ``[value, unit]`` pairs into ``Parameter`` objects."""
    return {
        key: Parameter(val[0], val[1]) if isinstance(val, list) and len(val) == 2 else val
        for key, val in raw_group.items()
    }


def _sync_dataclass_fields_in_source(cls: type, json_keys: list[str]) -> bool:
    """Updates the ``field: Parameter`` declarations of ``cls`` in its Python source file.

    Preserves class docstrings and any ``@property`` or method definitions on the class.

    Args:
        cls: Dataclass type whose source definition should be updated.
        json_keys: Ordered list of field names from the JSON section.

    Returns:
        ``True`` if the source file was modified, ``False`` otherwise.
    """
    source_file = inspect.getsourcefile(cls)
    if not source_file or not json_keys:
        return False

    path = Path(source_file)
    content = path.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in content else "\n"

    pattern = re.compile(
        rf"(class {re.escape(cls.__name__)}:\r?\n"
        rf'(?:    """.*?"""\r?\n\r?\n)?)'
        rf"((?:    \w+:\s*Parameter\r?\n)+)",
        re.DOTALL,
    )
    new_fields_block = "".join(f"    {key}: Parameter{newline}" for key in json_keys)
    new_content, count = pattern.subn(rf"\g<1>{new_fields_block}", content, count=1)

    if count > 0 and new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def instantiate_dataclass_with_extra_warning(cls: type[T], data: dict[str, Parameter]) -> T:
    """Instantiates a frozen dataclass and auto-syncs its source definition if JSON keys changed.

    If the JSON keys differ from the fields declared on ``cls`` (fields added, removed,
    or reordered), the dataclass definition in the Python source file is automatically
    updated for IDE autocompletion, a ``UserWarning`` is emitted, and all JSON attributes
    are attached dynamically so the current run succeeds without a restart.

    Args:
        cls: Target dataclass type.
        data: Dictionary of parsed ``Parameter`` instances.

    Returns:
        Instantiated dataclass of type ``cls``.
    """
    declared_fields = [f.name for f in dataclasses.fields(cls)]
    json_keys = list(data.keys())

    if declared_fields != json_keys:
        added = [k for k in json_keys if k not in declared_fields]
        removed = [k for k in declared_fields if k not in json_keys]
        synced = _sync_dataclass_fields_in_source(cls, json_keys)
        sync_note = "Python dataclass source file updated automatically." if synced else "Attached dynamically."
        warnings.warn(
            f"{cls.__name__}: JSON keys changed (added={added}, removed={removed}). {sync_note}",
            UserWarning,
            stacklevel=2,
        )
        instance = object.__new__(cls)
        for key, val in data.items():
            object.__setattr__(instance, key, val)
        return instance

    return cls(**data)


@dataclass(frozen=True)
class PayloadParameters:
    """Passenger and luggage payload requirement parameters."""

    numberOfPassengers: Parameter
    weightPerPassenger: Parameter
    maxStructuralPayloadPerPassenger: Parameter
    luggageVolumePerPassenger: Parameter


@dataclass(frozen=True)
class MissionParameters:
    """Mission profile requirement parameters (range, reserves, turnaround)."""

    range: Parameter
    routeReserve: Parameter
    diversionDistance: Parameter
    loiterTime: Parameter
    turnaroundTimeMax: Parameter
    gravity: Parameter


@dataclass(frozen=True)
class PerformanceParameters:
    """Take-off, landing, and cruise performance requirement parameters."""

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
    """Battery cell and pack gravimetric energy density parameters."""

    cellEnergyDensityMax: Parameter
    cellToPackFactorMin: Parameter


@dataclass(frozen=True)
class Parameters:
    """Top-level container for all target aircraft design parameters."""

    payload: PayloadParameters
    mission: MissionParameters
    performance: PerformanceParameters
    battery: BatteryParameters
