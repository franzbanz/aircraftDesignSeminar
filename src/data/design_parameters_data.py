"""Dataclass definitions representing design_parameters.json."""

from dataclasses import dataclass

from data.unit_value import UnitValue


@dataclass(frozen=True)
class DesignInitialSizingParameters:
    """Initial sizing parameters (e.g. maximum take-off mass)."""

    maximumTakeOffMass: UnitValue


@dataclass(frozen=True)
class DesignPerformanceParameters:
    """Flight performance parameters (cruise speed, altitude)."""

    cruiseSpeedTAS: UnitValue
    cruiseAltitude: UnitValue


@dataclass(frozen=True)
class DesignAerodynamicParameters:
    """Aerodynamic parameters and lift coefficients."""

    liftToDragRatioCruise: UnitValue
    liftToDragRatioLoiter: UnitValue
    maxLandingLiftCoefficient: UnitValue
    aspectRatio: UnitValue
    oswaldFactor: UnitValue
    maxWingSpan: UnitValue
    relWingThickness: UnitValue


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
class DesignMissionParameters:
    """Mission distance parameters."""

    range: UnitValue


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
    performance: DesignPerformanceParameters
    aerodynamics: DesignAerodynamicParameters
    propulsion: DesignPropulsionParameters
    mission: DesignMissionParameters
    assumptions: DesignAssumptionsParameters

