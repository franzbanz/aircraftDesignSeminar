"""Dataclass definitions representing constraints.json."""

from dataclasses import dataclass

from data.unit_value import UnitValue


@dataclass(frozen=True)
class PayloadConstraints:
    """Passenger and luggage payload requirement constraints."""

    numberOfPassengers: UnitValue
    weightPerPassenger: UnitValue
    maxStructuralPayloadPerPassenger: UnitValue
    luggageVolumePerPassenger: UnitValue


@dataclass(frozen=True)
class MissionConstraints:
    """Mission profile requirement constraints (range, reserves, turnaround)."""

    range: UnitValue
    routeReserve: UnitValue
    diversionDistance: UnitValue
    loiterTime: UnitValue
    turnaroundTimeMax: UnitValue


@dataclass(frozen=True)
class PerformanceConstraints:
    """Take-off, landing, and cruise performance requirement constraints."""

    takeOffFieldLengthMax: UnitValue
    landingFieldLengthMax: UnitValue
    takeOffMassMax: UnitValue
    takeOffAltitude: UnitValue
    cruiseSpeedMin: UnitValue


@dataclass(frozen=True)
class BatteryConstraints:
    """Battery cell and pack gravimetric energy density constraints."""

    cellEnergyDensityMax: UnitValue
    cellToPackFactorMin: UnitValue


@dataclass(frozen=True)
class Cs23Constraints:
    """CS-23 regulatory airworthiness requirement constraints."""

    maxStallSpeed: UnitValue
    minClimbGradient: UnitValue


@dataclass(frozen=True)
class Constraints:
    """Top-level container for all target aircraft design constraints."""

    payload: PayloadConstraints
    mission: MissionConstraints
    performance: PerformanceConstraints
    battery: BatteryConstraints
    cs23: Cs23Constraints

