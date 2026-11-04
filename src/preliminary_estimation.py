import math

from formulas import (
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
    calc_wing_mass,
)
from data import UnitValue, load_parameters, load_reference_aircraft


params = load_parameters()
ref_aircraft = load_reference_aircraft()
gravity = 9.81  # m/s^2
L_D = ref_aircraft.aerodynamics.liftToDragRatioCruise  # Cruise lift-to-drag ratio
MTOM = 8600
# (MZFM = MLM = MTOM for battery-electric aircraft)
MZFM = MTOM
MLM = MTOM


def calc_calibrated_landing_gear_mass() -> float:
    """Calculates landing gear mass scaled with the reference aircraft calibration factor [kg]."""
    m_landing_gear = calc_landing_gear_mass(MTOM)
    calibration_factor = ref_aircraft.calculatedValues.landingGearCalibrationFactor
    return m_landing_gear * calibration_factor


def calc_calibrated_wing_mass() -> float:
    """Calculates wing mass scaled with the reference aircraft calibration factor [kg]."""
    b_s = ref_aircraft.calculatedValues.structuralWingspan
    n_ult = ref_aircraft.calculatedValues.ultimateLoadFactor
    d_root = ref_aircraft.assumptions.wingRootThickness
    s_w = ref_aircraft.dimensions.wingArea
    delta_m_F = ref_aircraft.assumptions.wingMassPenaltyFactor
    m_wing = calc_wing_mass(MZFM, b_s, n_ult, d_root, s_w, delta_m_F)
    calibration_factor = ref_aircraft.calculatedValues.wingCalibrationFactor
    return m_wing * calibration_factor


def calc_calibrated_fuselage_mass() -> float:
    """Calculates fuselage mass scaled with the reference aircraft calibration factor [kg]."""
    v_D = 1.25 * params.performance.cruiseSpeedMin.to("m/s")  # [m/s] Design diving speed (1.25 * v_cruise)
    r_H = ref_aircraft.calculatedValues.horizontalTailLeverArm  # [m] Horizontal tail moment arm
    b_R = ref_aircraft.dimensions.fuselageWidth  # [m] Max fuselage width
    h_R = ref_aircraft.dimensions.fuselageHeight  # [m] Fuselage height
    l_R = ref_aircraft.dimensions.fuselageLength  # [m] Fuselage length
    delta_m_F = 0.07  # Fuselage-mounted landing gear (+7%)
    # Approximate wetted fuselage surface area S_O [m^2] as the lateral surface of an elliptical cylinder
    s_o = math.pi * ((b_R + h_R) / 2.0) * l_R
    m_fuselage = calc_fuselage_mass(v_D, r_H, b_R, h_R, s_o, delta_m_F)
    calibration_factor = ref_aircraft.calculatedValues.fuselageCalibrationFactor
    return m_fuselage * calibration_factor


def calc_calibrated_empennage_mass() -> float:
    """Calculates empennage mass scaled with the reference aircraft calibration factor [kg]."""
    n_ult = ref_aircraft.calculatedValues.ultimateLoadFactor
    S_HTP = ref_aircraft.dimensions.horizontalTailArea
    S_VTP = ref_aircraft.dimensions.verticalTailArea
    m_empennage = calc_empennage_mass(n_ult, S_HTP, S_VTP)
    calibration_factor = ref_aircraft.calculatedValues.empennageCalibrationFactor
    return m_empennage * calibration_factor


def calc_calibrated_pylons_mass() -> float:
    """Calculates cowling/pylon mass scaled with the reference aircraft calibration factor [kg]."""
    p_to_kw = ref_aircraft.propulsion.totalTakeOffPower
    m_pylons = calc_pylons_mass(p_to_kw)
    calibration_factor = ref_aircraft.calculatedValues.pylonsCalibrationFactor
    return m_pylons * calibration_factor


def calc_structure_mass() -> float:
    """Calculates total airframe structure mass as the sum of all structural component masses [kg]."""
    return (
        calc_calibrated_wing_mass()
        + calc_calibrated_fuselage_mass()
        + calc_calibrated_landing_gear_mass()
        + calc_calibrated_empennage_mass()
        + calc_calibrated_pylons_mass()
    )


def calc_engine_mass() -> float:
    """Returns propulsion engine mass [kg] (adopted from reference aircraft)."""
    return ref_aircraft.mass.engine


def calc_calibrated_systems_mass() -> float:
    """Calculates systems mass scaled with the reference aircraft calibration factor [kg]."""
    m_systems = calc_systems_mass(MTOM)
    calibration_factor = ref_aircraft.calculatedValues.systemsCalibrationFactor
    return m_systems * calibration_factor


def calc_furnishings_mass() -> float:
    """Returns cabin furnishings mass [kg].

    Adopted directly from the reference aircraft because fuselage dimensions, cabin layout,
    and passenger capacity (19 PAX) remain unchanged. Empirical MTOM-based formulas would
    artificially inflate furnishings mass due to the heavy battery.
    """
    return ref_aircraft.mass.furnishings


def calc_payload_mass() -> float:
    """Calculates design payload mass from passenger count and mass per passenger [kg]."""
    return params.payload.weightPerPassenger * params.payload.numberOfPassengers


def calc_operator_items_mass() -> float:
    """Returns operator items mass [kg].

    Adopted directly from the reference aircraft because crew size, operational equipment,
    and mission category remain identical.
    """
    return ref_aircraft.mass.operatorItems


# ------------- Mass Breakdown ------------------
print("----- MASS BREAKDOWN -----")
mass_unit = params.performance.takeOffMassMax.unit

m_payload = calc_payload_mass()
m_operator_items = calc_operator_items_mass()
m_structure = calc_structure_mass()
m_engine = calc_engine_mass()
m_systems = calc_calibrated_systems_mass()
m_furnishings = calc_furnishings_mass()
m_battery = (
    MTOM
    - m_payload
    - m_operator_items
    - m_structure
    - m_engine
    - m_systems
    - m_furnishings
)

m_structure_ref = (
    ref_aircraft.mass.wing
    + ref_aircraft.mass.fuselage
    + ref_aircraft.mass.landingGear
    + ref_aircraft.mass.empennage
    + ref_aircraft.mass.pylons
)

print(f"Payload mass: {calc_payload_mass()} {mass_unit}")
print(f"Operator items mass: {calc_operator_items_mass()} {mass_unit} (Ref: {ref_aircraft.mass.operatorItems})")
print(f"Structure mass: {calc_structure_mass()} {mass_unit} (Ref: {m_structure_ref} {mass_unit})")
print(f"  - Wing: {calc_calibrated_wing_mass()} {mass_unit} (Ref: {ref_aircraft.mass.wing})")
print(f"  - Fuselage: {calc_calibrated_fuselage_mass()} {mass_unit} (Ref: {ref_aircraft.mass.fuselage})")
print(f"  - Landing gear: {calc_calibrated_landing_gear_mass()} {mass_unit} (Ref: {ref_aircraft.mass.landingGear})")
print(f"  - Empennage: {calc_calibrated_empennage_mass()} {mass_unit} (Ref: {ref_aircraft.mass.empennage})")
print(f"  - Pylons: {calc_calibrated_pylons_mass()} {mass_unit} (Ref: {ref_aircraft.mass.pylons})")
print(f"Engine mass: {calc_engine_mass()} {mass_unit} (Ref: {ref_aircraft.mass.engine})")
print(f"Systems mass: {calc_calibrated_systems_mass()} {mass_unit} (Ref: {ref_aircraft.mass.systems})")
print(f"Furnishings mass: {calc_furnishings_mass()} {mass_unit} (Ref: {ref_aircraft.mass.furnishings})")
print(f"Battery mass: {m_battery} {mass_unit}")
print(f"Total Takeoff Mass (MTOM): {MTOM} {mass_unit} (Ref: {ref_aircraft.mass.takeOffMassMax})\n")

# ------------- Range ------------------
range_m = params.battery.cellEnergyDensityMax.to("J/kg") * 0.85 * 1 / gravity * L_D * m_battery / MTOM
range_km = UnitValue(range_m, "m").to("km")
print(f"Range: {range_km}")
print(f"Range: {range_km.to('NM').value} NM")
