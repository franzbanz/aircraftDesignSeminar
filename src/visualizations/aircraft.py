"""Print summaries and plots for battery aircraft mass breakdown and geometry."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from data import SiValue

if TYPE_CHECKING:
    from aircraft import BatteryAircraft
    from reference_aircraft import ReferenceAircraft


def print_aircraft_summary(
    aircraft: BatteryAircraft, ref_aircraft: ReferenceAircraft
) -> None:
    """Prints mass breakdown, achievable range, and geometric dimensions of the electric aircraft."""
    m_structure_ref = SiValue(
        ref_aircraft.data.mass.wing.si
        + ref_aircraft.data.mass.fuselage.si
        + ref_aircraft.data.mass.landingGear.si
        + ref_aircraft.data.mass.empennage.si
        + ref_aircraft.data.mass.pylons.si,
        "kg",
    )

    print("----- MASS BREAKDOWN -----")
    print(f"Payload mass: {aircraft.m_payload}")
    print(
        f"Operator items mass: {aircraft.m_operator_items} (Ref: {ref_aircraft.data.mass.operatorItems})"
    )
    print(f"Structure mass: {aircraft.m_structure} (Ref: {m_structure_ref})")
    print(f"  - Wing: {aircraft.m_wing} (Ref: {ref_aircraft.data.mass.wing})")
    print(
        f"  - Fuselage: {aircraft.m_fuselage} (Ref: {ref_aircraft.data.mass.fuselage})"
    )
    print(
        f"  - Landing gear: {aircraft.m_landing_gear} (Ref: {ref_aircraft.data.mass.landingGear})"
    )
    print(
        f"  - Empennage: {aircraft.m_empennage} (Ref: {ref_aircraft.data.mass.empennage})"
    )
    print(f"  - Pylons: {aircraft.m_pylons} (Ref: {ref_aircraft.data.mass.pylons})")
    print(f"Engine mass: {aircraft.m_engine} (Ref: {ref_aircraft.data.mass.engine})")
    print(f"Systems mass: {aircraft.m_systems} (Ref: {ref_aircraft.data.mass.systems})")
    print(
        f"Furnishings mass: {aircraft.m_furnishings} (Ref: {ref_aircraft.data.mass.furnishings})"
    )
    print(f"Battery mass: {aircraft.m_battery}")
    print(
        f"Total Takeoff Mass (MTOM): {aircraft.mtom} (Ref: {ref_aircraft.data.mass.takeOffMassMax})\n"
    )

    print(f"Range: {aircraft.range.to('km')}")
    print(f"Range: {aircraft.range.to('NM')}")
    print(
        f"Cruise L/D (at {aircraft.design.mission.cruiseSpeedTAS}): "
        f"{aircraft.wing.lift_to_drag_cruise:.2f} "
        f"(C_L = {aircraft.wing.cruise_lift_coefficient:.3f}, "
        f"C_D = {aircraft.wing.cruise_drag_coefficient:.4f}, "
        f"c_W0 = {aircraft.wing.zero_lift_drag_coefficient:.4f}, "
        f"c_Wi = {aircraft.wing.induced_drag_coefficient:.4f})"
    )

    print("\n----- AIRCRAFT DIMENSIONS & GEOMETRY -----")
    print(
        f"Wing Area (S_W):             {aircraft.wing.area:.2f} (Ref: {ref_aircraft.data.dimensions.wingArea:.2f})"
    )
    print(
        f"Wingspan (b_W):              {aircraft.wing.span:.2f} (Ref: {ref_aircraft.data.dimensions.wingspan:.2f}, Max: {aircraft.design.aerodynamics.maxWingSpan:.2f})"
    )
    print(
        f"Aspect Ratio (AR):           {aircraft.wing.aspect_ratio:.2f} (Ref: {ref_aircraft.aspect_ratio:.2f})"
    )
    print(
        f"Mean Aerodynamic Chord:      {aircraft.wing.mean_aerodynamic_chord:.2f} (Ref: {ref_aircraft.mean_aerodynamic_chord:.2f})"
    )
    print(
        f"Wing Root Thickness (16%):   {aircraft.wing.root_thickness:.2f} (Ref: {ref_aircraft.wing_root_thickness:.2f})"
    )
    print(
        f"Fuselage (L x W x H):        {aircraft.fuselage_length:.2f} x {aircraft.fuselage_width:.2f} x {aircraft.fuselage_height:.2f}"
    )
    print(
        f"Horizontal Tail Area (S_HT): {aircraft.horizontal_tail_area:.2f} (Ref: {ref_aircraft.data.dimensions.horizontalTailArea:.2f})"
    )
    print(
        f"Vertical Tail Area (S_VT):   {aircraft.vertical_tail_area:.2f} (Ref: {ref_aircraft.data.dimensions.verticalTailArea:.2f})"
    )
    print(f"Design Wing Loading:         {aircraft.wing_loading_design:.2f} kg/m^2")
    print(f"Design Thrust Loading:       {aircraft.thrust_loading_design:.4f}")
    print(f"Total Take-off Thrust:       {aircraft.total_takeoff_thrust.to('kN'):.2f}")
    print(f"Total Installed Power:       {aircraft.total_takeoff_power.to('kW'):.1f}")


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

    ref_pay = ref_aircraft.data.mass.payload
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


def plot_aircraft_geometry(
    aircraft: BatteryAircraft,
    ref_aircraft: ReferenceAircraft,
) -> None:
    """Plots 2D top-down geometric comparison between Dornier 228 and the electric aircraft."""
    _fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(14, 6.5), gridspec_kw={"width_ratios": [1.4, 1]}
    )

    l_f = aircraft.fuselage_length
    w_f = aircraft.fuselage_width

    fuselage_x = [0, 1.5, l_f - 3.0, l_f, l_f - 3.0, 1.5, 0]
    fuselage_y = [0, w_f / 2, w_f / 2, 0, -w_f / 2, -w_f / 2, 0]
    ax1.plot(fuselage_y, fuselage_x, color="dimgray", lw=2, label="Fuselage (19 PAX)")
    ax1.fill(fuselage_y, fuselage_x, color="lightgray", alpha=0.4)

    x_qc = 6.0

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

    b_el = aircraft.wing.span
    c_el = aircraft.wing.mean_aerodynamic_chord
    x_w_el_le = x_qc - 0.25 * c_el
    x_w_el_te = x_w_el_le + c_el
    ax1.fill(
        [-b_el / 2, b_el / 2, b_el / 2, -b_el / 2],
        [x_w_el_le, x_w_el_le, x_w_el_te, x_w_el_te],
        color="#27ae60",
        alpha=0.35,
        edgecolor="#1e8449",
        lw=2.5,
        label=f"Electric Wing (b = {b_el:.1f}, S = {aircraft.wing.area:.1f})",
    )

    b_max = aircraft.design.aerodynamics.maxWingSpan.si
    ax1.axvline(
        -b_max / 2, color="red", ls=":", lw=1.5, label=f"CS-23 Max Span ({b_max:.0f})"
    )
    ax1.axvline(b_max / 2, color="red", ls=":", lw=1.5)

    x_qc_ht = 15.0
    s_ht_ref = ref_aircraft.data.dimensions.horizontalTailArea.si
    b_ht_ref = (s_ht_ref * 4.0) ** 0.5
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
        aircraft.wing.area,
        aircraft.wing.span,
        aircraft.wing.aspect_ratio,
        aircraft.wing.mean_aerodynamic_chord,
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
