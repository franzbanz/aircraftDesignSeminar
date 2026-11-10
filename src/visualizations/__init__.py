"""Visualization and terminal reporting package for aircraft sizing, mass, energy, and geometry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from visualizations.aircraft import (
    plot_aircraft_geometry,
    plot_mass_breakdown,
    print_aircraft_summary,
)
from visualizations.fuel_fractions import (
    plot_mission_energy,
    plot_payload_range,
    print_mission_energy_breakdown,
)
from visualizations.reference_aircraft import print_reference_aircraft
from visualizations.sizing_diagram import plot_sizing_diagram, print_sizing_diagram

if TYPE_CHECKING:
    from aircraft import BatteryAircraft
    from reference_aircraft import ReferenceAircraft

__all__ = [
    "interactive_plot_menu",
    "plot_aircraft_geometry",
    "plot_mass_breakdown",
    "plot_mission_energy",
    "plot_payload_range",
    "plot_sizing_diagram",
    "print_aircraft_summary",
    "print_mission_energy_breakdown",
    "print_reference_aircraft",
    "print_sizing_diagram",
]


def interactive_plot_menu(
    aircraft: BatteryAircraft, ref_aircraft: ReferenceAircraft
) -> None:
    """CLI selection menu allowing the user to select which visualization to display."""
    menu_text = """
======================================================================
               AIRCRAFT DESIGN - PLOT MENU
======================================================================
  [1] Sizing Diagram (Matching Chart & Design Point)
  [2] Mass Breakdown (Comparison with Do 228)
  [3] Mission Energy Breakdown (Simple Variant - matches active MTOM)
  [3d] Mission Energy Breakdown (Detailed Variant - analytical segments)
  [4] Payload-Range Diagram
  [5] Aircraft Dimensions & 2D Geometry Comparison
  [A] Show All Plots
  [Q] Exit Menu
======================================================================
"""
    while True:
        print(menu_text)
        try:
            choice = input("Select a diagram (number/letter): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting plot menu.")
            break

        if choice in ("q", "quit", "exit", "0"):
            print("Plot menu exited.")
            break
        elif choice in ("1", "s", "sizing"):
            print("Opening Sizing Diagram...")
            plot_sizing_diagram()
        elif choice in ("2", "m", "mass"):
            print("Opening Mass Breakdown Comparison...")
            plot_mass_breakdown(aircraft, ref_aircraft)
        elif choice in ("3", "e", "energy", "simple"):
            print("Opening Mission Energy Breakdown (Simple Variant)...")
            plot_mission_energy(aircraft, ref_aircraft, variant="simple")
        elif choice in ("3d", "detailed"):
            print("Opening Mission Energy Breakdown (Detailed Variant)...")
            plot_mission_energy(aircraft, ref_aircraft, variant="detailed")
        elif choice in ("4", "p", "payload", "range"):
            print("Opening Payload-Range Diagram...")
            plot_payload_range(aircraft)
        elif choice in ("5", "g", "geom", "geometry", "dimensions"):
            print("Opening Aircraft Dimensions & Geometry Comparison...")
            plot_aircraft_geometry(aircraft, ref_aircraft)
        elif choice in ("a", "all"):
            print("Opening all diagrams sequentially...")
            plot_sizing_diagram()
            plot_mass_breakdown(aircraft, ref_aircraft)
            plot_mission_energy(aircraft, ref_aircraft, variant="simple")
            plot_payload_range(aircraft)
            plot_aircraft_geometry(aircraft, ref_aircraft)
        else:
            print(
                f"Unknown option '{choice}'. Please choose 1, 2, 3, 3d, 4, 5, A or Q."
            )
