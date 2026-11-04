"""Dataclass definitions for the reference aircraft and its derived properties.

Defines frozen dataclasses representing ``reference_aircraft.json`` sections
as well as ``ReferenceCalculatedValues`` and the top-level ``ReferenceAircraft``.
"""

from dataclasses import dataclass

from data.parameters_data import Parameter


@dataclass(frozen=True)
class ReferenceMassParameters:
    """Component mass breakdown parameters for the reference aircraft."""

    takeOffMassMax: Parameter
    landingMassMax: Parameter
    zeroFuelMassMax: Parameter
    mwe: Parameter
    wing: Parameter
    fuselage: Parameter
    horizontalEmpennage: Parameter
    verticalEmpennage: Parameter
    landingGear: Parameter
    pylons: Parameter
    engine: Parameter
    systems: Parameter
    furnishings: Parameter
    operatorItems: Parameter

    @property
    def empennage(self) -> Parameter:
        """Returns total empennage mass (horizontal + vertical tailplane)."""
        return Parameter(
            value=self.horizontalEmpennage.value + self.verticalEmpennage.value,
            unit=self.horizontalEmpennage.unit,
        )


@dataclass(frozen=True)
class ReferenceDimensionsParameters:
    """Geometric dimension parameters of the reference aircraft."""

    wingArea: Parameter
    wingspan: Parameter
    fuselageLength: Parameter
    fuselageWidth: Parameter
    fuselageHeight: Parameter
    horizontalTailArea: Parameter
    verticalTailArea: Parameter


@dataclass(frozen=True)
class ReferencePerformanceParameters:
    """Cruise performance parameters of the reference aircraft."""

    cruiseSpeedTAS: Parameter
    cruiseAltitude: Parameter


@dataclass(frozen=True)
class ReferenceAssumptionsParameters:
    """Assumed parameters for the reference aircraft (not directly specified in datasheet)."""

    limitLoad: Parameter
    maxTakeOffLiftCoefficient: Parameter
    wingRootThickness: Parameter
    wingSweepHalfChord: Parameter
    wingMassPenaltyFactor: Parameter


@dataclass(frozen=True)
class ReferenceAerodynamicParameters:
    """Aerodynamic performance parameters of the reference aircraft."""

    liftToDragRatioCruise: Parameter
    liftToDragRatioLoiter: Parameter
    maxLandingLiftCoefficient: Parameter


@dataclass(frozen=True)
class ReferencePropulsionParameters:
    """Propulsion and engine power parameters of the reference aircraft."""

    engineTakeOffPower: Parameter
    numberOfEngines: Parameter
    tsfcCruise: Parameter

    @property
    def totalTakeOffPower(self) -> Parameter:
        """Returns total take-off power across all engines."""
        return Parameter(
            value=self.engineTakeOffPower.value * self.numberOfEngines.value,
            unit=self.engineTakeOffPower.unit,
        )


@dataclass(frozen=True)
class ReferenceFuelParameters:
    """Fuel energy density and mission phase fuel masses of the reference aircraft."""

    energyDensity: Parameter
    referenceRange: Parameter
    referenceMass: Parameter
    taxiOutAndTakeOff: Parameter
    climb: Parameter
    cruise: Parameter
    descent: Parameter
    approachLandingAndTaxiIn: Parameter
    reserve: Parameter
    total: Parameter

    @property
    def tripMass(self) -> Parameter:
        """Returns total trip fuel mass across all flight phases (excluding reserve)."""
        return Parameter(
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
    def totalMass(self) -> Parameter:
        """Returns total mission fuel mass including reserve."""
        return Parameter(
            value=self.tripMass.value + self.reserve.value,
            unit=self.cruise.unit,
        )


@dataclass(frozen=True)
class ReferenceCalculatedValues:
    """Values calculated/derived for the reference aircraft (not directly specified in JSON)."""

    aspectRatio: Parameter
    meanAerodynamicChord: Parameter
    structuralWingspan: Parameter
    designDivingSpeed: Parameter
    ultimateLoadFactor: Parameter
    horizontalTailLeverArm: Parameter
    verticalTailLeverArm: Parameter
    horizontalTailVolumeCoefficient: Parameter
    verticalTailVolumeCoefficient: Parameter

    wingEstimatedMass: Parameter
    wingCalibrationFactor: Parameter

    landingGearEstimatedMass: Parameter
    landingGearCalibrationFactor: Parameter

    fuselageEstimatedMass: Parameter
    fuselageCalibrationFactor: Parameter

    empennageEstimatedMass: Parameter
    empennageCalibrationFactor: Parameter

    pylonsEstimatedMass: Parameter
    pylonsCalibrationFactor: Parameter

    systemsEstimatedMass: Parameter
    systemsCalibrationFactor: Parameter


@dataclass(frozen=True)
class ReferenceAircraft:
    """Top-level container for all reference aircraft data and derived values."""

    mass: ReferenceMassParameters
    dimensions: ReferenceDimensionsParameters
    performance: ReferencePerformanceParameters
    assumptions: ReferenceAssumptionsParameters
    aerodynamics: ReferenceAerodynamicParameters
    propulsion: ReferencePropulsionParameters
    fuel: ReferenceFuelParameters
    calculatedValues: ReferenceCalculatedValues

