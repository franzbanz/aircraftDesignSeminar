"""Data package providing JSON loaders and top-level types for parameters and reference aircraft."""

from data.loader import load_parameters, load_reference_aircraft
from data.parameters_data import Parameters
from data.reference_aircraft_data import ReferenceAircraft
from data.unit_value import SiValue, UnitValue

__all__ = [
    "load_parameters",
    "load_reference_aircraft",
    "Parameters",
    "ReferenceAircraft",
    "SiValue",
    "UnitValue",
]
