"""Reference aircraft model (Dornier 228) with datasheet parameters and derived calculations.

Combines catalog specifications from ``reference_aircraft.json`` with derived geometry,
tail volume coefficients, cruise aerodynamics, and component mass calibration factors.
"""

import math
from pathlib import Path

from constants import GRAVITY, isa_density
from data import SiValue
from data.loader import load_reference_aircraft_data
from data.reference_aircraft_data import ReferenceAircraftData
from formulas.aerodynamics import (
    calc_cf_flat_plate_turbulent,
    calc_effective_reynolds_number,
    calc_form_factor_wing,
    calc_mach_number,
    calc_reynolds_number,
)
from formulas.geometry import (
    calc_aspect_ratio,
    calc_horizontal_tail_volume_coefficient,
    calc_mean_aerodynamic_chord,
    calc_vertical_tail_volume_coefficient,
)
from formulas.mass_formulas import (
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
    calc_wing_mass,
)


class ReferenceAircraft:
    """Reference aircraft (Dornier 228) with catalog parameters and derived properties."""

    def __init__(self, data: ReferenceAircraftData) -> None:
        self.data = data

    @property
    def aspect_ratio(self) -> float:
        """Wing aspect ratio AR = b_W^2 / S_W [-]."""
        return calc_aspect_ratio(
            self.data.dimensions.wingspan.si, self.data.dimensions.wingArea.si
        )

    @property
    def mean_aerodynamic_chord(self) -> SiValue:
        """Mean aerodynamic chord c_mu [m]."""
        return calc_mean_aerodynamic_chord(
            self.data.dimensions.wingArea.si, self.data.dimensions.wingspan.si
        )

    @property
    def structural_wingspan(self) -> SiValue:
        """Structural wingspan b_s adjusted for sweep [m]."""
        sweep_rad = math.radians(self.data.assumptions.wingSweepHalfChord)
        return SiValue(self.data.dimensions.wingspan.si / math.cos(sweep_rad), "m")

    @property
    def fuselage_wetted_area(self) -> SiValue:
        """Approximate wetted fuselage surface area S_O [m^2] (elliptical cylinder)."""
        b_r = self.data.dimensions.fuselageWidth.si
        h_r = self.data.dimensions.fuselageHeight.si
        l_r = self.data.dimensions.fuselageLength.si
        return SiValue(math.pi * ((b_r + h_r) / 2.0) * l_r, "m^2")

    @property
    def horizontal_tail_lever_arm(self) -> SiValue:
        """Horizontal tail lever arm r_H [m]."""
        return self.data.assumptions.horizontalTailLeverArm.si

    @property
    def vertical_tail_lever_arm(self) -> SiValue:
        """Vertical tail lever arm r_V [m]."""
        return self.data.assumptions.verticalTailLeverArm.si

    @property
    def horizontal_tail_volume_coefficient(self) -> float:
        """Horizontal tail volume coefficient c_HT [-]."""
        return calc_horizontal_tail_volume_coefficient(
            self.data.dimensions.horizontalTailArea.si,
            self.horizontal_tail_lever_arm,
            self.data.dimensions.wingArea.si,
            self.mean_aerodynamic_chord,
        )

    @property
    def vertical_tail_volume_coefficient(self) -> float:
        """Vertical tail volume coefficient c_VT [-]."""
        return calc_vertical_tail_volume_coefficient(
            self.data.dimensions.verticalTailArea.si,
            self.vertical_tail_lever_arm,
            self.data.dimensions.wingArea.si,
            self.data.dimensions.wingspan.si,
        )

    @property
    def ultimate_load_factor(self) -> float:
        """Ultimate load factor n_ult = 1.5 * n_max [-]."""
        return 1.5 * self.data.assumptions.limitLoad.si

    @property
    def design_diving_speed(self) -> SiValue:
        """Design diving speed v_D = 1.25 * v_cruise [m/s]."""
        return SiValue(1.25 * self.data.mission.cruiseSpeedTAS.si, "m/s")

    @property
    def cruise_dynamic_pressure(self) -> float:
        """Cruise dynamic pressure q [N/m^2]."""
        rho_cruise = isa_density(self.data.mission.cruiseAltitude.si).si
        v_cruise = self.data.mission.cruiseSpeedTAS.si
        return 0.5 * rho_cruise * (v_cruise**2)

    @property
    def cruise_lift_coefficient(self) -> float:
        """Cruise lift coefficient c_A,cruise [-] (stationary horizontal flight: L = W = m_ref * g)."""
        m_ref = self.data.fuel.referenceMass.si
        s_w = self.data.dimensions.wingArea.si
        return (m_ref * GRAVITY.si) / (self.cruise_dynamic_pressure * s_w)

    @property
    def induced_drag_coefficient(self) -> float:
        """Induced drag coefficient c_Wi [-] (c_Wi = c_A^2 / (pi * AR * e))."""
        return (self.cruise_lift_coefficient**2) / (
            math.pi * self.aspect_ratio * self.data.aerodynamics.oswaldFactor
        )

    @property
    def zero_lift_drag_coefficient(self) -> float:
        """Total zero-lift drag coefficient c_W0 [-] (c_W0 = (c_A / E) - c_Wi)."""
        c_w_cruise = (
            self.cruise_lift_coefficient / self.data.aerodynamics.liftToDragRatioCruise
        )
        return c_w_cruise - self.induced_drag_coefficient

    @property
    def wing_zero_lift_drag_coefficient(self) -> float:
        """Wing zero-lift drag coefficient c_W0,wing [-]."""
        v_cruise = self.data.mission.cruiseSpeedTAS.si
        h_cruise = self.data.mission.cruiseAltitude.si
        c_mu = self.mean_aerodynamic_chord
        mach_cruise = calc_mach_number(v_cruise, h_cruise)
        re_wing = calc_reynolds_number(v_cruise, c_mu, h_cruise)
        k_roughness = SiValue(6.34e-6, "m")
        re_eff = calc_effective_reynolds_number(re_wing, c_mu, k_roughness, mach_cruise)
        cf_wing = calc_cf_flat_plate_turbulent(re_eff, mach_cruise)
        t_over_c = self.data.assumptions.wingRootThickness.si / c_mu
        sweep_deg = self.data.assumptions.wingSweepHalfChord
        ff_wing = calc_form_factor_wing(
            d_over_l=t_over_c,
            x_d_over_l=0.35,
            mach=mach_cruise,
            sweep_d_max_deg=sweep_deg,
        )
        if_wing = 1.0
        return 2.0 * cf_wing * ff_wing * if_wing

    @property
    def wing_estimated_mass(self) -> SiValue:
        """Uncalibrated formula estimation of wing mass [kg]."""
        return calc_wing_mass(
            self.data.mass.zeroFuelMassMax.si,
            self.structural_wingspan,
            self.ultimate_load_factor,
            self.data.assumptions.wingRootThickness.si,
            self.data.dimensions.wingArea.si,
            self.data.assumptions.wingMassPenaltyFactor,
        )

    @property
    def wing_calibration_factor(self) -> float:
        """Calibration factor for wing mass estimation [-]."""
        return self.data.mass.wing / self.wing_estimated_mass

    @property
    def fuselage_estimated_mass(self) -> SiValue:
        """Uncalibrated formula estimation of fuselage mass [kg]."""
        return calc_fuselage_mass(
            self.design_diving_speed,
            self.horizontal_tail_lever_arm,
            self.data.dimensions.fuselageWidth.si,
            self.data.dimensions.fuselageHeight.si,
            self.fuselage_wetted_area,
            self.data.assumptions.fuselageMassPenaltyFactor,
        )

    @property
    def fuselage_calibration_factor(self) -> float:
        """Calibration factor for fuselage mass estimation [-]."""
        return self.data.mass.fuselage / self.fuselage_estimated_mass

    @property
    def landing_gear_estimated_mass(self) -> SiValue:
        """Uncalibrated formula estimation of landing gear mass [kg]."""
        return calc_landing_gear_mass(self.data.mass.takeOffMassMax.si)

    @property
    def landing_gear_calibration_factor(self) -> float:
        """Calibration factor for landing gear mass estimation [-]."""
        return self.data.mass.landingGear / self.landing_gear_estimated_mass

    @property
    def empennage_estimated_mass(self) -> SiValue:
        """Uncalibrated formula estimation of empennage mass [kg]."""
        return calc_empennage_mass(
            self.ultimate_load_factor,
            self.data.dimensions.horizontalTailArea.si,
            self.data.dimensions.verticalTailArea.si,
        )

    @property
    def empennage_calibration_factor(self) -> float:
        """Calibration factor for empennage mass estimation [-]."""
        return self.data.mass.empennage / self.empennage_estimated_mass

    @property
    def pylons_estimated_mass(self) -> SiValue:
        """Uncalibrated formula estimation of engine pylons mass [kg]."""
        return calc_pylons_mass(self.data.propulsion.totalTakeOffPower.si)

    @property
    def pylons_calibration_factor(self) -> float:
        """Calibration factor for engine pylons mass estimation [-]."""
        return self.data.mass.pylons / self.pylons_estimated_mass

    @property
    def systems_estimated_mass(self) -> SiValue:
        """Uncalibrated formula estimation of systems mass [kg]."""
        return calc_systems_mass(self.data.mass.takeOffMassMax.si)

    @property
    def systems_calibration_factor(self) -> float:
        """Calibration factor for systems mass estimation [-]."""
        return self.data.mass.systems / self.systems_estimated_mass


def load_reference_aircraft(path: Path | str | None = None) -> ReferenceAircraft:
    """Loads reference aircraft JSON data and returns an initialized ``ReferenceAircraft``."""
    return ReferenceAircraft(load_reference_aircraft_data(path))


def print_reference_aircraft(ref: ReferenceAircraft) -> None:
    """Prints a structured summary of reference aircraft given inputs and calculated values."""
    print("=" * 65)
    print("                      REFERENCE AIRCRAFT")
    print("=" * 65)

    print("\n--- GIVEN PARAMETERS (FROM JSON) ---")
    print(f"MTOM:                            {ref.data.mass.takeOffMassMax}")
    print(f"MLM:                             {ref.data.mass.landingMassMax}")
    print(f"MZFM:                            {ref.data.mass.zeroFuelMassMax}")
    print(f"Wing area (S_W):                 {ref.data.dimensions.wingArea}")
    print(f"Wingspan (b_W):                  {ref.data.dimensions.wingspan}")
    print(f"Fuselage length (l_R):           {ref.data.dimensions.fuselageLength}")
    print(f"Fuselage width (b_R):            {ref.data.dimensions.fuselageWidth}")
    print(f"Fuselage height (h_R):           {ref.data.dimensions.fuselageHeight}")
    print(f"Horizontal tail area (S_HTP):    {ref.data.dimensions.horizontalTailArea}")
    print(f"Vertical tail area (S_VTP):      {ref.data.dimensions.verticalTailArea}")
    print(f"Limit load factor (n_max):       {ref.data.assumptions.limitLoad}")

    print("\n--- CALCULATED VALUES (DERIVED) ---")
    print(f"Aspect ratio (AR):                   {ref.aspect_ratio:.3f}")
    print(f"Mean aerodynamic chord (c_mu):       {ref.mean_aerodynamic_chord:.3f}")
    print(f"Ultimate load factor (n_ult):        {ref.ultimate_load_factor:.2f}")
    print(f"Horizontal tail arm (r_H):           {ref.horizontal_tail_lever_arm}")
    print(
        f"Horizontal tail volume coeff (c_HT): {ref.horizontal_tail_volume_coefficient:.4f}"
    )
    print(f"Vertical tail arm (r_V):             {ref.vertical_tail_lever_arm}")
    print(
        f"Vertical tail volume coeff (c_VT):   {ref.vertical_tail_volume_coefficient:.4f}"
    )
    print(f"Cruise lift coefficient (c_A):       {ref.cruise_lift_coefficient:.4f}")
    print(f"Total zero-lift drag (c_W0):         {ref.zero_lift_drag_coefficient:.4f}")
    print(f"Induced drag coeff (c_Wi):           {ref.induced_drag_coefficient:.4f}")
    print(
        f"Wing zero-lift drag (c_W0,wing):     {ref.wing_zero_lift_drag_coefficient:.4f}"
    )

    print("\n--- FORMULA MASS ESTIMATIONS & CALIBRATION FACTORS ---")
    print(
        f"Wing:         Catalog: {ref.data.mass.wing:>7} | Formula: {ref.wing_estimated_mass:>10.2f} | Factor: {ref.wing_calibration_factor:.4f}"
    )
    print(
        f"Fuselage:     Catalog: {ref.data.mass.fuselage:>7} | Formula: {ref.fuselage_estimated_mass:>10.2f} | Factor: {ref.fuselage_calibration_factor:.4f}"
    )
    print(
        f"Empennage:    Catalog: {ref.data.mass.empennage:>7} | Formula: {ref.empennage_estimated_mass:>10.2f} | Factor: {ref.empennage_calibration_factor:.4f}"
    )
    print(
        f"Landing gear: Catalog: {ref.data.mass.landingGear:>7} | Formula: {ref.landing_gear_estimated_mass:>10.2f} | Factor: {ref.landing_gear_calibration_factor:.4f}"
    )
    print(
        f"Pylons:       Catalog: {ref.data.mass.pylons:>7} | Formula: {ref.pylons_estimated_mass:>10.2f} | Factor: {ref.pylons_calibration_factor:.4f}"
    )
    print(
        f"Systems:      Catalog: {ref.data.mass.systems:>7} | Formula: {ref.systems_estimated_mass:>10.2f} | Factor: {ref.systems_calibration_factor:.4f}"
    )
    print("=" * 65 + "\n")


if __name__ == "__main__":
    print_reference_aircraft(load_reference_aircraft())
