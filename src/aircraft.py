"""Battery-powered electric aircraft model with integrated calibrated mass estimation."""

import math

from constants import GRAVITY
from data import Constraints, DesignParameters, ReferenceAircraft, SiValue
from fuel_fractions import (
    calc_battery_pack_mass,
    calc_total_mission_energy,
    calc_trip_energy,
)
from formulas import (
    calc_electric_battery_mass_from_range,
    calc_electric_range,
    calc_empennage_mass,
    calc_fuselage_mass,
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
    calc_wing_mass,
)


class BatteryAircraft:
    """Represents a battery-electric aircraft with integrated mass estimation and performance sizing."""

    def __init__(
        self,
        constraints: Constraints,
        design: DesignParameters,
        ref: ReferenceAircraft,
        mtom: SiValue | None = None,
        eta_electric: float = 0.85,
    ) -> None:
        self.constraints = constraints
        self.design = design
        self.ref = ref
        self.eta_electric = eta_electric
        self.mtom: SiValue = (
            mtom if mtom is not None else design.initialSizing.maximumTakeOffMass.si
        )

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
        """Propulsion engine mass [kg] (adopted from reference aircraft)."""
        return self.ref.mass.engine.si

    # --------------------------------------------------------------------------
    # Calibrated Structural Component Masses
    # --------------------------------------------------------------------------

    @property
    def m_wing(self) -> SiValue:
        """Calibrated wing mass [kg]."""
        raw = calc_wing_mass(
            mzfm=self.mtom,
            b_s=self.ref.calculatedValues.structuralWingspan.si,
            n_ult=self.ref.calculatedValues.ultimateLoadFactor.value,
            d_root=self.ref.assumptions.wingRootThickness.si,
            s_w=self.ref.dimensions.wingArea.si,
            delta_m_F=self.ref.assumptions.wingMassPenaltyFactor.value,
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
        p_to = self.ref.propulsion.totalTakeOffPower.si
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

    def calc_required_battery_mass(self, include_reserves: bool = True) -> SiValue:
        """Calculates required battery pack mass for the complete mission via fuel_fractions [kg].

        Args:
            include_reserves: Whether to include reserve energy (route, loiter, diversion).

        Returns:
            Required battery pack mass [kg].
        """
        e_mission = calc_total_mission_energy(self.mtom)
        print("E-Mission:", e_mission)
        return calc_battery_pack_mass(e_mission)

    def converge_mtom(
        self,
        include_reserves: bool = True,
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
        history = [float(self.mtom)]

        for _ in range(max_iterations):
            m_bat_req = self.calc_required_battery_mass(include_reserves=include_reserves)
            new_mtom = SiValue(
                self.m_operating_empty + self.m_payload + m_bat_req,
                "kg",
            )
            print(self.mtom, m_bat_req, self.m_operating_empty, self.m_payload, new_mtom)
            history.append(float(new_mtom))

            if abs(float(new_mtom) - float(self.mtom)) < tolerance:
                self.mtom = new_mtom
                break

            self.mtom = new_mtom

        return history
