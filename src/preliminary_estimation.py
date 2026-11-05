import math

from constants import GRAVITY
from data import SiValue, load_parameters, load_reference_aircraft
from formulas import (
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
    calc_wing_mass,
)

params = load_parameters()
ref_aircraft = load_reference_aircraft()

L_D = ref_aircraft.aerodynamics.liftToDragRatioCruise  # Cruise lift-to-drag ratio
MTOM = SiValue(8600.0, "kg")
# (MZFM = MLM = MTOM for battery-electric aircraft)
MZFM = MTOM
MLM = MTOM


def calc_calibrated_landing_gear_mass() -> SiValue:
    """Calculates landing gear mass scaled with the reference aircraft calibration factor [kg]."""
    m_landing_gear = calc_landing_gear_mass(MTOM)
    calibration_factor = ref_aircraft.calculatedValues.landingGearCalibrationFactor
    return SiValue(m_landing_gear * calibration_factor, "kg")


def calc_calibrated_wing_mass() -> SiValue:
    """Calculates wing mass scaled with the reference aircraft calibration factor [kg]."""
    b_s = ref_aircraft.calculatedValues.structuralWingspan.si
    n_ult = ref_aircraft.calculatedValues.ultimateLoadFactor
    d_root = ref_aircraft.assumptions.wingRootThickness.si
    s_w = ref_aircraft.dimensions.wingArea.si
    delta_m_F = ref_aircraft.assumptions.wingMassPenaltyFactor
    m_wing = calc_wing_mass(MZFM, b_s, n_ult, d_root, s_w, delta_m_F)
    calibration_factor = ref_aircraft.calculatedValues.wingCalibrationFactor
    return SiValue(m_wing * calibration_factor, "kg")


def calc_calibrated_fuselage_mass() -> SiValue:
    """Calculates fuselage mass scaled with the reference aircraft calibration factor [kg]."""
    v_D = SiValue(1.25 * params.performance.cruiseSpeedMin.si, "m/s")
    r_H = ref_aircraft.calculatedValues.horizontalTailLeverArm.si
    b_R = ref_aircraft.dimensions.fuselageWidth.si
    h_R = ref_aircraft.dimensions.fuselageHeight.si
    l_R = ref_aircraft.dimensions.fuselageLength.si
    delta_m_F = 0.07  # Fuselage-mounted landing gear (+7%)
    # Approximate wetted fuselage surface area S_O [m^2] as the lateral surface of an elliptical cylinder
    s_o = SiValue(math.pi * ((b_R + h_R) / 2.0) * l_R, "m^2")
    m_fuselage = calc_fuselage_mass(v_D, r_H, b_R, h_R, s_o, delta_m_F)
    calibration_factor = ref_aircraft.calculatedValues.fuselageCalibrationFactor
    return SiValue(m_fuselage * calibration_factor, "kg")


def calc_calibrated_empennage_mass() -> SiValue:
    """Calculates empennage mass scaled with the reference aircraft calibration factor [kg]."""
    n_ult = ref_aircraft.calculatedValues.ultimateLoadFactor
    s_htp = ref_aircraft.dimensions.horizontalTailArea.si
    s_vtp = ref_aircraft.dimensions.verticalTailArea.si
    m_empennage = calc_empennage_mass(n_ult, s_htp, s_vtp)
    calibration_factor = ref_aircraft.calculatedValues.empennageCalibrationFactor
    return SiValue(m_empennage * calibration_factor, "kg")


def calc_calibrated_pylons_mass() -> SiValue:
    """Calculates cowling/pylon mass scaled with the reference aircraft calibration factor [kg]."""
    p_to = ref_aircraft.propulsion.totalTakeOffPower.si
    m_pylons = calc_pylons_mass(p_to)
    calibration_factor = ref_aircraft.calculatedValues.pylonsCalibrationFactor
    return SiValue(m_pylons * calibration_factor, "kg")


def calc_structure_mass() -> SiValue:
    """Calculates total airframe structure mass as the sum of all structural component masses [kg]."""
    return SiValue(
        calc_calibrated_wing_mass()
        + calc_calibrated_fuselage_mass()
        + calc_calibrated_landing_gear_mass()
        + calc_calibrated_empennage_mass()
        + calc_calibrated_pylons_mass(),
        "kg",
    )


def calc_engine_mass() -> SiValue:
    """Returns propulsion engine mass [kg] (adopted from reference aircraft)."""
    return ref_aircraft.mass.engine.si


def calc_calibrated_systems_mass() -> SiValue:
    """Calculates systems mass scaled with the reference aircraft calibration factor [kg]."""
    m_systems = calc_systems_mass(MTOM)
    calibration_factor = ref_aircraft.calculatedValues.systemsCalibrationFactor
    return SiValue(m_systems * calibration_factor, "kg")


def calc_furnishings_mass() -> SiValue:
    """Returns cabin furnishings mass [kg].

    Adopted directly from the reference aircraft because fuselage dimensions, cabin layout,
    and passenger capacity (19 PAX) remain unchanged. Empirical MTOM-based formulas would
    artificially inflate furnishings mass due to the heavy battery.
    """
    return ref_aircraft.mass.furnishings.si


def calc_payload_mass() -> SiValue:
    """Calculates design payload mass from passenger count and mass per passenger [kg]."""
    return SiValue(params.payload.weightPerPassenger.si * params.payload.numberOfPassengers, "kg")


def calc_operator_items_mass() -> SiValue:
    """Returns operator items mass [kg].

    Adopted directly from the reference aircraft because crew size, operational equipment,
    and mission category remain identical.
    """
    return ref_aircraft.mass.operatorItems.si


# ------------- Mass Breakdown ------------------
print("----- MASS BREAKDOWN -----")

m_payload = calc_payload_mass()
m_operator_items = calc_operator_items_mass()
m_structure = calc_structure_mass()
m_engine = calc_engine_mass()
m_systems = calc_calibrated_systems_mass()
m_furnishings = calc_furnishings_mass()
m_battery = SiValue(
    MTOM
    - m_payload
    - m_operator_items
    - m_structure
    - m_engine
    - m_systems
    - m_furnishings,
    "kg",
)

m_structure_ref = SiValue(
    ref_aircraft.mass.wing.si
    + ref_aircraft.mass.fuselage.si
    + ref_aircraft.mass.landingGear.si
    + ref_aircraft.mass.empennage.si
    + ref_aircraft.mass.pylons.si,
    "kg",
)

print(f"Payload mass: {m_payload}")
print(f"Operator items mass: {m_operator_items} (Ref: {ref_aircraft.mass.operatorItems})")
print(f"Structure mass: {m_structure} (Ref: {m_structure_ref})")
print(f"  - Wing: {calc_calibrated_wing_mass()} (Ref: {ref_aircraft.mass.wing})")
print(f"  - Fuselage: {calc_calibrated_fuselage_mass()} (Ref: {ref_aircraft.mass.fuselage})")
print(f"  - Landing gear: {calc_calibrated_landing_gear_mass()} (Ref: {ref_aircraft.mass.landingGear})")
print(f"  - Empennage: {calc_calibrated_empennage_mass()} (Ref: {ref_aircraft.mass.empennage})")
print(f"  - Pylons: {calc_calibrated_pylons_mass()} (Ref: {ref_aircraft.mass.pylons})")
print(f"Engine mass: {m_engine} (Ref: {ref_aircraft.mass.engine})")
print(f"Systems mass: {m_systems} (Ref: {ref_aircraft.mass.systems})")
print(f"Furnishings mass: {m_furnishings} (Ref: {ref_aircraft.mass.furnishings})")
print(f"Battery mass: {m_battery}")
print(f"Total Takeoff Mass (MTOM): {MTOM} (Ref: {ref_aircraft.mass.takeOffMassMax})\n")

# ------------- Range ------------------
range_ = SiValue(
    params.battery.cellEnergyDensityMax.si * 0.85 * 1 / GRAVITY * L_D * m_battery / MTOM,
    "m",
)
print(f"Range: {range_.to('km')}")
print(f"Range: {range_.to('NM')}")
