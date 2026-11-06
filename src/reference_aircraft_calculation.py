"""Reference aircraft derived geometry, tail volume, and mass calibration calculations.

Computes derived aerodynamic/geometric properties and calibration factors for the
reference aircraft (Dornier 228) from its datasheet parameters.
"""
from data import SiValue

import math

from data.unit_value import UnitValue
from data.reference_aircraft_data import (
    ReferenceAircraft,
    ReferenceAssumptionsParameters,
    ReferenceCalculatedValues,
    ReferenceDimensionsParameters,
    ReferenceMassParameters,
    ReferenceMissionParameters,
    ReferencePropulsionParameters,
)
from formulas.geometry import (
    calc_horizontal_tail_volume_coefficient,
    calc_mean_aerodynamic_chord,
    calc_vertical_tail_volume_coefficient,
)
from formulas.mass_formulas import (
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
    calc_wing_mass,
)


def calc_reference_aircraft_values(
    mass: ReferenceMassParameters,
    dimensions: ReferenceDimensionsParameters,
    mission: ReferenceMissionParameters,
    assumptions: ReferenceAssumptionsParameters,
    propulsion: ReferencePropulsionParameters,
) -> ReferenceCalculatedValues:
    """Computes derived geometry, tail volume coefficients, and calibration factors.

    Args:
        mass: Reference aircraft mass breakdown parameters.
        dimensions: Reference aircraft geometric dimensions.
        mission: Reference aircraft cruise and mission parameters.
        assumptions: Reference aircraft assumed parameters.
        propulsion: Reference aircraft propulsion parameters.

    Returns:
        Populated ``ReferenceCalculatedValues`` instance.
    """
    r_h = assumptions.horizontalTailLeverArm.si
    r_v = assumptions.verticalTailLeverArm.si
    delta_m_f = assumptions.fuselageMassPenaltyFactor

    s_w = dimensions.wingArea.si
    b_w = dimensions.wingspan.si
    aspect_ratio = (b_w ** 2) / s_w
    c_mu = calc_mean_aerodynamic_chord(s_w, b_w)
    b_s = b_w / math.cos(math.radians(assumptions.wingSweepHalfChord))
    b_s = SiValue(b_s, "m")

    b_r = dimensions.fuselageWidth.si
    h_r = dimensions.fuselageHeight.si
    l_r = dimensions.fuselageLength.si
    # Approximate wetted fuselage surface area S_O [m^2] as the lateral surface of an elliptical cylinder
    s_o = math.pi * ((b_r + h_r) / 2.0) * l_r
    s_o = SiValue(s_o, "m^2")
    print(f"Wetted fuselage surface area S_O: {s_o}")

    s_htp = dimensions.horizontalTailArea.si
    s_vtp = dimensions.verticalTailArea.si

    c_ht = calc_horizontal_tail_volume_coefficient(s_htp, r_h, s_w, c_mu)
    c_vt = calc_vertical_tail_volume_coefficient(s_vtp, r_v, s_w, b_w)

    # Component mass estimations using uncalibrated formulas
    mtom_ref = mass.takeOffMassMax.si
    mzfm_ref = mass.zeroFuelMassMax.si
    n_ult = 1.5 * assumptions.limitLoad.si
    # Design diving speed v_D = 1.25 * v_cruise converted from kts to m/s
    v_D = SiValue(1.25 * mission.cruiseSpeedTAS.si, "m/s")

    m_wing_calc = calc_wing_mass(
        mzfm=mzfm_ref,
        b_s=b_s,
        n_ult=n_ult,
        d_root=assumptions.wingRootThickness.si,
        s_w=s_w,
        delta_m_F=assumptions.wingMassPenaltyFactor,
    )
    k_wing = mass.wing / m_wing_calc

    m_lg_calc = calc_landing_gear_mass(mtom_ref)
    k_lg = mass.landingGear / m_lg_calc

    m_fus_calc = calc_fuselage_mass(v_D, r_h, b_r, h_r, s_o, delta_m_f)
    k_fus = mass.fuselage / m_fus_calc

    m_emp_calc = calc_empennage_mass(n_ult, s_htp, s_vtp)
    k_emp = mass.empennage / m_emp_calc

    m_pyl_calc = calc_pylons_mass(propulsion.totalTakeOffPower.si)
    k_pyl = mass.pylons / m_pyl_calc

    m_sys_calc = calc_systems_mass(mtom_ref)
    k_sys = mass.systems / m_sys_calc

    return ReferenceCalculatedValues(
        aspectRatio=UnitValue(aspect_ratio, ""),
        meanAerodynamicChord=UnitValue(c_mu, "m"),
        structuralWingspan=UnitValue(b_s, "m"),
        designDivingSpeed=UnitValue(v_D, "m/s"),
        ultimateLoadFactor=UnitValue(n_ult, ""),
        horizontalTailLeverArm=assumptions.horizontalTailLeverArm,
        verticalTailLeverArm=assumptions.verticalTailLeverArm,
        horizontalTailVolumeCoefficient=UnitValue(c_ht, ""),
        verticalTailVolumeCoefficient=UnitValue(c_vt, ""),
        wingEstimatedMass=UnitValue(m_wing_calc, "kg"),
        wingCalibrationFactor=UnitValue(k_wing, ""),
        landingGearEstimatedMass=UnitValue(m_lg_calc, "kg"),
        landingGearCalibrationFactor=UnitValue(k_lg, ""),
        fuselageEstimatedMass=UnitValue(m_fus_calc, "kg"),
        fuselageCalibrationFactor=UnitValue(k_fus, ""),
        empennageEstimatedMass=UnitValue(m_emp_calc, "kg"),
        empennageCalibrationFactor=UnitValue(k_emp, ""),
        pylonsEstimatedMass=UnitValue(m_pyl_calc, "kg"),
        pylonsCalibrationFactor=UnitValue(k_pyl, ""),
        systemsEstimatedMass=UnitValue(m_sys_calc, "kg"),
        systemsCalibrationFactor=UnitValue(k_sys, ""),
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
    from data import load_reference_aircraft

    print_reference_aircraft(load_reference_aircraft())

