"""Dataclass definitions for the reference aircraft and its derived properties.

Defines frozen dataclasses representing ``reference_aircraft.json`` sections
as well as ``ReferenceCalculatedValues`` and the top-level ``ReferenceAircraft``.
"""

from dataclasses import dataclass

from data.unit_value import UnitValue


@dataclass(frozen=True)
class ReferenceMassParameters:
    """Component mass breakdown parameters for the reference aircraft."""

    takeOffMassMax: UnitValue
    landingMassMax: UnitValue
    zeroFuelMassMax: UnitValue
    mwe: UnitValue
    wing: UnitValue
    fuselage: UnitValue
    horizontalEmpennage: UnitValue
    verticalEmpennage: UnitValue
    landingGear: UnitValue
    pylons: UnitValue
    engine: UnitValue
    systems: UnitValue
    furnishings: UnitValue
    operatorItems: UnitValue

    @property
    def empennage(self) -> UnitValue:
        """Returns total empennage mass (horizontal + vertical tailplane)."""
        return UnitValue(
            value=self.horizontalEmpennage.value + self.verticalEmpennage.value,
            unit=self.horizontalEmpennage.unit,
        )


@dataclass(frozen=True)
class ReferenceDimensionsParameters:
    """Geometric dimension parameters of the reference aircraft."""

    wingArea: UnitValue
    wingspan: UnitValue
    fuselageLength: UnitValue
    fuselageWidth: UnitValue
    fuselageHeight: UnitValue
    horizontalTailArea: UnitValue
    verticalTailArea: UnitValue


@dataclass(frozen=True)
class ReferenceMissionParameters:
    """Cruise and mission parameters of the reference aircraft."""

    cruiseSpeedTAS: UnitValue
    cruiseAltitude: UnitValue


@dataclass(frozen=True)
class ReferenceAssumptionsParameters:
    """Assumed parameters for the reference aircraft (not directly specified in datasheet)."""

    limitLoad: UnitValue
    maxTakeOffLiftCoefficient: UnitValue
    wingRootThickness: UnitValue
    wingSweepHalfChord: UnitValue
    wingMassPenaltyFactor: UnitValue
    fuselageMassPenaltyFactor: UnitValue
    horizontalTailLeverArm: UnitValue
    verticalTailLeverArm: UnitValue
    wettedSurface: UnitValue


@dataclass(frozen=True)
class ReferenceAerodynamicParameters:
    """Aerodynamic performance parameters of the reference aircraft."""

    liftToDragRatioCruise: UnitValue
    liftToDragRatioLoiter: UnitValue
    maxLandingLiftCoefficient: UnitValue


@dataclass(frozen=True)
class ReferencePropulsionParameters:
    """Propulsion and engine power parameters of the reference aircraft."""

    engineTakeOffPower: UnitValue
    numberOfEngines: UnitValue
    tsfcCruise: UnitValue

    @property
    def totalTakeOffPower(self) -> UnitValue:
        """Returns total take-off power across all engines."""
        return UnitValue(
            value=self.engineTakeOffPower.value * self.numberOfEngines.value,
            unit=self.engineTakeOffPower.unit,
        )


@dataclass(frozen=True)
class ReferenceFuelParameters:
    """Fuel energy density and mission phase fuel masses of the reference aircraft."""

    energyDensity: UnitValue
    referenceRange: UnitValue
    referenceMass: UnitValue
    taxiOutAndTakeOff: UnitValue
    climb: UnitValue
    cruise: UnitValue
    descent: UnitValue
    approachLandingAndTaxiIn: UnitValue
    reserve: UnitValue
    total: UnitValue

    @property
    def tripMass(self) -> UnitValue:
        """Returns total trip fuel mass across all flight phases (excluding reserve)."""
        return UnitValue(
            value=(
                self.taxiOutAndTakeOff.value
                + self.climb.value
                + self.cruise.value
                + self.descent.value
                + self.approachLandingAndTaxiIn.value
            ),
            unit=self.cruise.unit,
        )

    @property
    def totalMass(self) -> UnitValue:
        """Returns total mission fuel mass including reserve."""
        return UnitValue(
            value=self.tripMass.value + self.reserve.value,
            unit=self.cruise.unit,
        )


@dataclass(frozen=True)
class ReferenceCalculatedValues:
    """Values calculated/derived for the reference aircraft (not directly specified in JSON)."""

    aspectRatio: UnitValue
    meanAerodynamicChord: UnitValue
    structuralWingspan: UnitValue
    designDivingSpeed: UnitValue
    ultimateLoadFactor: UnitValue
    horizontalTailLeverArm: UnitValue
    verticalTailLeverArm: UnitValue
    horizontalTailVolumeCoefficient: UnitValue
    verticalTailVolumeCoefficient: UnitValue

    wingEstimatedMass: UnitValue
    wingCalibrationFactor: UnitValue

    landingGearEstimatedMass: UnitValue
    landingGearCalibrationFactor: UnitValue

    fuselageEstimatedMass: UnitValue
    fuselageCalibrationFactor: UnitValue

    empennageEstimatedMass: UnitValue
    empennageCalibrationFactor: UnitValue

    pylonsEstimatedMass: UnitValue
    pylonsCalibrationFactor: UnitValue

    systemsEstimatedMass: UnitValue
    systemsCalibrationFactor: UnitValue


@dataclass(frozen=True)
class ReferenceAircraft:
    """Top-level container for all reference aircraft data and derived values."""

    mass: ReferenceMassParameters
    dimensions: ReferenceDimensionsParameters
    mission: ReferenceMissionParameters
    assumptions: ReferenceAssumptionsParameters
    aerodynamics: ReferenceAerodynamicParameters
    propulsion: ReferencePropulsionParameters
    fuel: ReferenceFuelParameters
    calculatedValues: ReferenceCalculatedValues

