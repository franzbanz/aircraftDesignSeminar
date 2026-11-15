"""Dataclass definitions representing design_parameters.json."""

from dataclasses import dataclass

from data.unit_value import UnitValue


@dataclass(frozen=True)
class DesignInitialSizingParameters:
    """Initial sizing parameters (e.g. maximum take-off mass)."""

    maximumTakeOffMass: UnitValue


@dataclass(frozen=True)
class DesignAerodynamicParameters:
    """Whole-aircraft aerodynamic performance parameters."""

    liftToDragRatioLoiter: UnitValue
    oswaldFactor: UnitValue


@dataclass(frozen=True)
class DesignWingParameters:
    """Wing geometry, high-lift, and mass assumptions."""

    maxTakeOffLiftCoefficient: UnitValue
    maxLandingLiftCoefficient: UnitValue
    aspectRatio: UnitValue
    relWingThickness: UnitValue
    wingSweepHalfChord: UnitValue
    wingMassPenaltyFactor: UnitValue


@dataclass(frozen=True)
class DesignEmpennageParameters:
    """Empennage sizing parameters."""

    maxHorizontalVolumeCoefficient: UnitValue


@dataclass(frozen=True)
class DesignPropulsionParameters:
    """Propulsion and engine parameters."""

    engineTakeOffPower: UnitValue
    engineMaxContinousPower: UnitValue
    engineMass: UnitValue
    numberOfEngines: UnitValue
    etaPropTakeOff: UnitValue
    etaPropClimb: UnitValue
    etaPropCruise: UnitValue
    etaElectric: UnitValue


@dataclass(frozen=True)
class DesignFuselageParameters:
    """Fuselage geometric dimension and cabin layout parameters."""

    seatPitch: UnitValue
    seatWidth: UnitValue
    armrestWidth: UnitValue
    aisleWidth: UnitValue
    wallClearance: UnitValue
    wallThickness: UnitValue
    aisleHeadroom: UnitValue
    floorStructuralDepth: UnitValue
    noseLength: UnitValue
    frontBulkheadClearance: UnitValue
    minBaggageLength: UnitValue
    usableBaggageFactor: UnitValue
    underfloorBaggageHeight: UnitValue
    fuselageMassPenaltyFactor: UnitValue


@dataclass(frozen=True)
class DesignMissionParameters:
    """Mission distance and cruise profile parameters."""

    range: UnitValue
    cruiseSpeedTAS: UnitValue
    cruiseAltitude: UnitValue
    numberOfPassengers: UnitValue


@dataclass(frozen=True)
class DesignAssumptionsParameters:
    """Structural design assumptions."""

    limitLoad: UnitValue


@dataclass(frozen=True)
class DesignParameters:
    """Top-level container for all battery-powered aircraft design parameters."""

    initialSizing: DesignInitialSizingParameters
    aerodynamics: DesignAerodynamicParameters
    wing: DesignWingParameters
    empennage: DesignEmpennageParameters
    propulsion: DesignPropulsionParameters
    fuselage: DesignFuselageParameters
    mission: DesignMissionParameters
    assumptions: DesignAssumptionsParameters
