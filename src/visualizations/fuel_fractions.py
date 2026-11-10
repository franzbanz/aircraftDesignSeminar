"""Print breakdown and plots for mission energy and payload-range performance."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import matplotlib.pyplot as plt
import numpy as np

from data import SiValue

if TYPE_CHECKING:
    from aircraft import BatteryAircraft
    from fuel_fractions import MissionEnergyCalculator
    from reference_aircraft import ReferenceAircraft


def print_mission_energy_breakdown(calc: MissionEnergyCalculator) -> None:
    """Prints a comprehensive breakdown table comparing reference kerosene and electric battery sizing."""

    def _row(
        name: str,
        fuel: SiValue,
        energy: SiValue,
        ld_bat: float | None = None,
        ld_kero: float | None = None,
    ) -> None:
        r_kero = calc.ref_mission.equivalent_range(fuel, ld_kero)
        r_bat = calc.equivalent_range(energy, ld_bat)
        print(
            f"{name:<32} | {fuel.to('kg'):6.1f} | {r_kero.to('nm'):6.1f} | {energy.to('kWh'):10.1f} | "
            f"{calc.battery_cell_mass(energy):7.1f} | {calc.battery_pack_mass(energy):7.1f} | {r_bat.to('nm'):6.1f}"
        )

    ref = calc.ref_mission.ref
    print("----- MISSION ENERGY & BATTERY MASS BREAKDOWN -----")
    print(
        f"Reference Turboprop Efficiency (eta_ref): {calc.ref_mission.propulsion_efficiency * 100:.2f} %"
    )
    print(
        f"Electric Aircraft: MTOM = {calc.mtom}, eta_el = {calc.design.propulsion.etaElectric * 100:.1f} %, "
        f"Range = {calc.range.to('nm'):.0f}, L/D = {calc.design.aerodynamics.liftToDragRatioCruise:.1f}\n"
    )
    print(
        f"{'Segment':<32} | {'Ref Fuel':>9} | {'R (Kero)':>9} | {'E_el [kWh]':>10} | {'m_Cell':>10} | {'m_Pack':>10} | {'R (Bat)':>9}"
    )
    print("-" * 105)

    _row(
        "1. Taxi-out & Take-off",
        ref.fuel.taxiOutAndTakeOff.si,
        calc.taxi_and_takeoff_energy(),
    )
    _row(
        f"2. Cruise ({calc.range.to('nm'):.0f})",
        ref.fuel.cruise.si,
        calc.cruise_energy(),
    )
    _row(
        "3. Climb & Descent (+10.3% Ref.)",
        SiValue(ref.fuel.climb.si + ref.fuel.descent.si, "kg"),
        calc.climb_and_descent_energy(),
    )
    _row(
        "4. Approach, Landing & Taxi-in",
        ref.fuel.approachLandingAndTaxiIn.si,
        calc.approach_and_landing_energy(),
    )
    print("-" * 105)
    _row("TRIP TOTAL (Phases 1-5)", ref.fuel.tripMass.si, calc.trip_energy())
    print("-" * 105)
    _row(
        "  - 5% Route Reserve",
        calc.ref_mission.route_reserve_fuel_mass(),
        calc.route_reserve_energy(),
    )
    _row(
        f"  - 30 min Loiter (L/D = {calc.design.aerodynamics.liftToDragRatioLoiter:.1f})",
        calc.ref_mission.loiter_fuel_mass(),
        calc.loiter_energy(),
        calc.design.aerodynamics.liftToDragRatioLoiter,
        ref.aerodynamics.liftToDragRatioLoiter,
    )
    _row(
        "  - 50 NM Diversion",
        calc.ref_mission.diversion_fuel_mass(),
        calc.diversion_energy(),
    )
    res_fuel = calc.ref_mission.reserve_fuel_mass()
    _row("6. Reserve Total (Ref: 186 kg)", res_fuel, calc.reserve_energy())
    print("=" * 105)
    _row(
        "MISSION TOTAL (Trip + Reserve)",
        SiValue(ref.fuel.tripMass.si + res_fuel.si, "kg"),
        calc.total_mission_energy(),
    )


def plot_mission_energy(
    aircraft: BatteryAircraft,
    ref_aircraft: ReferenceAircraft,
    variant: Literal["simple", "detailed"] = "simple",
) -> None:
    """Plots energy consumption across mission phases and reserves.

    Args:
        aircraft: BatteryAircraft model instance.
        ref_aircraft: Reference aircraft data.
        variant: 'simple' uses proportional fuel scaling (matching current MTOM sizing);
                 'detailed' uses analytical segment calculation via MissionEnergyCalculator.
    """
    if variant == "simple":
        range_fuel = (
            ref_aircraft.data.fuel.climb.si
            + ref_aircraft.data.fuel.cruise.si
            + ref_aircraft.data.fuel.descent.si
        )
        range_energy = aircraft.mission_energy.cruise_energy(
            aircraft.design.mission.range.si
        )
        energy_per_kg = range_energy / range_fuel

        phases = [
            (
                "Taxi-out & Take-off (24 kg fuel)",
                (ref_aircraft.data.fuel.taxiOutAndTakeOff.si * energy_per_kg) / 3.6e6,
                "#3498db",
                "Trip",
            ),
            (
                "Climb (36 kg fuel)",
                (ref_aircraft.data.fuel.climb.si * energy_per_kg) / 3.6e6,
                "#2980b9",
                "Trip",
            ),
            (
                "Cruise (78 kg fuel, 100 NM)",
                (ref_aircraft.data.fuel.cruise.si * energy_per_kg) / 3.6e6,
                "#1abc9c",
                "Trip",
            ),
            (
                "Descent (9 kg fuel)",
                (ref_aircraft.data.fuel.descent.si * energy_per_kg) / 3.6e6,
                "#16a085",
                "Trip",
            ),
            (
                "Approach & Landing (17 kg fuel)",
                (ref_aircraft.data.fuel.approachLandingAndTaxiIn.si * energy_per_kg)
                / 3.6e6,
                "#27ae60",
                "Trip",
            ),
            (
                "Mission Reserves (186 kg fuel)",
                (ref_aircraft.data.fuel.reserve.si * energy_per_kg) / 3.6e6,
                "#e67e22",
                "Reserve",
            ),
        ]
        title_suffix = "Simple Variant – Proportional Fuel Scaling"
    else:
        me = aircraft.mission_energy
        phases = [
            (
                "Taxi-out & Take-off",
                me.taxi_and_takeoff_energy() / 3.6e6,
                "#3498db",
                "Trip",
            ),
            (
                "Climb & Descent",
                me.climb_and_descent_energy() / 3.6e6,
                "#2980b9",
                "Trip",
            ),
            (
                "Horizontal Cruise (100 NM)",
                me.cruise_energy() / 3.6e6,
                "#1abc9c",
                "Trip",
            ),
            (
                "Approach & Landing",
                me.approach_and_landing_energy() / 3.6e6,
                "#16a085",
                "Trip",
            ),
            (
                "Route Reserve (5 %)",
                me.route_reserve_energy() / 3.6e6,
                "#f39c12",
                "Reserve",
            ),
            ("Loiter Hold (30 min)", me.loiter_energy() / 3.6e6, "#e67e22", "Reserve"),
            ("Diversion (50 NM)", me.diversion_energy() / 3.6e6, "#d35400", "Reserve"),
        ]
        title_suffix = "Detailed Variant – MissionEnergyCalculator"

    labels = [p[0] for p in phases]
    values_kwh = [p[1] for p in phases]
    colors = [p[2] for p in phases]
    total_energy_kwh = sum(values_kwh)

    trip_kwh = sum(v for p, v in zip(phases, values_kwh) if p[3] == "Trip")
    reserve_kwh = sum(v for p, v in zip(phases, values_kwh) if p[3] == "Reserve")

    _fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1.3, 1]}
    )

    y_pos = np.arange(len(labels))
    bars = ax1.barh(y_pos, values_kwh, color=colors, edgecolor="black", lw=0.6)

    for bar, val in zip(bars, values_kwh):
        pct = val / total_energy_kwh * 100
        ax1.text(
            bar.get_width() + 4,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f} kWh ({pct:.1f} %)",
            va="center",
            fontsize=8.5,
            fontweight="bold",
        )

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=10)
    ax1.invert_yaxis()
    ax1.set_xlabel("Electric Energy [kWh]", fontsize=11)
    ax1.set_title(
        f"Energy Distribution by Flight Phase\n({title_suffix})",
        fontsize=11,
        fontweight="bold",
    )
    ax1.set_xlim(0, max(values_kwh) * 1.32)
    ax1.grid(axis="x", linestyle=":", alpha=0.6)

    ax2.pie(
        [trip_kwh, reserve_kwh],
        labels=[
            f"Nominal Flight\n({trip_kwh:.1f} kWh)",
            f"Mission Reserves\n({reserve_kwh:.1f} kWh)",
        ],
        autopct="%1.1f %%",
        startangle=140,
        colors=["#2980b9", "#e67e22"],
        wedgeprops=dict(width=0.4, edgecolor="white", lw=2),
        textprops=dict(fontsize=10, fontweight="bold"),
    )
    ax2.set_title(
        f"Total Mission Energy: {total_energy_kwh:.1f} kWh\n(Battery Mass: {aircraft.m_battery:.0f})",
        fontsize=11,
        fontweight="bold",
    )

    plt.tight_layout()
    plt.show()


def plot_payload_range(aircraft: BatteryAircraft) -> None:
    """Plots Payload-Range diagram for the electric aircraft."""
    pax_max = 19
    pax_weight = 90.0  # kg
    nominal_payload = aircraft.m_payload
    mtom = aircraft.mtom
    nominal_range_nm = aircraft.range.to("NM")

    pax_range = np.arange(0, 20)
    payload_vals = pax_range * pax_weight
    masses = mtom - (nominal_payload - payload_vals)

    ranges_fixed_nm = nominal_range_nm * (mtom / masses)

    _fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(
        ranges_fixed_nm,
        payload_vals,
        color="#2980b9",
        lw=2.5,
        marker="o",
        label="Fixed Battery (Reduced weight with fewer passengers)",
    )
    ax1.plot(
        nominal_range_nm,
        nominal_payload,
        marker="*",
        markersize=15,
        color="#d35400",
        label=f"Design Point ({nominal_range_nm:.1f}, {pax_max} PAX)",
    )

    ax1.annotate(
        f"Design Point:\n{pax_max} PAX ({nominal_payload:.0f})\n{nominal_range_nm:.1f} (incl. reserves)",
        xy=(nominal_range_nm, nominal_payload),
        xytext=(nominal_range_nm - 40, nominal_payload - 450),
        arrowprops=dict(facecolor="#d35400", shrink=0.08, width=1.5, headwidth=7),
        fontsize=9,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fadbd8", alpha=0.8),
    )

    ferry_range = ranges_fixed_nm[0]
    ax1.annotate(
        f"Ferry Range (0 PAX):\n{ferry_range:.1f} NM",
        xy=(ferry_range, 0),
        xytext=(ferry_range - 45, 250),
        arrowprops=dict(facecolor="#2980b9", shrink=0.08, width=1.5, headwidth=7),
        fontsize=9,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="#d4e6f1", alpha=0.8),
    )

    ax1.set_xlabel("Range [NM]", fontsize=11)
    ax1.set_ylabel("Payload [kg]", fontsize=11)
    ax1.set_title("Payload-Range Diagram", fontsize=13, fontweight="bold")
    ax1.set_ylim(-50, nominal_payload * 1.15)
    ax1.set_xlim(min(ranges_fixed_nm) * 0.9, max(ranges_fixed_nm) * 1.08)
    ax1.grid(True, linestyle=":", alpha=0.6)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Number of Passengers [PAX]", fontsize=11)
    ax2.set_ylim(-50 / pax_weight, (nominal_payload * 1.15) / pax_weight)
    ax2.set_yticks(np.arange(0, 21, 2))

    ax1.legend(loc="upper right", fontsize=9.5, framealpha=0.95)
    plt.tight_layout()
    plt.show()
