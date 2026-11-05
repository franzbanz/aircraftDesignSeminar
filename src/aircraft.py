"""Battery-powered electric aircraft model with integrated calibrated mass estimation."""
from formulas.geometry import wing_span
from sizing_diagram import get_design_point

import math

from constants import GRAVITY
from data import Constraints, DesignParameters, ReferenceAircraft, SiValue
from fuel_fractions import MissionEnergyCalculator
from formulas import (
    calc_electric_battery_mass_from_range,
    calc_electric_range,
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
    calc_wing_mass, calc_mean_aerodynamic_chord,
)


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
        self.mtom: SiValue = (
            mtom if mtom is not None else design.initialSizing.maximumTakeOffMass.si
        )

    @property
    def eta_electric(self) -> float:
        """Overall electric powertrain efficiency [-]."""
        return self.design.propulsion.etaElectric

    # --------------------------------------------------------------------------
    # Fixed Operational & Payload Masses
    # --------------------------------------------------------------------------

    @property
    def m_payload(self) -> SiValue:
        """Passenger and luggage payload mass [kg]."""
        return SiValue(
            self.constraints.payload.weightPerPassenger.si
            * self.constraints.payload.numberOfPassengers.value,
            "kg",
        )

    @property
    def m_operator_items(self) -> SiValue:
        """Operator items mass [kg] (adopted from reference aircraft)."""
        return self.ref.mass.operatorItems.si

    @property
    def m_furnishings(self) -> SiValue:
        """Cabin furnishings mass [kg] (adopted from reference aircraft)."""
        return self.ref.mass.furnishings.si

    @property
    def m_engine(self) -> SiValue:
        """Propulsion engine mass [kg] (scaled by number of engines)."""
        return SiValue(
            self.design.propulsion.numberOfEngines.value * self.design.propulsion.engineMass.si,
            "kg",
        )

    # --------------------------------------------------------------------------
    # Calibrated Structural Component Masses
    # --------------------------------------------------------------------------

    @property
    def m_wing(self) -> SiValue:
        """Calibrated wing mass [kg]."""
        constraint_mtom = self.constraints.performance.takeOffMassMax.si
        mtom = self.mtom if self.mtom < constraint_mtom else constraint_mtom
        s_w = SiValue(mtom / get_design_point()[0], "m^2")
        b_s = wing_span(s_w, self.design.aerodynamics.aspectRatio)
        # constrain max wing span
        if b_s > self.design.aerodynamics.maxWingSpan.si:
            b_s = self.design.aerodynamics.maxWingSpan.si
        d_root = calc_mean_aerodynamic_chord(s_w, b_s)
        raw = calc_wing_mass(
            mzfm=self.mtom,
            b_s=b_s,
            n_ult=self.design.assumptions.limitLoad * 1.5,
            d_root=d_root,
            s_w=s_w,
            delta_m_F=self.design.assumptions.wingMassPenaltyFactor.value,
        )
        return SiValue(raw * self.ref.calculatedValues.wingCalibrationFactor, "kg")

    @property
    def m_fuselage(self) -> SiValue:
        """Calibrated fuselage mass [kg]."""
        v_D = SiValue(1.25 * self.constraints.performance.cruiseSpeedMin.si, "m/s")
        r_H = self.ref.calculatedValues.horizontalTailLeverArm.si
        b_R = self.ref.dimensions.fuselageWidth.si
        h_R = self.ref.dimensions.fuselageHeight.si
        l_R = self.ref.dimensions.fuselageLength.si
        delta_m_F = 0.07  # Fuselage-mounted landing gear (+7%)
        s_o = SiValue(math.pi * ((b_R + h_R) / 2.0) * l_R, "m^2")
        raw = calc_fuselage_mass(v_D, r_H, b_R, h_R, s_o, delta_m_F)
        return SiValue(raw * self.ref.calculatedValues.fuselageCalibrationFactor, "kg")

    @property
    def m_landing_gear(self) -> SiValue:
        """Calibrated landing gear mass [kg]."""
        raw = calc_landing_gear_mass(self.mtom)
        return SiValue(raw * self.ref.calculatedValues.landingGearCalibrationFactor, "kg")

    @property
    def m_empennage(self) -> SiValue:
        """Calibrated empennage mass [kg]."""
        n_ult = self.ref.calculatedValues.ultimateLoadFactor.value
        s_htp = self.ref.dimensions.horizontalTailArea.si
        s_vtp = self.ref.dimensions.verticalTailArea.si
        raw = calc_empennage_mass(n_ult, s_htp, s_vtp)
        return SiValue(raw * self.ref.calculatedValues.empennageCalibrationFactor, "kg")

    @property
    def m_pylons(self) -> SiValue:
        """Calibrated engine pylons/cowling mass [kg]."""
        p_to = SiValue(self.design.propulsion.engineTakeOffPower.si * self.design.propulsion.numberOfEngines, "W")
        raw = calc_pylons_mass(p_to)
        return SiValue(raw * self.ref.calculatedValues.pylonsCalibrationFactor, "kg")

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
        return SiValue(raw * self.ref.calculatedValues.systemsCalibrationFactor.value, "kg")

    @property
    def m_empty(self) -> SiValue:
        """Manufacturer's Empty Weight (MEW) excluding battery [kg]."""
        return SiValue(
            self.m_structure
            + self.m_engine
            + self.m_systems
            + self.m_furnishings,
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
            / self.constraints.battery.cellToPackFactorMin.value,
            "J/kg",
        )

    @property
    def range(self) -> SiValue:
        """Achievable cruise range with available battery mass using pack energy density [m]."""
        return calc_electric_range(
            battery_energy_density=self.battery_pack_energy_density,
            eta_electric=self.eta_electric,
            lift_to_drag=self.design.aerodynamics.liftToDragRatioCruise,
            battery_mass=self.m_battery,
            take_off_mass=self.mtom,
        )

    @property
    def mission_energy(self) -> MissionEnergyCalculator:
        """Mission energy calculator bound to current aircraft state."""
        return MissionEnergyCalculator(
            constraints=self.constraints,
            design=self.design,
            ref=self.ref,
            mtom=self.mtom,
        )

    def calc_required_battery_mass(self) -> SiValue:
        """Calculates required battery pack mass for the complete mission [kg].

        Returns:
            Required battery pack mass [kg].
        """
        # Detailed segment-by-segment calculation:
        # return self.mission_energy.battery_pack_mass()

        # Simpler approach:
        range_fuel = self.ref.fuel.climb + self.ref.fuel.cruise + self.ref.fuel.descent
        range_energy = self.mission_energy.cruise_energy(self.design.mission.range.si)
        energy_per_kg = range_energy / range_fuel
        e_mission = SiValue(energy_per_kg * self.ref.fuel.total, "J")
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
