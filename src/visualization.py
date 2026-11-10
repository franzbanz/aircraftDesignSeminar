"""Interactive visualizations for aircraft sizing, mass breakdown, energy, and mission performance."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import matplotlib.pyplot as plt
import numpy as np

from data import SiValue
from sizing_diagram import SizingDiagram

if TYPE_CHECKING:
    from aircraft import BatteryAircraft
    from reference_aircraft import ReferenceAircraft


def plot_sizing_diagram() -> None:
    """Plots the sizing diagram (matching chart) with design point and feasible region.

    Reuses the calculation from sizing_diagram.py to avoid code duplication.
    """
    SizingDiagram().plot()


def plot_mass_breakdown(
    aircraft: BatteryAircraft,
    ref_aircraft: ReferenceAircraft,
) -> None:
    """Plots stacked mass comparison between Dornier 228 reference and the electric aircraft."""
    _fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(13, 6.5), gridspec_kw={"width_ratios": [1.2, 1]}
    )

    ref_struct = SiValue(
        ref_aircraft.data.mass.wing.si
        + ref_aircraft.data.mass.fuselage.si
        + ref_aircraft.data.mass.landingGear.si
        + ref_aircraft.data.mass.empennage.si
        + ref_aircraft.data.mass.pylons.si,
        "kg",
    )
    el_struct = aircraft.m_structure

    ref_prop = ref_aircraft.data.mass.engine.si
    el_prop = aircraft.m_engine

    ref_sys = SiValue(
        ref_aircraft.data.mass.systems.si + ref_aircraft.data.mass.furnishings.si,
        "kg",
    )
    el_sys = SiValue(aircraft.m_systems + aircraft.m_furnishings, "kg")

    ref_ops = ref_aircraft.data.mass.operatorItems.si
    el_ops = aircraft.m_operator_items

    ref_pay = 19 * 90.0  # 1710 kg
    el_pay = aircraft.m_payload

    ref_energy = ref_aircraft.data.fuel.total.si
    el_energy = aircraft.m_battery

    ref_total = SiValue(
        ref_struct + ref_prop + ref_sys + ref_ops + ref_pay + ref_energy,
        "kg",
    )
    el_total = aircraft.mtom

    categories = [
        "Structure",
        "Propulsion",
        "Systems & Furnishings",
        "Operator Items",
        "Payload (19 PAX)",
        "Energy Storage (Fuel / Battery)",
    ]

    colors = ["#4a7bb0", "#e67e22", "#27ae60", "#95a5a6", "#9b59b6", "#e74c3c"]
    ref_values = [ref_struct, ref_prop, ref_sys, ref_ops, ref_pay, ref_energy]
    el_values = [el_struct, el_prop, el_sys, el_ops, el_pay, el_energy]

    x = np.array([0, 1])
    width = 0.55

    # Stacked bars
    bottom_ref = 0.0
    bottom_el = 0.0
    for cat, c_color, v_ref, v_el in zip(categories, colors, ref_values, el_values):
        ax1.bar(
            x[0],
            v_ref,
            width,
            bottom=bottom_ref,
            color=c_color,
            label=cat,
            edgecolor="white",
            lw=1,
        )
        if v_ref > 200:
            pct_ref = v_ref / ref_total * 100
            ax1.text(
                x[0],
                bottom_ref + v_ref / 2,
                f"{v_ref:.0f}\n({pct_ref:.1f}%)",
                ha="center",
                va="center",
                color="white",
                fontsize=8.5,
                fontweight="bold",
            )
        bottom_ref += v_ref

        ax1.bar(
            x[1], v_el, width, bottom=bottom_el, color=c_color, edgecolor="white", lw=1
        )
        if v_el > 200:
            pct_el = v_el / el_total * 100
            ax1.text(
                x[1],
                bottom_el + v_el / 2,
                f"{v_el:.0f}\n({pct_el:.1f}%)",
                ha="center",
                va="center",
                color="white",
                fontsize=8.5,
                fontweight="bold",
            )
        bottom_el += v_el

    ax1.set_xticks(x)
    ax1.set_xticklabels(
        [
            f"Dornier 228 (Ref)\nMTOM: {ref_total:.0f}",
            f"Electric Aircraft\nMTOM: {el_total:.0f}",
        ],
        fontsize=11,
        fontweight="bold",
    )
    ax1.set_ylabel("Mass [kg]", fontsize=11)
    ax1.set_title("Mass Breakdown Comparison", fontsize=12, fontweight="bold")
    ax1.set_ylim(0, max(ref_total, el_total) * 1.08)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=8.5, framealpha=0.95)

    # Detailed structural breakdown (Subplot 2)
    struct_parts = ["Wing", "Fuselage", "Landing Gear", "Empennage", "Pylons"]
    ref_parts = [
        ref_aircraft.data.mass.wing.si,
        ref_aircraft.data.mass.fuselage.si,
        ref_aircraft.data.mass.landingGear.si,
        ref_aircraft.data.mass.empennage.si,
        ref_aircraft.data.mass.pylons.si,
    ]
    el_parts = [
        aircraft.m_wing,
        aircraft.m_fuselage,
        aircraft.m_landing_gear,
        aircraft.m_empennage,
        aircraft.m_pylons,
    ]

    y_pos = np.arange(len(struct_parts))
    bar_h = 0.35

    ax2.barh(
        y_pos + bar_h / 2,
        ref_parts,
        bar_h,
        label="Do 228 (Ref)",
        color="#7fb3d5",
        edgecolor="black",
        lw=0.5,
    )
    ax2.barh(
        y_pos - bar_h / 2,
        el_parts,
        bar_h,
        label="Electric Aircraft",
        color="#2980b9",
        edgecolor="black",
        lw=0.5,
    )

    for i, (vr, ve) in enumerate(zip(ref_parts, el_parts)):
        ax2.text(vr + 15, i + bar_h / 2, f"{vr:.0f}", va="center", fontsize=8)
        ax2.text(
            ve + 15,
            i - bar_h / 2,
            f"{ve:.0f}",
            va="center",
            fontsize=8,
            fontweight="bold",
        )

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(struct_parts, fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel("Mass [kg]", fontsize=11)
    ax2.set_title(
        "Structural Mass Details (Class II Breakdown)", fontsize=12, fontweight="bold"
    )
    ax2.set_xlim(0, max(max(ref_parts), max(el_parts)) * 1.25)
    ax2.grid(axis="x", linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", fontsize=9)

    plt.tight_layout()
    plt.show()


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
        # Simpler approach matching aircraft.calc_required_battery_mass():
        range_fuel = (
            ref_aircraft.data.fuel.climb.si
            + ref_aircraft.data.fuel.cruise.si
            + ref_aircraft.data.fuel.descent.si
        )
        range_energy = aircraft.mission_energy.cruise_energy(
            aircraft.design.mission.range.si
        )
        energy_per_kg = range_energy / range_fuel

        # Flight phases proportional to reference aircraft fuel breakdown
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
        # Detailed segment calculation via MissionEnergyCalculator:
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

    # Horizontal bar chart
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

    # Donut chart for Trip vs Reserve
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
    nominal_payload = pax_max * pax_weight  # 1710 kg
    mtom = aircraft.mtom
    nominal_range_nm = aircraft.range.to("NM")

    pax_range = np.arange(0, 20)
    payload_vals = pax_range * pax_weight
    masses = mtom - (nominal_payload - payload_vals)

    # Range with fixed battery [NM] (scales inversely with take-off mass)
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


def plot_aircraft_geometry(
    aircraft: BatteryAircraft,
    ref_aircraft: ReferenceAircraft,
) -> None:
    """Plots 2D top-down geometric comparison between Dornier 228 and the electric aircraft."""
    _fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(14, 6.5), gridspec_kw={"width_ratios": [1.4, 1]}
    )

    # ------------------ Subplot 1: Top-down Planform Schematic ------------------
    # Fuselage (common 19-pax fuselage geometry)
    l_f = aircraft.fuselage_length
    w_f = aircraft.fuselage_width

    # Simplified fuselage contour
    fuselage_x = [0, 1.5, l_f - 3.0, l_f, l_f - 3.0, 1.5, 0]
    fuselage_y = [0, w_f / 2, w_f / 2, 0, -w_f / 2, -w_f / 2, 0]
    ax1.plot(fuselage_y, fuselage_x, color="dimgray", lw=2, label="Fuselage (19 PAX)")
    ax1.fill(fuselage_y, fuselage_x, color="lightgray", alpha=0.4)

    # Wing position (quarter-chord around x = 6.0 m)
    x_qc = 6.0

    # Reference Aircraft (Do 228) Wing
    b_ref = ref_aircraft.data.dimensions.wingspan.si
    c_ref = ref_aircraft.mean_aerodynamic_chord.si
    x_w_ref_le = x_qc - 0.25 * c_ref
    x_w_ref_te = x_w_ref_le + c_ref
    ax1.fill(
        [-b_ref / 2, b_ref / 2, b_ref / 2, -b_ref / 2],
        [x_w_ref_le, x_w_ref_le, x_w_ref_te, x_w_ref_te],
        color="#3498db",
        alpha=0.35,
        edgecolor="#2980b9",
        lw=2,
        ls="--",
        label=f"Do 228 Wing (b = {b_ref:.1f}, S = {ref_aircraft.data.dimensions.wingArea:.1f})",
    )

    # Electric Aircraft Wing
    b_el = aircraft.wingspan
    c_el = aircraft.mean_aerodynamic_chord
    x_w_el_le = x_qc - 0.25 * c_el
    x_w_el_te = x_w_el_le + c_el
    ax1.fill(
        [-b_el / 2, b_el / 2, b_el / 2, -b_el / 2],
        [x_w_el_le, x_w_el_le, x_w_el_te, x_w_el_te],
        color="#27ae60",
        alpha=0.35,
        edgecolor="#1e8449",
        lw=2.5,
        label=f"Electric Wing (b = {b_el:.1f}, S = {aircraft.wing_area:.1f})",
    )

    # CS-23 Maximum Wingspan constraint line (24 m)
    b_max = aircraft.design.aerodynamics.maxWingSpan.si
    ax1.axvline(
        -b_max / 2, color="red", ls=":", lw=1.5, label=f"CS-23 Max Span ({b_max:.0f})"
    )
    ax1.axvline(b_max / 2, color="red", ls=":", lw=1.5)

    # Horizontal Tailplane (quarter-chord around x = 15.0 m)
    x_qc_ht = 15.0
    s_ht_ref = ref_aircraft.data.dimensions.horizontalTailArea.si
    b_ht_ref = (s_ht_ref * 4.0) ** 0.5  # assuming AR ~ 4.0
    c_ht_ref = s_ht_ref / b_ht_ref
    ax1.fill(
        [-b_ht_ref / 2, b_ht_ref / 2, b_ht_ref / 2, -b_ht_ref / 2],
        [
            x_qc_ht - 0.25 * c_ht_ref,
            x_qc_ht - 0.25 * c_ht_ref,
            x_qc_ht + 0.75 * c_ht_ref,
            x_qc_ht + 0.75 * c_ht_ref,
        ],
        color="#3498db",
        alpha=0.35,
        edgecolor="#2980b9",
        lw=1.5,
        ls="--",
    )

    s_ht_el = aircraft.horizontal_tail_area
    b_ht_el = (s_ht_el * 4.0) ** 0.5
    c_ht_el = s_ht_el / b_ht_el
    ax1.fill(
        [-b_ht_el / 2, b_ht_el / 2, b_ht_el / 2, -b_ht_el / 2],
        [
            x_qc_ht - 0.25 * c_ht_el,
            x_qc_ht - 0.25 * c_ht_el,
            x_qc_ht + 0.75 * c_ht_el,
            x_qc_ht + 0.75 * c_ht_el,
        ],
        color="#27ae60",
        alpha=0.35,
        edgecolor="#1e8449",
        lw=2,
        label=f"Horizontal Tail (Do: {s_ht_ref:.1f} vs. El: {s_ht_el:.1f})",
    )

    ax1.set_aspect("equal", "datalim")
    ax1.invert_yaxis()
    ax1.set_xlabel("Lateral Span Position [m]", fontsize=11)
    ax1.set_ylabel("Fuselage Station (Nose to Tail) [m]", fontsize=11)
    ax1.set_title(
        "Top-Down 2D Planform Schematic Comparison", fontsize=12, fontweight="bold"
    )
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=8.5, framealpha=0.95)

    # ------------------ Subplot 2: Numerical Comparison ------------------
    labels = [
        "Wing Area [m²]",
        "Wingspan [m]",
        "Aspect Ratio [-]",
        "Mean Chord (MAC) [m]",
        "HTP Area [m²]",
        "VTP Area [m²]",
    ]
    ref_vals = [
        ref_aircraft.data.dimensions.wingArea.si,
        ref_aircraft.data.dimensions.wingspan.si,
        ref_aircraft.aspect_ratio,
        ref_aircraft.mean_aerodynamic_chord.si,
        ref_aircraft.data.dimensions.horizontalTailArea.si,
        ref_aircraft.data.dimensions.verticalTailArea.si,
    ]
    el_vals = [
        aircraft.wing_area,
        aircraft.wingspan,
        aircraft.aspect_ratio,
        aircraft.mean_aerodynamic_chord,
        aircraft.horizontal_tail_area,
        aircraft.vertical_tail_area,
    ]

    y = np.arange(len(labels))
    bar_h = 0.35

    ax2.barh(
        y + bar_h / 2,
        ref_vals,
        bar_h,
        label="Do 228 (Ref)",
        color="#7fb3d5",
        edgecolor="black",
        lw=0.5,
    )
    ax2.barh(
        y - bar_h / 2,
        el_vals,
        bar_h,
        label="Electric Aircraft",
        color="#27ae60",
        edgecolor="black",
        lw=0.5,
    )

    for i, (vr, ve) in enumerate(zip(ref_vals, el_vals)):
        pct_delta = ((ve - vr) / vr) * 100
        ax2.text(
            vr + max(el_vals) * 0.02,
            i + bar_h / 2,
            f"{vr:.2f}",
            va="center",
            fontsize=8.5,
        )
        ax2.text(
            ve + max(el_vals) * 0.02,
            i - bar_h / 2,
            f"{ve:.2f} ({'+' if pct_delta >= 0 else ''}{pct_delta:.0f}%)",
            va="center",
            fontsize=8.5,
            fontweight="bold",
        )

    ax2.set_yticks(y)
    ax2.set_yticklabels(labels, fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel("Dimension Value", fontsize=11)
    ax2.set_title("Geometric Dimensions Comparison", fontsize=12, fontweight="bold")
    ax2.set_xlim(0, max(el_vals) * 1.35)
    ax2.grid(axis="x", linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", fontsize=9.5)

    plt.tight_layout()
    plt.show()


def interactive_plot_menu(
    aircraft: BatteryAircraft, ref_aircraft: ReferenceAircraft
) -> None:
    """CLI selection menu allowing the user to select which visualization to display."""
    menu_text = """
======================================================================
               AIRCRAFT DESIGN - PLOT MENU
======================================================================
  [1] Sizing Diagram (Matching Chart & Design Point)
  [2] Mass Breakdown (Comparison with Do 228)
  [3] Mission Energy Breakdown (Simple Variant - matches active MTOM)
  [3d] Mission Energy Breakdown (Detailed Variant - analytical segments)
  [4] Payload-Range Diagram
  [5] Aircraft Dimensions & 2D Geometry Comparison
  [A] Show All Plots
  [Q] Exit Menu
======================================================================
"""
    while True:
        print(menu_text)
        try:
            choice = input("Select a diagram (number/letter): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting plot menu.")
            break

        if choice in ("q", "quit", "exit", "0"):
            print("Plot menu exited.")
            break
        elif choice in ("1", "s", "sizing"):
            print("Opening Sizing Diagram...")
            plot_sizing_diagram()
        elif choice in ("2", "m", "mass"):
            print("Opening Mass Breakdown Comparison...")
            plot_mass_breakdown(aircraft, ref_aircraft)
        elif choice in ("3", "e", "energy", "simple"):
            print("Opening Mission Energy Breakdown (Simple Variant)...")
            plot_mission_energy(aircraft, ref_aircraft, variant="simple")
        elif choice in ("3d", "detailed"):
            print("Opening Mission Energy Breakdown (Detailed Variant)...")
            plot_mission_energy(aircraft, ref_aircraft, variant="detailed")
        elif choice in ("4", "p", "payload", "range"):
            print("Opening Payload-Range Diagram...")
            plot_payload_range(aircraft)
        elif choice in ("5", "g", "geom", "geometry", "dimensions"):
            print("Opening Aircraft Dimensions & Geometry Comparison...")
            plot_aircraft_geometry(aircraft, ref_aircraft)
        elif choice in ("a", "all"):
            print("Opening all diagrams sequentially...")
            plot_sizing_diagram()
            plot_mass_breakdown(aircraft, ref_aircraft)
            plot_mission_energy(aircraft, ref_aircraft, variant="simple")
            plot_payload_range(aircraft)
            plot_aircraft_geometry(aircraft, ref_aircraft)
        else:
            print(
                f"Unknown option '{choice}'. Please choose 1, 2, 3, 3d, 4, 5, A or Q."
            )


if __name__ == "__main__":
    from aircraft import BatteryAircraft
    from data import load_constraints, load_design_parameters
    from reference_aircraft import load_reference_aircraft

    constraints = load_constraints()
    ref_aircraft = load_reference_aircraft()
    design_params = load_design_parameters()

    aircraft = BatteryAircraft(constraints, design_params, ref_aircraft)
    aircraft.converge_mtom()
    interactive_plot_menu(aircraft, ref_aircraft)
