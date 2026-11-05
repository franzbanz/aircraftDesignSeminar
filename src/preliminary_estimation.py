"""Preliminary mass estimation and range calculation for the battery-electric aircraft."""

from aircraft import BatteryAircraft
from data import SiValue, load_constraints, load_design_parameters, load_reference_aircraft

constraints = load_constraints()
ref_aircraft = load_reference_aircraft()
design_params = load_design_parameters()

# Initialize unified aircraft model at design MTOM
aircraft = BatteryAircraft(constraints, design_params, ref_aircraft)
aircraft.converge_mtom()

m_structure_ref = SiValue(
    ref_aircraft.mass.wing.si
    + ref_aircraft.mass.fuselage.si
    + ref_aircraft.mass.landingGear.si
    + ref_aircraft.mass.empennage.si
    + ref_aircraft.mass.pylons.si,
    "kg",
)

# ------------- Mass Breakdown ------------------
print("----- MASS BREAKDOWN -----")
print(f"Payload mass: {aircraft.m_payload}")
print(f"Operator items mass: {aircraft.m_operator_items} (Ref: {ref_aircraft.mass.operatorItems})")
print(f"Structure mass: {aircraft.m_structure} (Ref: {m_structure_ref})")
print(f"  - Wing: {aircraft.m_wing} (Ref: {ref_aircraft.mass.wing})")
print(f"  - Fuselage: {aircraft.m_fuselage} (Ref: {ref_aircraft.mass.fuselage})")
print(f"  - Landing gear: {aircraft.m_landing_gear} (Ref: {ref_aircraft.mass.landingGear})")
print(f"  - Empennage: {aircraft.m_empennage} (Ref: {ref_aircraft.mass.empennage})")
print(f"  - Pylons: {aircraft.m_pylons} (Ref: {ref_aircraft.mass.pylons})")
print(f"Engine mass: {aircraft.m_engine} (Ref: {ref_aircraft.mass.engine})")
print(f"Systems mass: {aircraft.m_systems} (Ref: {ref_aircraft.mass.systems})")
print(f"Furnishings mass: {aircraft.m_furnishings} (Ref: {ref_aircraft.mass.furnishings})")
print(f"Battery mass: {aircraft.m_battery}")
print(f"Total Takeoff Mass (MTOM): {aircraft.mtom} (Ref: {ref_aircraft.mass.takeOffMassMax})\n")

# ------------- Range ------------------
print(f"Range: {aircraft.range.to('km')}")
print(f"Range: {aircraft.range.to('NM')}")
