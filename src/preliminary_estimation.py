import math

from mass_formulas import calc_empennage_mass, calc_fuselage_mass, calc_landing_gear_mass, calc_systems_mass
from read_parameters import load_parameters
from read_reference_aircraft import load_reference_aircraft

params = load_parameters()
ref_aircraft = load_reference_aircraft()
gravity = 9.81  # m/s^2
L_D = ref_aircraft.aerodynamics.liftToDragRatioCruise  # Cruise lift-to-drag ratio
MTOM = 7500
MLM = MTOM


def calc_calibrated_landing_gear_mass() -> float:
    m_landing_gear = calc_landing_gear_mass(MTOM)
    calibration_factor = ref_aircraft.calculatedValues.landingGearCalibrationFactor
    return m_landing_gear * calibration_factor


def calculate_wing_mass() -> float:
    return ref_aircraft.mass.wing


def calc_calibrated_fuselage_mass() -> float:
    # Real aircraft calculation
    v_D = 140.0  # [m/s] Design diving speed
    r_H = ref_aircraft.calculatedValues.r_H  # [m] Horizontal tail moment arm
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
    # Real aircraft calculation
    n_ult = ref_aircraft.flightLoads.ultimateLoadFactor
    S_HTP = ref_aircraft.dimensions.horizontalTailArea
    S_VTP = ref_aircraft.dimensions.verticalTailArea
    m_empennage = calc_empennage_mass(n_ult, S_HTP, S_VTP)
    calibration_factor = ref_aircraft.calculatedValues.empennageCalibrationFactor
    return m_empennage * calibration_factor


def calculate_pylons_mass() -> float:
    return ref_aircraft.mass.pylons


def calculate_structure_mass() -> float:
    return (
        calculate_wing_mass()
        + calc_calibrated_fuselage_mass()
        + calc_calibrated_landing_gear_mass()
        + calc_calibrated_empennage_mass()
        + calculate_pylons_mass()
    )


def calculate_engine_mass() -> float:
    return ref_aircraft.mass.engine


def calc_calibrated_systems_mass() -> float:
    m_systems = calc_systems_mass(MTOM)
    calibration_factor = ref_aircraft.calculatedValues.systemsCalibrationFactor
    return m_systems * calibration_factor


def calculate_furnishings_mass() -> float:
    return float(ref_aircraft.mass.furnishings)


def calculate_payload_mass() -> float:
    return params.payload.weightPerPassenger * params.payload.numberOfPassengers


def calculate_operator_items_mass() -> float:
    return float(ref_aircraft.mass.operatorItems)


# ------------- Mass Breakdown ------------------
print("----- MASS BREAKDOWN -----")
mass_unit = params.performance.takeOffMassMax.unit

m_payload = calculate_payload_mass()
m_operator_items = calculate_operator_items_mass()
m_structure = calculate_structure_mass()
m_engine = calculate_engine_mass()
m_systems = calc_calibrated_systems_mass()
m_furnishings = calculate_furnishings_mass()
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

print(f"Payload mass: {calculate_payload_mass()} {mass_unit}")
print(f"Operator items mass: {calculate_operator_items_mass()} {mass_unit} (Ref: {ref_aircraft.mass.operatorItems})")
print(f"Structure mass: {calculate_structure_mass()} {mass_unit} (Ref: {m_structure_ref} {mass_unit})")
print(f"  - Wing: {calculate_wing_mass()} {mass_unit} (Ref: {ref_aircraft.mass.wing})")
print(f"  - Fuselage: {calc_calibrated_fuselage_mass()} {mass_unit} (Ref: {ref_aircraft.mass.fuselage})")
print(f"  - Landing gear: {calc_calibrated_landing_gear_mass()} {mass_unit} (Ref: {ref_aircraft.mass.landingGear})")
print(f"  - Empennage: {calc_calibrated_empennage_mass()} {mass_unit} (Ref: {ref_aircraft.mass.empennage})")
print(f"  - Pylons: {calculate_pylons_mass()} {mass_unit} (Ref: {ref_aircraft.mass.pylons})")
print(f"Engine mass: {calculate_engine_mass()} {mass_unit} (Ref: {ref_aircraft.mass.engine})")
print(f"Systems mass: {calc_calibrated_systems_mass()} {mass_unit} (Ref: {ref_aircraft.mass.systems})")
print(f"Furnishings mass: {calculate_furnishings_mass()} {mass_unit} (Ref: {ref_aircraft.mass.furnishings})")
print(f"Battery mass: {m_battery} {mass_unit}")
print(f"Total Takeoff Mass (MTOM): {MTOM} {mass_unit} (Ref: {ref_aircraft.mass.mtom})\n")

# ------------- Range ------------------
range_m = params.battery.cellEnergyDensityMax*3600 * 0.85 * 1/gravity * L_D * m_battery / MTOM
range_km = range_m / 1000
print(f"Range: {range_km} {params.mission.range.unit}")
print(f"Range: {range_km / 1.852} NM")





# ------------- Takeoff Distance ------------------
print("\n\n----- TAKEOFF DISTANCE (calculation seems invalid) -----")
rho = params.performance.takeOffDensity  # [kg/m^3]
rho0 = 1.225  # [kg/m^3]
CA_MAX_TO = ref_aircraft.aerodynamics.maxTakeOffLiftCoefficient
P = (
    ref_aircraft.propulsion.engineTakeOffPower
    * ref_aircraft.propulsion.numberOfEngines
    * 1000
)  # [W]
takeoff_distance = params.performance.takeOffFieldLengthMax
m0_S = takeoff_distance * (rho / rho0 * CA_MAX_TO * P / (MTOM * gravity))
print(f"Maximum wing loading: {m0_S} m^2")
S0 = MTOM / m0_S
print(f"Required wing area: {S0} m^2")

# ------------- Landing Distance ------------------
print("\n\n----- LANDING DISTANCE -----")
l_a = 183  # [m]
rho = params.performance.takeOffDensity  # [kg/m^3]
rho0 = 1.225  # [kg/m^3]
CA_MAX_LDG = ref_aircraft.aerodynamics.maxLandingLiftCoefficient
A = 1 # no reversed thrust
landing_distance = params.performance.landingFieldLengthMax + l_a
m0_S = MTOM / MLM * (landing_distance - l_a) * rho / rho0 * CA_MAX_LDG / (0.51 * 1 * gravity)
print(f"Maximum wing loading: {m0_S} m^2")
S0 = MTOM / m0_S
print(f"Required wing area: {S0} m^2")

# ------------- Approach Speed ------------------
print("\n\n----- APPROACH SPEED -----")
v_stall = 113 / 3.6 # Stall speed from CS-23 for small aircrafts [m/s]
m0_S = CA_MAX_LDG * rho / (2*gravity) * v_stall**2 * MTOM / MLM
print(f"Maximum wing loading: {m0_S} m^2")
S0 = MTOM / m0_S
print(f"Required wing area: {S0} m^2")