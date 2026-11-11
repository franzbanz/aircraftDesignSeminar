"""Dataclass definitions representing design_parameters.json."""

from dataclasses import dataclass

from data.unit_value import UnitValue


@dataclass(frozen=True)
class DesignInitialSizingParameters:
    """Initial sizing parameters (e.g. maximum take-off mass)."""

    maximumTakeOffMass: UnitValue


@dataclass(frozen=True)
class DesignAerodynamicParameters:
    """Aerodynamic parameters and lift coefficients."""

    liftToDragRatioLoiter: UnitValue
    maxLandingLiftCoefficient: UnitValue
    aspectRatio: UnitValue
    oswaldFactor: UnitValue
    maxWingSpan: UnitValue
    relWingThickness: UnitValue
    maxHorizontalVolumeCoefficient: UnitValue


@dataclass(frozen=True)
class DesignPropulsionParameters:
    """Propulsion and engine parameters."""

    engineTakeOffPower: UnitValue
    engineMaxContinousPower: UnitValue
    engineMass: UnitValue
    numberOfEngines: UnitValue
    maxThrustOverCruiseThrustRatio: UnitValue
    etaElectric: UnitValue


@dataclass(frozen=True)
class DesignFuselageParameters:
    """Fuselage geometric dimension parameters."""

    fuselageLength: UnitValue
    fuselageWidth: UnitValue
    fuselageHeight: UnitValue


@dataclass(frozen=True)
class DesignMissionParameters:
    """Mission distance and cruise profile parameters."""

    range: UnitValue
    cruiseSpeedTAS: UnitValue
    cruiseAltitude: UnitValue
    numberOfPassengers: UnitValue


@dataclass(frozen=True)
class DesignAssumptionsParameters:
    """Structural, geometric, and aerodynamic design assumptions."""

    limitLoad: UnitValue
    maxTakeOffLiftCoefficient: UnitValue
    wingSweepHalfChord: UnitValue
    wingMassPenaltyFactor: UnitValue


@dataclass(frozen=True)
class DesignParameters:
    """Top-level container for all battery-powered aircraft design parameters."""

    initialSizing: DesignInitialSizingParameters
    aerodynamics: DesignAerodynamicParameters
    propulsion: DesignPropulsionParameters
    fuselage: DesignFuselageParameters
    mission: DesignMissionParameters
    assumptions: DesignAssumptionsParameters
