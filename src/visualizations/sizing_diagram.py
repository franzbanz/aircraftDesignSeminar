"""Print summary and matching chart plot for the sizing diagram."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from sizing_diagram import SizingDiagram


def print_sizing_diagram(diagram: SizingDiagram) -> None:
    """Prints a structured summary of sizing diagram parameters and design point."""
    print("=" * 65)
    print("                      SIZING DIAGRAM SUMMARY")
    print("=" * 65)
    print(f"Aspect ratio:                      {diagram.aspect_ratio:.2f}")
    print(f"Cruise lift to drag ratio:         {diagram.l_d_cruise:.2f}")
    print(f"Cruise speed:                      {diagram.v_cruise:.2f}")
    print(f"Cruise air density:                {diagram.rho_cruise:.4f}")
    print(f"Cruise dynamic pressure:           {diagram.q_cruise:.2f} Pa")
    print(f"Max. wing loading (stall):         {diagram.x_stall:.2f}")
    print(f"Max. wing loading (landing):       {diagram.x_landing:.2f}")
    print(f"Active thrust constraint:          {diagram.active_thrust_constraint}")
    print(f"Limiting wing loading:             {diagram.limiting_wing_loading}")
    print(f"DESIGN WING LOADING:               {diagram.design_point[0]:.2f} kg/m^2")
    print(f"DESIGN THRUST LOADING:             {diagram.design_point[1]:.4f}")
    print("=" * 65 + "\n")


def plot_sizing_diagram(diagram: SizingDiagram | None = None) -> None:
    """Plots the sizing diagram (matching chart) with design point and feasible region."""
    diag = diagram if diagram is not None else SizingDiagram()

    _fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.plot(
        diag.wing_loadings,
        diag.y_takeoff,
        color="#1f77b4",
        lw=2,
        label=r"Take-off field length $s_{\mathrm{TOFL}} \leq 800\,\mathrm{m}$ (F.8)",
    )
    ax.plot(
        diag.wing_loadings,
        diag.y_climb,
        color="#ff7f0e",
        lw=2,
        label=r"Climb gradient OEI $\gamma_{\mathrm{OEI}} \geq 1.5\,\%$ (H.2)",
    )
    ax.plot(
        diag.wing_loadings,
        diag.y_cruise,
        color="#2ca02c",
        lw=2,
        label=r"Cruise speed $v_{\mathrm{cruise}} = 200\,\mathrm{kts}$ (I.1)",
    )
    ax.axvline(
        diag.x_stall,
        color="#d62728",
        lw=2,
        ls="--",
        label=f"Stall speed $v_S \\leq 61\\,\\mathrm{{kts}}$ ({diag.x_stall:.1f})",
    )
    ax.axvline(
        diag.x_landing,
        color="#9467bd",
        lw=2,
        ls="--",
        label=f"Landing field length $s_{{\\mathrm{{LDG}}}} \\leq 800\\,\\mathrm{{m}}$ ({diag.x_landing:.1f})",
    )

    x_lim = min(diag.x_stall, diag.x_landing)
    mask_feas = diag.wing_loadings <= x_lim
    y_envelope = np.maximum(np.maximum(diag.y_takeoff, diag.y_climb), diag.y_cruise)
    ax.fill_between(
        diag.wing_loadings[mask_feas],
        y_envelope[mask_feas],
        0.6,
        color="green",
        alpha=0.12,
        label="Feasible Design Region",
    )

    dp = diag.design_point
    ax.plot(
        dp[0],
        dp[1],
        marker="*",
        markersize=14,
        color="black",
        label=f"Design Point ({dp[0]:.1f} kg/m², {dp[1]:.4f})",
    )
    ax.annotate(
        f"DP: ({dp[0]:.1f} kg/m², {dp[1]:.4f})",
        xy=dp,
        xytext=(dp[0] - 45, dp[1] + 0.05),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=7),
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", fc="yellow", alpha=0.7),
    )

    ax.set_xlim(diag.wing_loadings[0], 350)
    ax.set_ylim(0, 0.55)
    ax.set_xlabel(r"Wing Loading $m_0 / S$ [$\mathrm{kg/m}^2$]", fontsize=11)
    ax.set_ylabel(r"Thrust-to-Weight Ratio $T / (m_0 \cdot g)$ [–]", fontsize=11)
    ax.set_title(
        "Sizing Diagram (Matching Chart) – Electric Aircraft",
        fontsize=13,
        fontweight="bold",
    )
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    plt.tight_layout()
    plt.show()
