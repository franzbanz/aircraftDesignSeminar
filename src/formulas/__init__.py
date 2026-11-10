"""Formulas package exporting active aerodynamics, mass, geometry, Breguet, and propulsion functions."""

from formulas.aerodynamics import (
    AerodynamicComponent,
    calc_cf_flat_plate_laminar,
    calc_cf_flat_plate_turbulent,
    calc_component_drag_area,
    calc_cruise_lift_coefficient,
    calc_delta_cf_body_laminar,
    calc_delta_cf_body_turbulent,
    calc_dynamic_pressure,
    calc_effective_reynolds_number,
    calc_form_factor_fuselage,
    calc_form_factor_wing,
    calc_mach_number,
    calc_reynolds_number,
    calc_zero_lift_drag_coefficient,
)
from formulas.breguet import (
    calc_breguet_fuel_mass_from_endurance,
    calc_breguet_fuel_mass_from_range,
    calc_breguet_range,
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
    calc_wingspan,
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
    # Aerodynamics
    "AerodynamicComponent",
    "calc_cf_flat_plate_laminar",
    "calc_cf_flat_plate_turbulent",
    "calc_cruise_lift_coefficient",
    "calc_delta_cf_body_laminar",
    "calc_delta_cf_body_turbulent",
    "calc_dynamic_pressure",
    "calc_effective_reynolds_number",
    "calc_form_factor_wing",
    "calc_form_factor_fuselage",
    "calc_mach_number",
    "calc_reynolds_number",
    "calc_component_drag_area",
    "calc_zero_lift_drag_coefficient",
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
    "calc_wingspan",
    # Conventional & Electric Breguet
    "calc_breguet_range",
    "calc_breguet_fuel_mass_from_range",
    "calc_breguet_fuel_mass_from_endurance",
    "calc_electric_range",
    "calc_electric_cruise_energy",
    "calc_electric_loiter_energy",
    # Propulsion
    "calc_thrust_loading_from_power",
    "calc_cruise_thrust_and_power",
]
