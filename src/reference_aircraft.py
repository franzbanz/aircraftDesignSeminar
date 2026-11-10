"""Reference aircraft model (Dornier 228) with datasheet parameters and derived calculations.

Combines catalog specifications from ``reference_aircraft.json`` with derived geometry,
tail volume coefficients, cruise aerodynamics, and component mass calibration factors.
"""

import math
from pathlib import Path

from data import SiValue
from data.loader import load_reference_aircraft_data
from data.reference_aircraft_data import ReferenceAircraftData
from formulas.aerodynamics import (
    calc_cruise_lift_coefficient,
    calc_wing_zero_lift_drag_coefficient,
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
    def wing_root_thickness(self) -> SiValue:
        """Wing thickness at root t_root = c_mu * rel_thickness [m]."""
        return SiValue(
            self.mean_aerodynamic_chord * self.data.assumptions.relWingThickness,
            "m",
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
    def cruise_lift_coefficient(self) -> float:
        """Cruise lift coefficient c_A,cruise [-] (stationary horizontal flight: L = W = m_ref * g)."""
        wing_loading = (
            self.data.fuel.referenceMass.si / self.data.dimensions.wingArea.si
        )
        return calc_cruise_lift_coefficient(
            wing_loading,
            self.data.mission.cruiseSpeedTAS.si,
            self.data.mission.cruiseAltitude.si,
        )

    @property
    def induced_drag_coefficient(self) -> float:
        """Induced drag coefficient c_Wi [-] (c_Wi = c_A^2 / (pi * AR * e))."""
        return (self.cruise_lift_coefficient**2) / (
            math.pi * self.aspect_ratio * self.data.assumptions.oswaldFactor
        )

    @property
    def zero_lift_drag_coefficient(self) -> float:
        """Total zero-lift drag coefficient c_W0 [-] from reference polar at C_L = 0."""
        return self.data.aerodynamics.zeroLiftDragCoefficient

    def drag_coefficient_from_polar(self, c_l: float) -> float:
        """Calculates drag coefficient C_D(C_L) = C_D0 + C_L^2 / (pi * AR * e) [-]."""
        return self.zero_lift_drag_coefficient + (c_l**2) / (
            math.pi * self.aspect_ratio * self.data.assumptions.oswaldFactor
        )

    def lift_to_drag_from_polar(self, c_l: float) -> float:
        """Calculates lift-to-drag ratio L/D = C_L / C_D(C_L) for a given lift coefficient C_L [-]."""
        if c_l <= 0.0:
            return 0.0
        return c_l / self.drag_coefficient_from_polar(c_l)

    @property
    def wing_zero_lift_drag_coefficient(self) -> float:
        """Wing zero-lift drag coefficient c_W0,wing [-]."""
        return calc_wing_zero_lift_drag_coefficient(
            velocity=self.data.mission.cruiseSpeedTAS.si,
            altitude=self.data.mission.cruiseAltitude.si,
            mean_aerodynamic_chord=self.mean_aerodynamic_chord,
            rel_thickness=self.data.assumptions.relWingThickness,
            sweep_deg=self.data.assumptions.wingSweepHalfChord,
        )

    @property
    def wing_estimated_mass(self) -> SiValue:
        """Uncalibrated formula estimation of wing mass [kg]."""
        return calc_wing_mass(
            self.data.mass.zeroFuelMassMax.si,
            self.structural_wingspan,
            self.ultimate_load_factor,
            self.wing_root_thickness,
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


if __name__ == "__main__":
    from visualizations.reference_aircraft import print_reference_aircraft

    print_reference_aircraft(load_reference_aircraft())
