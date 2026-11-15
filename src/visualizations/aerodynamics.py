"""Aerodynamics visualization: zero-lift drag buildup and cruise drag polar."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

if TYPE_CHECKING:
    from aircraft import BatteryAircraft
    from reference_aircraft import ReferenceAircraft


def plot_aerodynamics(
    aircraft: BatteryAircraft,
    ref_aircraft: ReferenceAircraft,
) -> None:
    """Plots component zero-lift drag buildup, cruise drag polar, and L/D vs C_L."""
    fig, (ax1, ax2, ax3) = plt.subplots(
        1, 3, figsize=(18, 6.0), gridspec_kw={"width_ratios": [0.95, 1.15, 1.15]}
    )

    categories = [
        "Wing",
        "Fuselage",
        "Empennage (HTP + VTP)",
        "Misc (Nacelles, Gear, Interf.)",
    ]
    colors = ["#4a7bb0", "#e67e22", "#27ae60", "#95a5a6"]

    ref_areas = [
        ref_aircraft.wing_drag_area,
        ref_aircraft.fuselage_drag_area,
        ref_aircraft.empennage_drag_area,
        ref_aircraft.misc_drag_area,
    ]
    el_areas = [
        aircraft.wing.drag_area,
        aircraft.fuselage.drag_area,
        aircraft.empennage.drag_area,
        ref_aircraft.misc_drag_area,
    ]

    ref_total_f = sum(ref_areas)
    el_total_f = sum(el_areas)

    x = np.array([0, 1])
    width = 0.52

    bottom_ref = 0.0
    bottom_el = 0.0
    for cat, color, v_ref, v_el in zip(categories, colors, ref_areas, el_areas):
        ax1.bar(
            x[0],
            v_ref,
            width,
            bottom=bottom_ref,
            color=color,
            label=cat,
            edgecolor="white",
            lw=1,
        )
        ax1.bar(
            x[1],
            v_el,
            width,
            bottom=bottom_el,
            color=color,
            edgecolor="white",
            lw=1,
        )

        if v_ref / ref_total_f > 0.07:
            ax1.text(
                x[0],
                bottom_ref + v_ref / 2,
                f"{v_ref:.3f} m²\n({v_ref / ref_total_f * 100:.1f}%)",
                ha="center",
                va="center",
                color="white",
                fontsize=8.5,
                fontweight="bold",
            )
        if v_el / el_total_f > 0.07:
            ax1.text(
                x[1],
                bottom_el + v_el / 2,
                f"{v_el:.3f} m²\n({v_el / el_total_f * 100:.1f}%)",
                ha="center",
                va="center",
                color="white",
                fontsize=8.5,
                fontweight="bold",
            )
        bottom_ref += v_ref
        bottom_el += v_el

    ax1.text(
        x[0],
        ref_total_f + 0.025,
        f"f = {ref_total_f:.3f} m²\nc_W0 = {ref_aircraft.zero_lift_drag_coefficient:.4f}",
        ha="center",
        va="bottom",
        fontsize=9.5,
        fontweight="bold",
    )
    ax1.text(
        x[1],
        el_total_f + 0.025,
        f"f = {el_total_f:.3f} m²\nc_W0 = {aircraft.aerodynamics.zero_lift_drag_coefficient:.4f}",
        ha="center",
        va="bottom",
        fontsize=9.5,
        fontweight="bold",
    )

    ax1.set_xticks(x)
    ax1.set_xticklabels(
        [
            f"Dornier 228\n(S_W = {ref_aircraft.data.dimensions.wingArea:.1f})",
            f"Electric Aircraft\n(S_W = {aircraft.wing.area:.1f})",
        ],
        fontsize=10,
        fontweight="bold",
    )
    ax1.set_ylabel("Parasite Drag Area f = c_D0 · S [m²]", fontsize=10.5)
    ax1.set_title("Zero-Lift Drag Buildup", fontsize=12, fontweight="bold")
    ax1.set_ylim(0, max(ref_total_f, el_total_f) * 1.22)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)
    ax1.legend(loc="upper left", fontsize=8.5, framealpha=0.9)

    cl_grid = np.linspace(0.0, 1.35, 200)

    ref_cw0 = ref_aircraft.zero_lift_drag_coefficient
    ref_k = 1.0 / (
        math.pi * ref_aircraft.aspect_ratio * ref_aircraft.data.assumptions.oswaldFactor
    )
    ref_cd_grid = ref_cw0 + ref_k * (cl_grid**2)

    el_cw0 = aircraft.aerodynamics.zero_lift_drag_coefficient
    el_k = 1.0 / (
        math.pi * aircraft.wing.aspect_ratio * aircraft.design.aerodynamics.oswaldFactor
    )
    el_cd_grid = el_cw0 + el_k * (cl_grid**2)

    ax2.plot(
        ref_cd_grid,
        cl_grid,
        linestyle="--",
        color="#7f8c8d",
        linewidth=2.0,
        label=f"Do 228 Polar (AR={ref_aircraft.aspect_ratio:.2f}, e={ref_aircraft.data.assumptions.oswaldFactor:.2f})",
    )
    ax2.plot(
        el_cd_grid,
        cl_grid,
        linestyle="-",
        color="#2980b9",
        linewidth=2.4,
        label=f"Electric Polar (AR={aircraft.wing.aspect_ratio:.2f}, e={aircraft.design.aerodynamics.oswaldFactor:.2f})",
    )

    ref_cl_cr = ref_aircraft.cruise_lift_coefficient
    ref_cd_cr = ref_aircraft.drag_coefficient_from_polar(ref_cl_cr)
    ref_ld_cr = ref_aircraft.lift_to_drag_from_polar(ref_cl_cr)

    el_cl_cr = aircraft.aerodynamics.cruise_lift_coefficient
    el_cd_cr = aircraft.aerodynamics.cruise_drag_coefficient
    el_ld_cr = aircraft.aerodynamics.lift_to_drag_cruise

    ax2.scatter(
        [ref_cd_cr],
        [ref_cl_cr],
        color="#7f8c8d",
        s=80,
        zorder=5,
        edgecolors="black",
    )
    ax2.annotate(
        f"Do 228 Cruise\nC_L={ref_cl_cr:.3f}, L/D={ref_ld_cr:.2f}",
        xy=(ref_cd_cr, ref_cl_cr),
        xytext=(ref_cd_cr + 0.009, ref_cl_cr - 0.14),
        arrowprops={"arrowstyle": "->", "color": "#7f8c8d"},
        fontsize=9,
        color="#555555",
        fontweight="bold",
    )

    ax2.scatter(
        [el_cd_cr],
        [el_cl_cr],
        color="#e74c3c",
        s=90,
        zorder=6,
        edgecolors="black",
    )
    ax2.annotate(
        f"Electric Cruise\nC_L={el_cl_cr:.3f}, L/D={el_ld_cr:.2f}",
        xy=(el_cd_cr, el_cl_cr),
        xytext=(el_cd_cr + 0.010, el_cl_cr + 0.06),
        arrowprops={"arrowstyle": "->", "color": "#e74c3c"},
        fontsize=9,
        color="#c0392b",
        fontweight="bold",
    )

    el_cl_opt = math.sqrt(el_cw0 / el_k)
    el_cd_opt = 2.0 * el_cw0
    el_ld_max = el_cl_opt / el_cd_opt
    ax2.scatter(
        [el_cd_opt],
        [el_cl_opt],
        marker="^",
        color="#27ae60",
        s=80,
        zorder=5,
        edgecolors="black",
        label=f"Electric (L/D)_max = {el_ld_max:.2f} (C_L={el_cl_opt:.2f})",
    )

    ax2.set_xlabel("Total Drag Coefficient C_D [-]", fontsize=10.5)
    ax2.set_ylabel("Lift Coefficient C_L [-]", fontsize=10.5)
    ax2.set_title("Cruise Drag Polar (C_L vs. C_D)", fontsize=12, fontweight="bold")
    ax2.set_xlim(0.0, max(ref_cd_grid[-1], el_cd_grid[-1]) * 1.05)
    ax2.set_ylim(0.0, 1.4)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="lower right", fontsize=8.5, framealpha=0.9)

    ref_ld_grid = cl_grid / ref_cd_grid
    el_ld_grid = cl_grid / el_cd_grid

    ax3.plot(
        cl_grid,
        ref_ld_grid,
        linestyle="--",
        color="#7f8c8d",
        linewidth=2.0,
        label="Do 228 Polar",
    )
    ax3.plot(
        cl_grid,
        el_ld_grid,
        linestyle="-",
        color="#2980b9",
        linewidth=2.4,
        label="Electric Aircraft",
    )
    ax3.scatter(
        [ref_cl_cr],
        [ref_ld_cr],
        color="#7f8c8d",
        s=80,
        zorder=5,
        edgecolors="black",
    )
    ax3.annotate(
        f"Do 228 Cruise\n({ref_cl_cr:.2f}, {ref_ld_cr:.2f})",
        xy=(ref_cl_cr, ref_ld_cr),
        xytext=(ref_cl_cr + 0.08, ref_ld_cr - 2.3),
        arrowprops={"arrowstyle": "->", "color": "#7f8c8d"},
        fontsize=8.5,
        color="#555555",
        fontweight="bold",
    )
    ax3.scatter(
        [el_cl_cr],
        [el_ld_cr],
        color="#e74c3c",
        s=90,
        zorder=6,
        edgecolors="black",
    )
    ax3.annotate(
        f"Electric Cruise\n({el_cl_cr:.2f}, {el_ld_cr:.2f})",
        xy=(el_cl_cr, el_ld_cr),
        xytext=(max(0.05, el_cl_cr - 0.25), el_ld_cr - 3.0),
        arrowprops={"arrowstyle": "->", "color": "#e74c3c"},
        fontsize=8.5,
        color="#c0392b",
        fontweight="bold",
    )
    ax3.scatter(
        [el_cl_opt],
        [el_ld_max],
        marker="^",
        color="#27ae60",
        s=80,
        zorder=5,
        edgecolors="black",
        label=f"(L/D)_max = {el_ld_max:.2f} at C_L={el_cl_opt:.2f}",
    )

    ax3.set_xlabel("Lift Coefficient C_L [-]", fontsize=10.5)
    ax3.set_ylabel("Lift-to-Drag Ratio L/D [-]", fontsize=10.5)
    ax3.set_title("Glide Ratio (L/D vs. C_L)", fontsize=12, fontweight="bold")
    ax3.set_xlim(0.0, 1.35)
    ax3.set_ylim(0.0, max(float(np.max(ref_ld_grid)), float(np.max(el_ld_grid))) * 1.15)
    ax3.grid(True, linestyle="--", alpha=0.4)
    ax3.legend(loc="lower right", fontsize=8.5, framealpha=0.9)

    fig.suptitle(
        "Aerodynamic Drag Buildup & Cruise Polar Comparison",
        fontsize=13.5,
        fontweight="bold",
    )
    plt.tight_layout()
    plt.show()
