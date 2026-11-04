"""Dataclass definitions and auto-sync utilities for target aircraft parameters.

Defines the auto-sync instantiation helper and frozen dataclasses representing ``parameters.json``.
"""

import dataclasses
import inspect
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from data.unit_value import UnitValue

T = TypeVar("T")


def _parameter_group(raw_group: dict[str, list]) -> dict[str, UnitValue]:
    """Converts a JSON dictionary of ``[value, unit]`` pairs into ``UnitValue`` objects."""
    return {
        key: UnitValue(val[0], val[1]) if isinstance(val, list) and len(val) == 2 else val
        for key, val in raw_group.items()
    }


def _sync_dataclass_fields_in_source(cls: type, json_keys: list[str]) -> bool:
    """Updates the ``field: UnitValue`` declarations of ``cls`` in its Python source file.

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
        rf"((?:    \w+:\s*(?:UnitValue|Parameter)\r?\n)+)",
        re.DOTALL,
    )
    new_fields_block = "".join(f"    {key}: UnitValue{newline}" for key in json_keys)
    new_content, count = pattern.subn(rf"\g<1>{new_fields_block}", content, count=1)

    if count > 0 and new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def instantiate_dataclass_with_extra_warning(cls: type[T], data: dict[str, UnitValue]) -> T:
    """Instantiates a frozen dataclass and auto-syncs its source definition if JSON keys changed.

    If the JSON keys differ from the fields declared on ``cls`` (fields added, removed,
    or reordered), the dataclass definition in the Python source file is automatically
    updated for IDE autocompletion, a ``UserWarning`` is emitted, and all JSON attributes
    are attached dynamically so the current run succeeds without a restart.

    Args:
        cls: Target dataclass type.
        data: Dictionary of parsed ``UnitValue`` instances.

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

    numberOfPassengers: UnitValue
    weightPerPassenger: UnitValue
    maxStructuralPayloadPerPassenger: UnitValue
    luggageVolumePerPassenger: UnitValue


@dataclass(frozen=True)
class MissionParameters:
    """Mission profile requirement parameters (range, reserves, turnaround)."""

    range: UnitValue
    routeReserve: UnitValue
    diversionDistance: UnitValue
    loiterTime: UnitValue
    turnaroundTimeMax: UnitValue
    gravity: UnitValue


@dataclass(frozen=True)
class PerformanceParameters:
    """Take-off, landing, and cruise performance requirement parameters."""

    takeOffFieldLengthMax: UnitValue
    landingFieldLengthMax: UnitValue
    takeOffMassMax: UnitValue
    takeOffAltitude: UnitValue
    takeOffTemperature: UnitValue
    takeOffPressure: UnitValue
    takeOffDensity: UnitValue
    cruiseSpeedMin: UnitValue


@dataclass(frozen=True)
class BatteryParameters:
    """Battery cell and pack gravimetric energy density parameters."""

    cellEnergyDensityMax: UnitValue
    cellToPackFactorMin: UnitValue


@dataclass(frozen=True)
class Parameters:
    """Top-level container for all target aircraft design parameters."""

    payload: PayloadParameters
    mission: MissionParameters
    performance: PerformanceParameters
    battery: BatteryParameters
