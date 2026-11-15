"""Preliminary mass estimation and range calculation for the battery-electric aircraft."""

import argparse
from pathlib import Path

from aircraft import BatteryAircraft
from data import load_constraints, load_design_parameters
from reference_aircraft import load_reference_aircraft
from visualizations import interactive_plot_menu, print_aircraft_summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preliminary mass estimation and range calculation."
    )
    parser.add_argument(
        "--design",
        type=Path,
        default=None,
        help="Path to design parameters JSON (defaults to design_parameters.json).",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Use design_parameters_baseline.json instead of design_parameters.json.",
    )
    return parser.parse_args()


args = _parse_args()
design_path = (
    Path(__file__).resolve().parent.parent / "design_parameters_baseline.json"
    if args.baseline
    else args.design
)

constraints = load_constraints()
design_params = load_design_parameters(design_path)
ref_aircraft = load_reference_aircraft(design=design_params)

# Initialize unified aircraft model at design MTOM
aircraft = BatteryAircraft(constraints, design_params, ref_aircraft)
aircraft.converge_mtom()

print_aircraft_summary(aircraft, ref_aircraft)

if __name__ == "__main__":
    interactive_plot_menu(aircraft, ref_aircraft)
