"""Battery-powered electric aircraft model with integrated calibrated mass estimation."""

import math

from constants import GRAVITY
from data import Constraints, DesignParameters, SiValue
from formulas import (
    calc_electric_range,
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_horizontal_tail_area,
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
    calc_vertical_tail_area,
)
from fuel_fractions import MissionEnergyCalculator, ReferenceMissionCalculator
from reference_aircraft import ReferenceAircraft
from sizing_diagram import SizingDiagram
from wing_design import WingDesign


class BatteryAircraft:
    """Represents a battery-electric aircraft with integrated mass estimation and performance sizing."""

    def __init__(
        self,
        constraints: Constraints,
        design: DesignParameters,
        ref: ReferenceAircraft,
        mtom: SiValue | None = None,
    ) -> None:
        self.constraints = constraints
        self.design = design
        self.ref = ref
        self.ref_mission = ReferenceMissionCalculator(constraints, ref.data)
        self.mtom: SiValue = (
            mtom if mtom is not None else design.initialSizing.maximumTakeOffMass.si
        )

    @property
    def eta_electric(self) -> float:
        """Overall electric powertrain efficiency [-]."""
        return self.design.propulsion.etaElectric

    @property
    def wing(self) -> WingDesign:
        """Wing and aerodynamic design calculator bound to current aircraft state."""
        return WingDesign(
            self.constraints,
            self.design,
            self.ref,
            self.mtom,
            self.wing_loading_design,
        )

    # --------------------------------------------------------------------------
    # Fixed Operational & Payload Masses
    # --------------------------------------------------------------------------

    @property
    def m_payload(self) -> SiValue:
        """Passenger and luggage payload mass [kg]."""
        return SiValue(
            self.constraints.payload.weightPerPassenger.si
            * self.design.mission.numberOfPassengers,
            "kg",
        )

    @property
    def m_operator_items(self) -> SiValue:
        """Operator items mass [kg] (adopted from reference aircraft)."""
        return self.ref.data.mass.operatorItems.si

    @property
    def m_furnishings(self) -> SiValue:
        """Cabin furnishings mass [kg] (adopted from reference aircraft)."""
        return self.ref.data.mass.furnishings.si

    @property
    def m_engine(self) -> SiValue:
        """Propulsion engine mass [kg] (scaled by number of engines)."""
        return SiValue(
            self.design.propulsion.numberOfEngines.value
            * self.design.propulsion.engineMass.si,
            "kg",
        )

    # --------------------------------------------------------------------------
    # Geometric Dimensions & Sizing
    # --------------------------------------------------------------------------

    @property
    def wing_loading_design(self) -> float:
        """Optimum wing loading from sizing diagram [kg/m^2]."""
        return SizingDiagram(
            self.constraints, self.design, self.ref
        ).design_wing_loading

    @property
    def thrust_loading_design(self) -> float:
        """Optimum thrust loading from sizing diagram [-]."""
        return SizingDiagram(
            self.constraints, self.design, self.ref
        ).design_thrust_loading

    @property
    def fuselage_length(self) -> SiValue:
        """Fuselage length [m]."""
        return self.design.fuselage.fuselageLength.si

    @property
    def fuselage_width(self) -> SiValue:
        """Fuselage width [m]."""
        return self.design.fuselage.fuselageWidth.si

    @property
    def fuselage_height(self) -> SiValue:
        """Fuselage height [m]."""
        return self.design.fuselage.fuselageHeight.si

    @property
    def horizontal_tail_area(self) -> SiValue:
        """Horizontal tailplane area S_HTP scaled via volume coefficient [m^2]."""
        c_ht = min(
            self.ref.horizontal_tail_volume_coefficient,
            self.design.aerodynamics.maxHorizontalVolumeCoefficient,
        )
        r_h = self.ref.horizontal_tail_lever_arm.si
        return calc_horizontal_tail_area(
            c_ht, r_h, self.wing.area, self.wing.mean_aerodynamic_chord
        )

    @property
    def vertical_tail_area(self) -> SiValue:
        """Vertical tailplane area S_VTP scaled via volume coefficient [m^2]."""
        c_vt = self.ref.vertical_tail_volume_coefficient
        r_v = self.ref.vertical_tail_lever_arm.si
        return calc_vertical_tail_area(c_vt, r_v, self.wing.area, self.wing.span)

    @property
    def total_takeoff_thrust(self) -> SiValue:
        """Total required take-off thrust T_TO [N]."""
        return SiValue(self.thrust_loading_design * self.mtom * GRAVITY, "N")

    @property
    def total_takeoff_power(self) -> SiValue:
        """Total required installed take-off power [W]."""
        return SiValue(
            self.design.propulsion.engineTakeOffPower.si
            * self.design.propulsion.numberOfEngines.value,
            "W",
        )

    # --------------------------------------------------------------------------
    # Calibrated Structural Component Masses
    # --------------------------------------------------------------------------

    @property
    def m_wing(self) -> SiValue:
        """Calibrated wing mass [kg]."""
        return self.wing.mass

    @property
    def m_fuselage(self) -> SiValue:
        """Calibrated fuselage mass [kg]."""
        v_D = SiValue(1.25 * self.design.mission.cruiseSpeedTAS.si, "m/s")
        r_H = self.ref.horizontal_tail_lever_arm.si
        b_R = self.fuselage_width
        h_R = self.fuselage_height
        l_R = self.fuselage_length
        delta_m_F = self.ref.data.assumptions.fuselageMassPenaltyFactor
        s_o = SiValue(math.pi * ((b_R + h_R) / 2.0) * l_R, "m^2")
        raw = calc_fuselage_mass(v_D, r_H, b_R, h_R, s_o, delta_m_F)
        return SiValue(raw * self.ref.fuselage_calibration_factor, "kg")

    @property
    def m_landing_gear(self) -> SiValue:
        """Calibrated landing gear mass [kg]."""
        raw = calc_landing_gear_mass(self.mtom)
        return SiValue(raw * self.ref.landing_gear_calibration_factor, "kg")

    @property
    def m_empennage(self) -> SiValue:
        """Calibrated empennage mass [kg]."""
        n_ult = self.design.assumptions.limitLoad * 1.5
        raw = calc_empennage_mass(
            n_ult, self.horizontal_tail_area, self.vertical_tail_area
        )
        return SiValue(raw * self.ref.empennage_calibration_factor, "kg")

    @property
    def m_pylons(self) -> SiValue:
        """Calibrated engine pylons/cowling mass [kg]."""
        p_to = SiValue(
            self.design.propulsion.engineTakeOffPower.si
            * self.design.propulsion.numberOfEngines,
            "W",
        )
        raw = calc_pylons_mass(p_to)
        return SiValue(raw * self.ref.pylons_calibration_factor, "kg")

    @property
    def m_structure(self) -> SiValue:
        """Total airframe structure mass [kg]."""
        return SiValue(
            self.m_wing
            + self.m_fuselage
            + self.m_landing_gear
            + self.m_empennage
            + self.m_pylons,
            "kg",
        )

    # --------------------------------------------------------------------------
    # Calibrated Systems & Group Masses
    # --------------------------------------------------------------------------

    @property
    def m_systems(self) -> SiValue:
        """Calibrated aircraft systems mass [kg]."""
        raw = calc_systems_mass(self.mtom)
        return SiValue(raw * self.ref.systems_calibration_factor, "kg")

    @property
    def m_empty(self) -> SiValue:
        """Manufacturer's Empty Weight (MEW) excluding battery [kg]."""
        return SiValue(
            self.m_structure + self.m_engine + self.m_systems + self.m_furnishings,
            "kg",
        )

    @property
    def m_operating_empty(self) -> SiValue:
        """Operating Empty Mass (OEM) excluding battery [kg]."""
        return SiValue(self.m_empty + self.m_operator_items, "kg")

    @property
    def m_battery_available(self) -> SiValue:
        """Remaining mass budget for the battery pack at current MTOM [kg]."""
        return SiValue(self.mtom - self.m_operating_empty - self.m_payload, "kg")

    @property
    def m_battery(self) -> SiValue:
        """Battery mass [kg] (alias for m_battery_available)."""
        return self.m_battery_available

    # --------------------------------------------------------------------------
    # Performance & Range
    # --------------------------------------------------------------------------

    @property
    def battery_pack_energy_density(self) -> SiValue:
        """Gravimetric battery pack energy density [J/kg]."""
        return SiValue(
            self.constraints.battery.cellEnergyDensityMax.si
            / self.constraints.battery.cellToPackFactorMin,
            "J/kg",
        )

    @property
    def range(self) -> SiValue:
        """Achievable cruise range with available battery mass using pack energy density [m]."""
        return calc_electric_range(
            self.battery_pack_energy_density,
            self.eta_electric,
            self.wing.lift_to_drag_cruise,
            self.m_battery,
            self.mtom,
        )

    @property
    def mission_energy(self) -> MissionEnergyCalculator:
        """Mission energy calculator bound to current aircraft state."""
        return MissionEnergyCalculator(
            self.constraints,
            self.design,
            self.ref_mission,
            self.mtom,
            lift_to_drag_cruise=self.wing.lift_to_drag_cruise,
        )

    def calc_required_battery_mass(self) -> SiValue:
        """Calculates required battery pack mass for the complete mission [kg].

        Returns:
            Required battery pack mass [kg].
        """
        # Detailed segment-by-segment calculation:
        # return self.mission_energy.battery_pack_mass()

        # Simpler approach:
        range_fuel = (
            self.ref.data.fuel.climb
            + self.ref.data.fuel.cruise
            + self.ref.data.fuel.descent
        )
        range_energy = self.mission_energy.cruise_energy(self.design.mission.range.si)
        energy_per_kg = range_energy / range_fuel
        e_mission = SiValue(energy_per_kg * self.ref.data.fuel.total, "J")
        return self.mission_energy.battery_pack_mass(e_mission)

    def converge_mtom(
        self,
        max_iterations: int = 100,
        tolerance: float = 0.1,
    ) -> list[float]:
        """Iterates MTOM until mass balance converges for the mission.

        Args:
            include_reserves: Whether to include reserves in battery sizing (default: True).
            max_iterations: Maximum iteration steps.
            tolerance: Convergence delta tolerance [kg].

        Returns:
            History of MTOM values during iteration [kg].
        """
        history = [self.mtom]

        for _ in range(max_iterations):
            m_bat_req = self.calc_required_battery_mass()
            new_mtom = SiValue(
                self.m_operating_empty + self.m_payload + m_bat_req,
                "kg",
            )
            history.append(new_mtom)

            if abs(new_mtom - self.mtom) < tolerance:
                self.mtom = new_mtom
                break

            self.mtom = new_mtom

        return history
