"""JSON loaders for target aircraft parameters and reference aircraft data.

Provides ``load_parameters`` and ``load_reference_aircraft`` to read
``parameters.json`` and ``reference_aircraft.json`` into typed dataclasses.
"""

import dataclasses
import inspect
import re
import warnings
from pathlib import Path
from typing import TypeVar

import commentjson as json

from data.parameters_data import (
    BatteryParameters,
    MissionParameters,
    Parameters,
    PayloadParameters,
    PerformanceParameters,
)
from data.reference_aircraft_data import (
    ReferenceAerodynamicParameters,
    ReferenceAircraft,
    ReferenceAssumptionsParameters,
    ReferenceDimensionsParameters,
    ReferenceFuelParameters,
    ReferenceMassParameters,
    ReferencePerformanceParameters,
    ReferencePropulsionParameters,
)
from data.unit_value import UnitValue

T = TypeVar("T")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


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


def _find_parameters_file() -> Path:
    """Resolves the path to ``parameters.json`` in the project root."""
    return _PROJECT_ROOT / "parameters.json"


def _find_reference_file() -> Path:
    """Resolves the path to the reference aircraft JSON file in the project root."""
    for filename in ("reference_aircraft.json", "referenceAircraft.json"):
        path = _PROJECT_ROOT / filename
        if path.exists():
            return path
    return _PROJECT_ROOT / "reference_aircraft.json"


def load_parameters(path: Path | str | None = None) -> Parameters:
    """Loads target aircraft design parameters from ``parameters.json``.

    Args:
        path: Optional explicit path to ``parameters.json``.

    Returns:
        Populated ``Parameters`` dataclass instance.
    """
    file_path = Path(path) if path else _find_parameters_file()
    with file_path.open(encoding="utf-8") as file:
        data = json.load(file)

    return Parameters(
        payload=instantiate_dataclass_with_extra_warning(PayloadParameters, _parameter_group(data["payload"])),
        mission=instantiate_dataclass_with_extra_warning(MissionParameters, _parameter_group(data["mission"])),
        performance=instantiate_dataclass_with_extra_warning(PerformanceParameters, _parameter_group(data["performance"])),
        battery=instantiate_dataclass_with_extra_warning(BatteryParameters, _parameter_group(data["battery"])),
    )


def load_reference_aircraft(
    path: Path | str | None = None,
    r_H: float = 8.8,
    r_V: float = 8.8,
    delta_m_F: float = 0.07,
) -> ReferenceAircraft:
    """Loads reference aircraft parameters from JSON and computes derived ``calculatedValues``.

    Args:
        path: Optional explicit path to the reference aircraft JSON file.
        r_H: Horizontal tail lever arm [m].
        r_V: Vertical tail lever arm [m].
        delta_m_F: Fuselage mass penalty factor [-].

    Returns:
        Populated ``ReferenceAircraft`` instance.
    """
    file_path = Path(path) if path else _find_reference_file()
    with file_path.open(encoding="utf-8") as file:
        data = json.load(file)

    mass = instantiate_dataclass_with_extra_warning(ReferenceMassParameters, _parameter_group(data["mass"]))
    dimensions = instantiate_dataclass_with_extra_warning(ReferenceDimensionsParameters, _parameter_group(data["dimensions"]))
    performance = instantiate_dataclass_with_extra_warning(ReferencePerformanceParameters, _parameter_group(data["performance"]))
    assumptions = instantiate_dataclass_with_extra_warning(ReferenceAssumptionsParameters, _parameter_group(data["assumptions"]))
    aerodynamics = instantiate_dataclass_with_extra_warning(ReferenceAerodynamicParameters, _parameter_group(data["aerodynamics"]))
    propulsion = instantiate_dataclass_with_extra_warning(ReferencePropulsionParameters, _parameter_group(data["propulsion"]))
    fuel = instantiate_dataclass_with_extra_warning(ReferenceFuelParameters, _parameter_group(data["fuel"]))

    from reference_aircraft_calculation import calc_reference_aircraft_values

    calculatedValues = calc_reference_aircraft_values(
        mass=mass,
        dimensions=dimensions,
        performance=performance,
        assumptions=assumptions,
        propulsion=propulsion,
        r_H=r_H,
        r_V=r_V,
        delta_m_F=delta_m_F,
    )

    return ReferenceAircraft(
        mass=mass,
        dimensions=dimensions,
        performance=performance,
        assumptions=assumptions,
        aerodynamics=aerodynamics,
        propulsion=propulsion,
        fuel=fuel,
        calculatedValues=calculatedValues,
    )
