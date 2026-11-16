"""Battery-powered electric aircraft model with integrated calibrated mass estimation."""

from cog import CenterOfGravity
from constants import GRAVITY
from data import Constraints, DesignParameters, SiValue
from empennage import EmpennageDesign
from formulas.breguet import calc_electric_range
from formulas.mass import (
    calc_landing_gear_mass,
    calc_pylons_mass,
    calc_systems_mass,
)
from fuselage import FuselageDesign
from mission_energy import MissionEnergyCalculator, ReferenceMissionCalculator
from reference_aircraft import ReferenceAircraft
from sizing_diagram import SizingDiagram, SizingMode
from wing import WingDesign


class BatteryAircraft:
    """Represents a battery-electric aircraft with integrated mass estimation and performance sizing."""

    def __init__(
        self,
        constraints: Constraints,
        design: DesignParameters,
        ref: ReferenceAircraft,
        mtom: SiValue | None = None,
        sizing_mode: SizingMode = "thrust",
    ) -> None:
        self.constraints = constraints
        self.design = design
        self.ref = ref
        self.ref_mission = ReferenceMissionCalculator(constraints, ref.data)
        self.mtom: SiValue = (
            mtom if mtom is not None else design.initialSizing.maximumTakeOffMass.si
        )
        self.sizing_mode: SizingMode = sizing_mode
        self._sizing_diagrams: dict[tuple[SizingMode, float], SizingDiagram] = {}

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

    @property
    def fuselage(self) -> FuselageDesign:
        """Fuselage geometry and cabin layout design calculator."""
        return FuselageDesign(self.constraints, self.design, self.ref)

    @property
    def empennage(self) -> EmpennageDesign:
        """Empennage sizing and mass calculator bound to current wing state."""
        return EmpennageDesign(self.design, self.ref, self.wing)

    @property
    def cog(self) -> CenterOfGravity:
        """Longitudinal Center of Gravity (CoG) and loading excursion analyzer."""
        return CenterOfGravity(self)

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

    def sizing_diagram(self, mode: SizingMode | None = None) -> SizingDiagram:
        """Builds or returns a cached sizing diagram for the active mode and MTOM."""
        active_mode = mode or self.sizing_mode
        key = (active_mode, self.mtom)
        if key not in self._sizing_diagrams:
            self._sizing_diagrams[key] = SizingDiagram(
                self.constraints,
                self.design,
                self.ref,
                mode=active_mode,
                mtom=self.mtom,
            )
        return self._sizing_diagrams[key]

    @property
    def wing_loading_design(self) -> float:
        """Optimum wing loading from sizing diagram [kg/m^2]."""
        return self.sizing_diagram().design_wing_loading

    @property
    def thrust_loading_design(self) -> float:
        """Optimum thrust loading from thrust-based sizing diagram [-]."""
        return self.sizing_diagram(mode="thrust").design_thrust_loading

    @property
    def power_loading_design(self) -> SiValue:
        """Optimum specific take-off shaft power from power-based sizing diagram [W/kg]."""
        return self.sizing_diagram(mode="power").design_power_loading

    @property
    def total_takeoff_thrust(self) -> SiValue:
        """Total required take-off thrust T_TO [N]."""
        return SiValue(self.thrust_loading_design * self.mtom * GRAVITY, "N")

    @property
    def required_takeoff_power(self) -> SiValue:
        """Total required take-off shaft power P_0 from power sizing diagram [W]."""
        return SiValue(self.power_loading_design * self.mtom, "W")

    @property
    def total_takeoff_power(self) -> SiValue:
        """Total installed take-off shaft power [W]."""
        return SiValue(
            self.design.propulsion.engineTakeOffPower.si
            * self.design.propulsion.numberOfEngines.value,
            "W",
        )

    # --------------------------------------------------------------------------
    # Calibrated Structural Component Masses
    # --------------------------------------------------------------------------

    @property
    def m_landing_gear(self) -> SiValue:
        """Calibrated landing gear mass [kg]."""
        raw = calc_landing_gear_mass(self.mtom)
        return SiValue(raw * self.ref.landing_gear_calibration_factor, "kg")

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
            self.wing.mass
            + self.fuselage.mass
            + self.m_landing_gear
            + self.empennage.mass
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

        # Simpler approach: scale 100 NM reference mission via fuel fractions,
        # then add any additional cruise range (+ route reserve) via electric Breguet.
        range_fuel = (
            self.ref.data.fuel.climb
            + self.ref.data.fuel.cruise
            + self.ref.data.fuel.descent
        )
        ref_range = self.ref.data.fuel.referenceRange.si
        ref_range_energy = self.mission_energy.cruise_energy(ref_range)
        energy_per_kg = ref_range_energy / range_fuel
        e_ref_mission = energy_per_kg * self.ref.data.fuel.total

        delta_range = SiValue(self.design.mission.range.si - ref_range, "m")
        e_delta_range = (
            1.0 + self.constraints.mission.routeReserve
        ) * self.mission_energy.cruise_energy(delta_range)
        e_mission = SiValue(e_ref_mission + e_delta_range, "J")
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
