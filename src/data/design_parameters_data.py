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


@dataclass(frozen=True)
class DesignPropulsionParameters:
    """Propulsion and engine parameters."""

    engineTakeOffPower: UnitValue
    numberOfEngines: UnitValue


@dataclass(frozen=True)
class DesignMissionParameters:
    """Mission distance parameters."""

    cruiseDistance: UnitValue


@dataclass(frozen=True)
class DesignAssumptionsParameters:
    """Structural, geometric, and aerodynamic design assumptions."""

    limitLoad: UnitValue
    maxTakeOffLiftCoefficient: UnitValue
    wingRootThickness: UnitValue
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

