"""Print summary and matching chart plot for the sizing diagram."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np

from sizing_diagram import SizingDiagram, SizingMode


@dataclass(frozen=True)
class _PlotModeSpec:
    """Display configuration for a sizing diagram mode."""

    title_suffix: str
    y_label: str
    dp_fmt: str
    summary_label: str
    summary_unit: str
    y_min_top: float


_MODE_SPECS: dict[SizingMode, _PlotModeSpec] = {
    "thrust": _PlotModeSpec(
        title_suffix="Thrust-to-Weight Ratio",
        y_label=r"Thrust-to-Weight Ratio $T / (m_0 \cdot g)$ [–]",
        dp_fmt=".4f",
        summary_label="DESIGN THRUST LOADING:",
        summary_unit="",
        y_min_top=0.55,
    ),
    "power": _PlotModeSpec(
        title_suffix="Specific Take-Off Shaft Power",
        y_label=r"Specific Take-Off Shaft Power $P_0 / m_0$ [$\mathrm{W/kg}$]",
        dp_fmt=".1f",
        summary_label="DESIGN SPECIFIC POWER:",
        summary_unit=" W/kg",
        y_min_top=300.0,
    ),
}


def print_sizing_diagram(diagram: SizingDiagram) -> None:
    """Prints a structured summary of sizing diagram parameters and design point."""
    spec = _MODE_SPECS[diagram.mode]
    print("=" * 65)
    print("                      SIZING DIAGRAM SUMMARY")
    print("=" * 65)
    print(f"Sizing mode:                       {diagram.mode}")
    print(f"Aspect ratio:                      {diagram.aspect_ratio:.2f}")
    print(f"Cruise lift to drag ratio:         {diagram.l_d_cruise:.2f}")
    print(f"Cruise speed:                      {diagram.v_cruise:.2f}")
    print(f"Cruise air density:                {diagram.rho_cruise:.4f}")
    print(f"Cruise dynamic pressure:           {diagram.q_cruise:.2f}")
    if diagram.mode == "thrust":
        print(f"Thrust ratio at DP (F_TO / F_cr):  {diagram.design_thrust_ratio:.2f}")
    else:
        print(f"Power ratio (P_TO / P_MCT):        {diagram.power_ratio:.2f}")
        print(
            f"Propeller eff. (TO / Climb / Cr):  "
            f"{diagram.eta_prop_to:.2f} / {diagram.eta_prop_climb:.2f} / {diagram.eta_prop_cruise:.2f}"
        )
    print(f"Max. wing loading (stall):         {diagram.x_stall:.2f}")
    print(f"Max. wing loading (landing):       {diagram.x_landing:.2f}")
    print(f"Active constraint:                 {diagram.active_constraint}")
    print(f"Limiting wing loading:             {diagram.limiting_wing_loading}")
    print(f"DESIGN WING LOADING:               {diagram.design_point[0]:.2f} kg/m^2")
    dp_val = format(diagram.design_point[1], spec.dp_fmt)
    print(f"{spec.summary_label:<35}{dp_val}{spec.summary_unit}")
    print("=" * 65 + "\n")


def plot_sizing_diagram(
    diagram: SizingDiagram | None = None,
    mode: SizingMode = "thrust",
) -> None:
    """Plots the sizing diagram (matching chart) with design point and feasible region."""
    diag = diagram if diagram is not None else SizingDiagram(mode=mode)
    spec = _MODE_SPECS[diag.mode]
    dp = diag.design_point
    y_max = max(spec.y_min_top, float(dp[1] * 2.0))
    if diag.mode == "power":
        y_max = max(spec.y_min_top, float(np.ceil(dp[1] * 2.0 / 50.0) * 50.0))

    _fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.plot(
        diag.wing_loadings,
        diag.y_takeoff,
        color="#1f77b4",
        lw=2,
        label=rf"Take-off field length $s_{{\mathrm{{TOFL}}}} \leq {diag.constraints.performance.takeOffFieldLengthMax:.0f}$ (F.8)",
    )
    ax.plot(
        diag.wing_loadings,
        diag.y_climb,
        color="#ff7f0e",
        lw=2,
        label=rf"Climb gradient OEI $\gamma_{{\mathrm{{OEI}}}} \geq {diag.gamma_min_oei * 100:.1f}\,\%$ (H.2)",
    )
    ax.plot(
        diag.wing_loadings,
        diag.y_cruise,
        color="#2ca02c",
        lw=2,
        label=rf"Cruise speed $v_{{\mathrm{{cruise}}}} = {diag.design.mission.cruiseSpeedTAS:.1f}$ (I.1)",
    )
    ax.axvline(
        diag.x_stall,
        color="#d62728",
        lw=2,
        ls="--",
        label=f"Stall speed $v_S \\leq {diag.constraints.cs23.maxStallSpeed:.0f}$ ({diag.x_stall:.1f})",
    )
    ax.axvline(
        diag.x_landing,
        color="#9467bd",
        lw=2,
        ls="--",
        label=f"Landing field length $s_{{\\mathrm{{LDG}}}} \\leq {diag.constraints.performance.landingFieldLengthMax:.0f}$ ({diag.x_landing:.1f})",
    )

    x_lim = min(diag.x_stall, diag.x_landing)
    mask_feas = diag.wing_loadings <= x_lim
    y_envelope = np.maximum(np.maximum(diag.y_takeoff, diag.y_climb), diag.y_cruise)
    ax.fill_between(
        diag.wing_loadings[mask_feas],
        y_envelope[mask_feas],
        y_max * 1.1,
        color="green",
        alpha=0.12,
        label="Feasible Design Region",
    )

    dp_y_str = f"{format(dp[1], spec.dp_fmt)}{spec.summary_unit}"
    ax.plot(
        dp[0],
        dp[1],
        marker="*",
        markersize=14,
        color="black",
        label=f"Design Point ({dp[0]:.1f} kg/m², {dp_y_str})",
    )
    ax.annotate(
        f"DP: ({dp[0]:.1f} kg/m², {dp_y_str})",
        xy=dp,
        xytext=(max(diag.wing_loadings[0] + 10, dp[0] - 50), dp[1] + 0.14 * y_max),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=7),
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", fc="yellow", alpha=0.7),
    )

    ax.set_xlim(diag.wing_loadings[0], 350)
    ax.set_ylim(0, y_max)
    ax.set_xlabel(r"Wing Loading $m_0 / S$ [$\mathrm{kg/m}^2$]", fontsize=11)
    ax.set_ylabel(spec.y_label, fontsize=11)
    ax.set_title(
        f"Sizing Diagram ({spec.title_suffix}) – Electric Aircraft",
        fontsize=13,
        fontweight="bold",
    )
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    plt.tight_layout()
    plt.show()
