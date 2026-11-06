"""Formulas package exporting active mass, geometry, Breguet, and propulsion functions."""

from formulas.breguet import (
    calc_breguet_fuel_mass_from_endurance,
    calc_breguet_fuel_mass_from_range,
    calc_breguet_mass_fraction_from_endurance,
    calc_breguet_mass_fraction_from_range,
    calc_breguet_range,
    calc_electric_battery_mass_from_range,
    calc_electric_cruise_energy,
    calc_electric_loiter_energy,
    calc_electric_range,
)
from formulas.geometry import (
    calc_aspect_ratio,
    calc_horizontal_tail_area,
    calc_horizontal_tail_volume_coefficient,
    calc_mean_aerodynamic_chord,
    calc_vertical_tail_area,
    calc_vertical_tail_volume_coefficient,
    wing_span,
)
from formulas.mass_formulas import (
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
    calc_wing_mass,
)
from formulas.propulsion import (
    calc_cruise_thrust_and_power,
    calc_thrust_loading_from_power,
)

__all__ = [
    # Mass estimation
    "calc_wing_mass",
    "calc_landing_gear_mass",
    "calc_fuselage_mass",
    "calc_empennage_mass",
    "calc_pylons_mass",
    "calc_systems_mass",
    # Geometry
    "calc_mean_aerodynamic_chord",
    "calc_aspect_ratio",
    "calc_horizontal_tail_area",
    "calc_vertical_tail_area",
    "calc_horizontal_tail_volume_coefficient",
    "calc_vertical_tail_volume_coefficient",
    "wing_span",
    # Conventional & Electric Breguet
    "calc_breguet_range",
    "calc_breguet_mass_fraction_from_range",
    "calc_breguet_fuel_mass_from_range",
    "calc_breguet_mass_fraction_from_endurance",
    "calc_breguet_fuel_mass_from_endurance",
    "calc_electric_range",
    "calc_electric_battery_mass_from_range",
    "calc_electric_cruise_energy",
    "calc_electric_loiter_energy",
    # Propulsion
    "calc_thrust_loading_from_power",
    "calc_cruise_thrust_and_power",
]
