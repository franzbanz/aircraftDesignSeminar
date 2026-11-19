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

    liftToDragRatioCruise: UnitValue | str | None
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
    bendingReliefFactor: UnitValue
    technologyFactor: UnitValue
    leadingEdgeMeanAerodynamicChordPosition: UnitValue
    batteryLeadingEdgeOffset: UnitValue


@dataclass(frozen=True)
class DesignEmpennageParameters:
    """Empennage sizing parameters."""

    massMethod: str
    maxHorizontalVolumeCoefficient: UnitValue
    technologyFactor: UnitValue
    horizontalTailAspectRatio: UnitValue
    verticalTailAspectRatio: UnitValue


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
    engineLeadingEdgeOffset: UnitValue
    pylonLeadingEdgeOffset: UnitValue


@dataclass(frozen=True)
class DesignFuselageParameters:
    """Fuselage geometric dimension and cabin layout parameters."""

    cabinLayout: str
    seatPitch: UnitValue
    seatWidth: UnitValue
    aisleWidth: UnitValue
    wallClearance: UnitValue
    wallThickness: UnitValue
    aisleHeadroom: UnitValue
    floorStructuralDepth: UnitValue
    noseLength: UnitValue
    frontClearance: UnitValue
    minBaggageLength: UnitValue
    usableBaggageFactor: UnitValue
    underfloorBaggageHeight: UnitValue
    forwardBaggageVolume: UnitValue
    forwardBaggagePosition: UnitValue
    crewPosition: UnitValue
    wettedArea: UnitValue | None
    fuselageMassPenaltyFactor: UnitValue
    technologyFactor: UnitValue


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
class DesignLandingGearParameters:
    """Landing gear longitudinal CG station parameters."""

    noseGearPosition: UnitValue
    mainGearPosition: UnitValue


@dataclass(frozen=True)
class DesignParameters:
    """Top-level container for all battery-powered aircraft design parameters."""

    initialSizing: DesignInitialSizingParameters
    aerodynamics: DesignAerodynamicParameters
    wing: DesignWingParameters
    empennage: DesignEmpennageParameters
    propulsion: DesignPropulsionParameters
    fuselage: DesignFuselageParameters
    landingGear: DesignLandingGearParameters
    mission: DesignMissionParameters
    assumptions: DesignAssumptionsParameters
