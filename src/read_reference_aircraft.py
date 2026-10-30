"""Reference aircraft parameter loader and derived properties calculator.

Loads values from reference_aircraft.json and computes derived geometry,
tail volume coefficients, formula mass estimates, and calibration factors,
storing them under `calculatedValues`.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path

from mass_formulas import (
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_horizontal_tail_volume_coefficient,
    calc_landing_gear_mass,
    calc_mean_aerodynamic_chord,
    calc_pylons_mass,
    calc_systems_mass,
    calc_vertical_tail_volume_coefficient,
    calc_wing_mass,
)
from read_parameters import Parameter, _parameter_group


@dataclass(frozen=True)
class ReferenceMassParameters:
    """Component mass breakdown parameters for the reference aircraft."""

    takeOffMassMax: Parameter
    landingMassMax: Parameter
    zeroFuelMassMax: Parameter
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

    @property
    def mtom(self) -> Parameter:
        """Alias for maximum take-off mass (takeOffMassMax)."""
        return self.takeOffMassMax

    @property
    def mlm(self) -> Parameter:
        """Alias for maximum landing mass (landingMassMax)."""
        return self.landingMassMax

    @property
    def mzfm(self) -> Parameter:
        """Alias for maximum zero-fuel mass (zeroFuelMassMax)."""
        return self.zeroFuelMassMax


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

    @property
    def CA_MAX_TO(self) -> Parameter:
        """Short alias for maximum take-off lift coefficient."""
        return self.maxTakeOffLiftCoefficient

    @property
    def d_root(self) -> Parameter:
        """Short alias for wing root thickness."""
        return self.wingRootThickness

    @property
    def phi_50(self) -> Parameter:
        """Short alias for mid-chord wing sweep angle."""
        return self.wingSweepHalfChord


@dataclass(frozen=True)
class ReferenceAerodynamicParameters:
    """Aerodynamic performance parameters of the reference aircraft."""

    liftToDragRatioCruise: Parameter
    maxLandingLiftCoefficient: Parameter

    @property
    def liftToDragRatio(self) -> Parameter:
        """Alias for cruise lift-to-drag ratio."""
        return self.liftToDragRatioCruise

    @property
    def L_D(self) -> Parameter:
        """Short alias L/D for cruise lift-to-drag ratio."""
        return self.liftToDragRatioCruise

    @property
    def CA_MAX_LDG(self) -> Parameter:
        """Short alias for maximum landing lift coefficient."""
        return self.maxLandingLiftCoefficient


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
    taxiOutAndTakeOff: Parameter
    climb: Parameter
    cruise: Parameter
    descent: Parameter
    approachLandingAndTaxiIn: Parameter

    @property
    def totalMass(self) -> Parameter:
        """Returns total mission fuel mass across all flight phases."""
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

    # Convenient aliases
    @property
    def AR(self) -> Parameter:
        """Short alias for wing aspect ratio."""
        return self.aspectRatio

    @property
    def c_mu(self) -> Parameter:
        """Short alias for mean aerodynamic chord."""
        return self.meanAerodynamicChord

    @property
    def b_s(self) -> Parameter:
        """Short alias for structural wingspan."""
        return self.structuralWingspan

    @property
    def v_D(self) -> Parameter:
        """Short alias for design diving speed (v_D = 1.25 * v_cruise)."""
        return self.designDivingSpeed

    @property
    def n_ult(self) -> Parameter:
        """Short alias for ultimate load factor (n_ult = 1.5 * n_max)."""
        return self.ultimateLoadFactor

    @property
    def c_HT(self) -> Parameter:
        """Short alias for horizontal tail volume coefficient."""
        return self.horizontalTailVolumeCoefficient

    @property
    def c_VT(self) -> Parameter:
        """Short alias for vertical tail volume coefficient."""
        return self.verticalTailVolumeCoefficient

    @property
    def r_H(self) -> Parameter:
        """Short alias for horizontal tail lever arm."""
        return self.horizontalTailLeverArm

    @property
    def r_V(self) -> Parameter:
        """Short alias for vertical tail lever arm."""
        return self.verticalTailLeverArm


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


def _compute_reference_calculated_values(
    mass: ReferenceMassParameters,
    dimensions: ReferenceDimensionsParameters,
    performance: ReferencePerformanceParameters,
    assumptions: ReferenceAssumptionsParameters,
    propulsion: ReferencePropulsionParameters,
    r_H: float = 8.8,
    r_V: float = 8.8,
    delta_m_F: float = 0.07,
) -> ReferenceCalculatedValues:
    """Computes derived geometry, tail volume coefficients, and calibration factors.

    Args:
        mass: Reference aircraft mass breakdown parameters.
        dimensions: Reference aircraft geometric dimensions.
        performance: Reference aircraft cruise performance parameters.
        assumptions: Reference aircraft assumed parameters.
        propulsion: Reference aircraft propulsion parameters.
        r_H: Horizontal tail lever arm [m].
        r_V: Vertical tail lever arm [m].
        delta_m_F: Fuselage mass penalty factor [-].

    Returns:
        Populated ReferenceCalculatedValues instance.
    """
    s_w = dimensions.wingArea
    b_w = dimensions.wingspan
    aspect_ratio = (b_w ** 2) / s_w
    c_mu = calc_mean_aerodynamic_chord(s_w, b_w)
    b_s = b_w / math.cos(math.radians(assumptions.wingSweepHalfChord))

    b_r = dimensions.fuselageWidth
    h_r = dimensions.fuselageHeight
    l_r = dimensions.fuselageLength
    # Approximate wetted fuselage surface area S_O [m^2] as the lateral surface of an elliptical cylinder
    s_o = math.pi * ((b_r + h_r) / 2.0) * l_r

    s_htp = dimensions.horizontalTailArea
    s_vtp = dimensions.verticalTailArea

    c_ht = calc_horizontal_tail_volume_coefficient(s_htp, r_H, s_w, c_mu)
    c_vt = calc_vertical_tail_volume_coefficient(s_vtp, r_V, s_w, b_w)

    # Component mass estimations using uncalibrated formulas
    mtom_ref = mass.takeOffMassMax
    mzfm_ref = mass.zeroFuelMassMax
    n_ult = 1.5 * assumptions.limitLoad
    # Design diving speed v_D = 1.25 * v_cruise converted from kts to m/s
    v_D = 1.25 * performance.cruiseSpeedTAS * (1.852 / 3.6)

    m_wing_calc = calc_wing_mass(
        mzfm=mzfm_ref,
        b_s=b_s,
        n_ult=n_ult,
        d_root=assumptions.wingRootThickness,
        s_w=s_w,
        delta_m_F=assumptions.wingMassPenaltyFactor,
    )
    k_wing = mass.wing / m_wing_calc

    m_lg_calc = calc_landing_gear_mass(mtom_ref)
    k_lg = mass.landingGear / m_lg_calc

    m_fus_calc = calc_fuselage_mass(v_D, r_H, b_r, h_r, s_o, delta_m_F)
    k_fus = mass.fuselage / m_fus_calc

    m_emp_calc = calc_empennage_mass(n_ult, s_htp, s_vtp)
    k_emp = mass.empennage / m_emp_calc

    m_pyl_calc = calc_pylons_mass(propulsion.totalTakeOffPower)
    k_pyl = mass.pylons / m_pyl_calc

    m_sys_calc = calc_systems_mass(mtom_ref)
    k_sys = mass.systems / m_sys_calc

    return ReferenceCalculatedValues(
        aspectRatio=Parameter(aspect_ratio, ""),
        meanAerodynamicChord=Parameter(c_mu, "m"),
        structuralWingspan=Parameter(b_s, "m"),
        designDivingSpeed=Parameter(v_D, "m/s"),
        ultimateLoadFactor=Parameter(n_ult, ""),
        horizontalTailLeverArm=Parameter(r_H, "m"),
        verticalTailLeverArm=Parameter(r_V, "m"),
        horizontalTailVolumeCoefficient=Parameter(c_ht, ""),
        verticalTailVolumeCoefficient=Parameter(c_vt, ""),
        wingEstimatedMass=Parameter(m_wing_calc, "kg"),
        wingCalibrationFactor=Parameter(k_wing, ""),
        landingGearEstimatedMass=Parameter(m_lg_calc, "kg"),
        landingGearCalibrationFactor=Parameter(k_lg, ""),
        fuselageEstimatedMass=Parameter(m_fus_calc, "kg"),
        fuselageCalibrationFactor=Parameter(k_fus, ""),
        empennageEstimatedMass=Parameter(m_emp_calc, "kg"),
        empennageCalibrationFactor=Parameter(k_emp, ""),
        pylonsEstimatedMass=Parameter(m_pyl_calc, "kg"),
        pylonsCalibrationFactor=Parameter(k_pyl, ""),
        systemsEstimatedMass=Parameter(m_sys_calc, "kg"),
        systemsCalibrationFactor=Parameter(k_sys, ""),
    )


def _find_reference_file() -> Path:
    """Resolves the path to the reference aircraft JSON file in the project root."""
    base_dir = Path(__file__).parent.parent
    for filename in ("reference_aircraft.json", "referenceAircraft.json"):
        path = base_dir / filename
        if path.exists():
            return path
    return base_dir / "reference_aircraft.json"


def load_reference_aircraft(
    path: Path | str | None = None,
    r_H: float = 8.8,
    r_V: float = 8.8,
    delta_m_F: float = 0.07,
) -> ReferenceAircraft:
    """Loads reference aircraft parameters from JSON and computes derived calculatedValues.

    Args:
        path: Optional explicit path to the reference aircraft JSON file.
        r_H: Horizontal tail lever arm [m].
        r_V: Vertical tail lever arm [m].
        delta_m_F: Fuselage mass penalty factor [-].

    Returns:
        Populated ReferenceAircraft instance.
    """
    file_path = Path(path) if path else _find_reference_file()
    with file_path.open(encoding="utf-8") as file:
        data = json.load(file)

    mass = ReferenceMassParameters(**_parameter_group(data["mass"]))
    dimensions = ReferenceDimensionsParameters(**_parameter_group(data["dimensions"]))
    performance = ReferencePerformanceParameters(**_parameter_group(data["performance"]))
    assumptions = ReferenceAssumptionsParameters(**_parameter_group(data["assumptions"]))
    aerodynamics = ReferenceAerodynamicParameters(**_parameter_group(data["aerodynamics"]))
    propulsion = ReferencePropulsionParameters(**_parameter_group(data["propulsion"]))
    fuel = ReferenceFuelParameters(**_parameter_group(data["fuel"]))

    calculatedValues = _compute_reference_calculated_values(
        mass=mass,
        dimensions=dimensions,
        performance=performance,
        assumptions=assumptions,
        propulsion=propulsion,
        r_H=r_H,
        r_V=r_V,
        delta_m_F=delta_m_F,
    )

    return ReferenceAircraft(
        mass=mass,
        dimensions=dimensions,
        performance=performance,
        assumptions=assumptions,
        aerodynamics=aerodynamics,
        propulsion=propulsion,
        fuel=fuel,
        calculatedValues=calculatedValues,
    )


def print_reference_aircraft(ref: ReferenceAircraft) -> None:
    """Prints a structured summary of reference aircraft given inputs and calculated values."""
    print("=" * 65)
    print("                      REFERENCE AIRCRAFT")
    print("=" * 65)

    print("\n--- GIVEN PARAMETERS (FROM JSON) ---")
    print(f"MTOM:                            {ref.mass.takeOffMassMax}")
    print(f"MLM:                             {ref.mass.landingMassMax}")
    print(f"MZFM:                            {ref.mass.zeroFuelMassMax}")
    print(f"Wing area (S_W):                 {ref.dimensions.wingArea}")
    print(f"Wingspan (b_W):                  {ref.dimensions.wingspan}")
    print(f"Fuselage length (l_R):           {ref.dimensions.fuselageLength}")
    print(f"Fuselage width (b_R):            {ref.dimensions.fuselageWidth}")
    print(f"Fuselage height (h_R):           {ref.dimensions.fuselageHeight}")
    print(f"Horizontal tail area (S_HTP):    {ref.dimensions.horizontalTailArea}")
    print(f"Vertical tail area (S_VTP):      {ref.dimensions.verticalTailArea}")
    print(f"Limit load factor (n_max):       {ref.assumptions.limitLoad}")

    print("\n--- CALCULATED VALUES (DERIVED) ---")
    calc = ref.calculatedValues
    print(f"Aspect ratio (AR):               {calc.aspectRatio.value:.3f}")
    print(f"Mean aerodynamic chord (c_mu):   {calc.meanAerodynamicChord.value:.3f} m")
    print(f"Ultimate load factor (n_ult):    {calc.ultimateLoadFactor.value:.2f}")
    print(f"Horizontal tail arm (r_H):       {calc.horizontalTailLeverArm}")
    print(f"Horizontal tail volume coeff (c_HT): {calc.horizontalTailVolumeCoefficient.value:.4f}")
    print(f"Vertical tail arm (r_V):         {calc.verticalTailLeverArm}")
    print(f"Vertical tail volume coeff (c_VT):   {calc.verticalTailVolumeCoefficient.value:.4f}")

    print("\n--- FORMULA MASS ESTIMATIONS & CALIBRATION FACTORS ---")
    print(f"Wing:         Catalog: {ref.mass.wing!s:>7} | Formula: {calc.wingEstimatedMass.value:7.2f} kg | Factor: {calc.wingCalibrationFactor.value:.4f}")
    print(f"Fuselage:     Catalog: {ref.mass.fuselage!s:>7} | Formula: {calc.fuselageEstimatedMass.value:7.2f} kg | Factor: {calc.fuselageCalibrationFactor.value:.4f}")
    print(f"Empennage:    Catalog: {ref.mass.empennage!s:>7} | Formula: {calc.empennageEstimatedMass.value:7.2f} kg | Factor: {calc.empennageCalibrationFactor.value:.4f}")
    print(f"Landing gear: Catalog: {ref.mass.landingGear!s:>7} | Formula: {calc.landingGearEstimatedMass.value:7.2f} kg | Factor: {calc.landingGearCalibrationFactor.value:.4f}")
    print(f"Pylons:       Catalog: {ref.mass.pylons!s:>7} | Formula: {calc.pylonsEstimatedMass.value:7.2f} kg | Factor: {calc.pylonsCalibrationFactor.value:.4f}")
    print(f"Systems:      Catalog: {ref.mass.systems!s:>7} | Formula: {calc.systemsEstimatedMass.value:7.2f} kg | Factor: {calc.systemsCalibrationFactor.value:.4f}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    ref = load_reference_aircraft()
    print_reference_aircraft(ref)
