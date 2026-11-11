"""JSON loaders for target aircraft design constraints, parameters, and reference aircraft data.

Provides ``load_constraints``, ``load_design_parameters``, and ``load_reference_aircraft`` to read
``constraints.json``, ``design_parameters.json``, and ``reference_aircraft.json`` into typed dataclasses.
"""

import dataclasses
import inspect
import json
import re
import warnings
from pathlib import Path
from typing import Any, TypeVar, cast

from data.constraints_data import (
    BatteryConstraints,
    Constraints,
    Cs23Constraints,
    MissionConstraints,
    PayloadConstraints,
    PerformanceConstraints,
)
from data.design_parameters_data import (
    DesignAerodynamicParameters,
    DesignAssumptionsParameters,
    DesignFuselageParameters,
    DesignInitialSizingParameters,
    DesignMissionParameters,
    DesignParameters,
    DesignPropulsionParameters,
)
from data.reference_aircraft_data import (
    ReferenceAerodynamicParameters,
    ReferenceAircraftData,
    ReferenceAssumptionsParameters,
    ReferenceDimensionsParameters,
    ReferenceFuelParameters,
    ReferenceMassParameters,
    ReferenceMissionParameters,
    ReferencePropulsionParameters,
)
from data.unit_value import UnitValue

T = TypeVar("T")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _parameter_group(raw_group: dict[str, Any]) -> dict[str, Any]:
    """Converts a JSON dictionary of ``[value, unit]`` pairs into ``UnitValue`` objects."""
    return {
        key: UnitValue(val[0], val[1])
        if isinstance(val, list) and len(val) == 2
        else val
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


def instantiate_dataclass_with_extra_warning(
    cls: type[T], data: dict[str, UnitValue]
) -> T:
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
    declared_fields = [f.name for f in dataclasses.fields(cast(Any, cls))]
    json_keys = list(data.keys())

    if declared_fields != json_keys:
        added = [k for k in json_keys if k not in declared_fields]
        removed = [k for k in declared_fields if k not in json_keys]
        synced = _sync_dataclass_fields_in_source(cls, json_keys)
        sync_note = (
            "Python dataclass source file updated automatically."
            if synced
            else "Attached dynamically."
        )
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


def _find_constraints_file() -> Path:
    """Resolves the path to ``constraints.json`` in the project root."""
    return _PROJECT_ROOT / "constraints.json"


def _find_design_parameters_file() -> Path:
    """Resolves the path to ``design_parameters.json`` in the project root."""
    return _PROJECT_ROOT / "design_parameters.json"


def _find_reference_file() -> Path:
    """Resolves the path to the reference aircraft JSON file in the project root."""
    return _PROJECT_ROOT / "reference_aircraft.json"


def _load_json_with_comments(file_path: Path) -> dict:
    """Loads a JSON file, stripping single-line (//) and block (/* ... */) comments."""
    content = file_path.read_text(encoding="utf-8")
    pattern = re.compile(r'("(?:\\.|[^"\\])*")|(/\*[\s\S]*?\*/)|(//[^\r\n]*)')
    cleaned = pattern.sub(lambda m: m.group(1) if m.group(1) else "", content)
    cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
    return json.loads(cleaned)


def load_constraints(path: Path | str | None = None) -> Constraints:
    """Loads target aircraft design constraints from ``constraints.json``.

    Args:
        path: Optional explicit path to ``constraints.json``.

    Returns:
        Populated ``Constraints`` dataclass instance.
    """
    file_path = Path(path) if path else _find_constraints_file()
    data = _load_json_with_comments(file_path)

    return Constraints(
        payload=instantiate_dataclass_with_extra_warning(
            PayloadConstraints, _parameter_group(data["payload"])
        ),
        mission=instantiate_dataclass_with_extra_warning(
            MissionConstraints, _parameter_group(data["mission"])
        ),
        performance=instantiate_dataclass_with_extra_warning(
            PerformanceConstraints, _parameter_group(data["performance"])
        ),
        battery=instantiate_dataclass_with_extra_warning(
            BatteryConstraints, _parameter_group(data["battery"])
        ),
        cs23=instantiate_dataclass_with_extra_warning(
            Cs23Constraints, _parameter_group(data["cs23"])
        ),
    )


def load_design_parameters(path: Path | str | None = None) -> DesignParameters:
    """Loads target aircraft design parameters from ``design_parameters.json``.

    Args:
        path: Optional explicit path to ``design_parameters.json``.

    Returns:
        Populated ``DesignParameters`` dataclass instance.
    """
    file_path = Path(path) if path else _find_design_parameters_file()
    data = _load_json_with_comments(file_path)

    return DesignParameters(
        initialSizing=instantiate_dataclass_with_extra_warning(
            DesignInitialSizingParameters, _parameter_group(data["initialSizing"])
        ),
        aerodynamics=instantiate_dataclass_with_extra_warning(
            DesignAerodynamicParameters, _parameter_group(data["aerodynamics"])
        ),
        propulsion=instantiate_dataclass_with_extra_warning(
            DesignPropulsionParameters, _parameter_group(data["propulsion"])
        ),
        fuselage=instantiate_dataclass_with_extra_warning(
            DesignFuselageParameters, _parameter_group(data["fuselage"])
        ),
        mission=instantiate_dataclass_with_extra_warning(
            DesignMissionParameters, _parameter_group(data["mission"])
        ),
        assumptions=instantiate_dataclass_with_extra_warning(
            DesignAssumptionsParameters, _parameter_group(data["assumptions"])
        ),
    )


def load_reference_aircraft_data(
    path: Path | str | None = None,
) -> ReferenceAircraftData:
    """Loads reference aircraft parameters from JSON into a typed ``ReferenceAircraftData`` dataclass.

    Args:
        path: Optional explicit path to the reference aircraft JSON file.

    Returns:
        Populated ``ReferenceAircraftData`` instance.
    """
    file_path = Path(path) if path else _find_reference_file()
    data = _load_json_with_comments(file_path)

    mass = instantiate_dataclass_with_extra_warning(
        ReferenceMassParameters, _parameter_group(data["mass"])
    )
    dimensions = instantiate_dataclass_with_extra_warning(
        ReferenceDimensionsParameters, _parameter_group(data["dimensions"])
    )
    mission = instantiate_dataclass_with_extra_warning(
        ReferenceMissionParameters, _parameter_group(data["mission"])
    )
    assumptions = instantiate_dataclass_with_extra_warning(
        ReferenceAssumptionsParameters, _parameter_group(data["assumptions"])
    )
    aerodynamics = instantiate_dataclass_with_extra_warning(
        ReferenceAerodynamicParameters, _parameter_group(data["aerodynamics"])
    )
    propulsion = instantiate_dataclass_with_extra_warning(
        ReferencePropulsionParameters, _parameter_group(data["propulsion"])
    )
    fuel = instantiate_dataclass_with_extra_warning(
        ReferenceFuelParameters, _parameter_group(data["fuel"])
    )

    return ReferenceAircraftData(
        mass=mass,
        dimensions=dimensions,
        mission=mission,
        assumptions=assumptions,
        aerodynamics=aerodynamics,
        propulsion=propulsion,
        fuel=fuel,
    )
