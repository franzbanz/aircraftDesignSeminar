"""Formulas package exporting the relevant mass, geometry, Breguet, and propulsion functions."""

from formulas.breguet import (
    calc_breguet_endurance,
    calc_breguet_fuel_mass_from_endurance,
    calc_breguet_fuel_mass_from_range,
    calc_breguet_range,
    calc_electric_battery_mass_from_range,
    calc_electric_cruise_energy,
    calc_electric_loiter_energy,
    calc_electric_range,
)
from formulas.geometry import (
    calc_horizontal_tail_volume_coefficient,
    calc_mean_aerodynamic_chord,
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
    calc_electric_power_from_shaft_power,
    calc_electric_power_from_thrust,
    calc_electric_power_from_thrust_loading,
    calc_shaft_power_from_electric_power,
    calc_thrust_from_electric_power,
    calc_thrust_from_thrust_loading,
    calc_thrust_loading_from_electric_power,
    calc_thrust_loading_from_thrust,
)

__all__ = [
    "calc_wing_mass",
    "calc_landing_gear_mass",
    "calc_fuselage_mass",
    "calc_empennage_mass",
    "calc_pylons_mass",
    "calc_systems_mass",
    "calc_mean_aerodynamic_chord",
    "calc_horizontal_tail_volume_coefficient",
    "calc_vertical_tail_volume_coefficient",
    "wing_span",
    "calc_breguet_range",
    "calc_breguet_fuel_mass_from_range",
    "calc_breguet_endurance",
    "calc_breguet_fuel_mass_from_endurance",
    "calc_electric_range",
    "calc_electric_battery_mass_from_range",
    "calc_electric_cruise_energy",
    "calc_electric_loiter_energy",
    "calc_electric_power_from_shaft_power",
    "calc_shaft_power_from_electric_power",
    "calc_electric_power_from_thrust",
    "calc_thrust_from_electric_power",
    "calc_electric_power_from_thrust_loading",
    "calc_thrust_loading_from_electric_power",
    "calc_thrust_from_thrust_loading",
    "calc_thrust_loading_from_thrust",
]
