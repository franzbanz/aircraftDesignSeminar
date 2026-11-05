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

# ------------- Aircraft Dimensions & Geometry ------------------
print("\n----- AIRCRAFT DIMENSIONS & GEOMETRY -----")
print(f"Wing Area (S_W):             {float(aircraft.wing_area):.2f} m^2 (Ref: {float(ref_aircraft.dimensions.wingArea):.2f} m^2)")
print(f"Wingspan (b_W):              {float(aircraft.wingspan):.2f} m (Ref: {float(ref_aircraft.dimensions.wingspan):.2f} m, Max: {float(aircraft.design.aerodynamics.maxWingSpan):.2f} m)")
print(f"Aspect Ratio (AR):           {aircraft.aspect_ratio:.2f} (Ref: {float(ref_aircraft.calculatedValues.aspectRatio.value):.2f})")
print(f"Mean Aerodynamic Chord:      {float(aircraft.mean_aerodynamic_chord):.2f} m (Ref: {float(ref_aircraft.calculatedValues.meanAerodynamicChord):.2f} m)")
print(f"Wing Root Thickness (16%):   {float(aircraft.wing_root_thickness):.2f} m (Ref: {float(ref_aircraft.assumptions.wingRootThickness):.2f} m)")
print(f"Fuselage (L x W x H):        {float(aircraft.fuselage_length):.2f} m x {float(aircraft.fuselage_width):.2f} m x {float(aircraft.fuselage_height):.2f} m")
print(f"Horizontal Tail Area (S_HT): {float(aircraft.horizontal_tail_area):.2f} m^2 (Ref: {float(ref_aircraft.dimensions.horizontalTailArea):.2f} m^2)")
print(f"Vertical Tail Area (S_VT):   {float(aircraft.vertical_tail_area):.2f} m^2 (Ref: {float(ref_aircraft.dimensions.verticalTailArea):.2f} m^2)")
print(f"Design Wing Loading:         {aircraft.wing_loading_design:.2f} kg/m^2")
print(f"Design Thrust Loading:       {aircraft.thrust_loading_design:.4f}")
print(f"Total Take-off Thrust:       {float(aircraft.total_takeoff_thrust.to('kN')):.2f} kN")
print(f"Total Installed Power:       {float(aircraft.total_takeoff_power.to('kW')):.1f} kW")

if __name__ == "__main__":
    from visualization import interactive_plot_menu

    interactive_plot_menu(aircraft, ref_aircraft)
