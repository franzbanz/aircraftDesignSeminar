"""JSON loaders for target aircraft parameters and reference aircraft data.

Provides ``load_parameters`` and ``load_reference_aircraft`` to read
``parameters.json`` and ``reference_aircraft.json`` into typed dataclasses.
"""

import json
from pathlib import Path

from data.parameters_data import (
    BatteryParameters,
    MissionParameters,
    Parameters,
    PayloadParameters,
    PerformanceParameters,
    _parameter_group,
    instantiate_dataclass_with_extra_warning,
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

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


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

