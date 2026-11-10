"""Preliminary mass estimation and range calculation for the battery-electric aircraft."""

from aircraft import BatteryAircraft
from data import load_constraints, load_design_parameters
from reference_aircraft import load_reference_aircraft
from visualizations import interactive_plot_menu, print_aircraft_summary

constraints = load_constraints()
ref_aircraft = load_reference_aircraft()
design_params = load_design_parameters()

# Initialize unified aircraft model at design MTOM
aircraft = BatteryAircraft(constraints, design_params, ref_aircraft)
aircraft.converge_mtom()

print_aircraft_summary(aircraft, ref_aircraft)

if __name__ == "__main__":
    interactive_plot_menu(aircraft, ref_aircraft)
