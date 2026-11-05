"""Dataclass definitions representing parameters.json."""

from dataclasses import dataclass

from data.unit_value import UnitValue


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
