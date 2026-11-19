"""Terminal reporting and loading diagram plot for Center of Gravity (CoG)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from cog import CenterOfGravity


def print_cog_summary(cog: CenterOfGravity, label: str = "Electric Aircraft") -> None:
    """Prints a detailed component CG table and loading excursion summary."""
    print("=" * 78)
    print(f"                  CENTER OF GRAVITY REPORT: {label}")
    print("=" * 78)
    print(
        f"Fuselage Length:   {cog.aircraft.fuselage.length:.2f} | LEMAC: {cog.aircraft.wing.x_lemac:.2f}"
    )
    print(
        f"Wing MAC (c_mu):   {cog.aircraft.wing.mean_aerodynamic_chord:.2f} | "
        f"Wing AC (25%): {cog.aircraft.wing.x_ac:.2f} | HTP AC: {cog.aircraft.empennage.x_htp_ac:.2f}"
    )
    print("-" * 78)
    print(
        f"{'Component':<28} | {'Mass [kg]':>10} | {'x_CG [m]':>9} | {'Moment [kg*m]':>14}"
    )
    print("-" * 78)
    for comp in cog.components:
        print(
            f"{comp.name:<28} | {float(comp.mass):10.1f} | "
            f"{float(comp.x_cg):9.2f} | {comp.moment:14.1f}"
        )
    print("-" * 78)

    states = [
        cog.oem_state,
        cog.zero_payload_state,
        cog.mtom_state,
        cog.extreme_state("forward"),
        cog.extreme_state("aft"),
    ]
    print(
        f"{'Loading State':<28} | {'Mass [kg]':>10} | {'x_CG [m]':>9} | {'% MAC':>14}"
    )
    print("-" * 78)
    for state in states:
        print(
            f"{state.name:<28} | {float(state.mass):10.1f} | "
            f"{float(state.x_cg):9.2f} | {state.mac_fraction * 100:13.1f}%"
        )
    print("-" * 78)
    print(
        f"CoG Travel (Fwd -> Aft):     {cog.cg_travel_mac * 100:.1f}% MAC "
        f"({cog.extreme_state('aft').x_cg - cog.extreme_state('forward').x_cg:.2f} m)"
    )
    print(
        f"Battery CG for 25.0% MAC:    {cog.required_battery_x_cg(0.25):.2f} "
        f"(Current: {cog.x_battery_cg:.2f})"
    )
    print("=" * 78 + "\n")


def plot_cog_excursion(cog: CenterOfGravity, label: str = "Electric Aircraft") -> None:
    """Plots the CoG loading excursion diagram (% MAC) and component CG positions."""
    fig, (ax_load, ax_comp) = plt.subplots(1, 2, figsize=(15, 6.5))
    fig.suptitle(
        f"Center of Gravity & Loading Diagram — {label}", fontsize=13, fontweight="bold"
    )

    fwd = cog.loading_curve("forward")
    aft = cog.loading_curve("aft")

    fwd_mac = [s.mac_fraction * 100.0 for s in fwd]
    fwd_m = [s.mass for s in fwd]
    aft_mac = [s.mac_fraction * 100.0 for s in aft]
    aft_m = [s.mass for s in aft]

    ax_load.axvspan(
        15.0,
        35.0,
        color="#2ecc71",
        alpha=0.12,
        label="Typical CoG Envelope (15–35% MAC)",
    )
    ax_load.axvline(15.0, color="#27ae60", linestyle="--", lw=1.0)
    ax_load.axvline(35.0, color="#27ae60", linestyle="--", lw=1.0)
    ax_load.axvline(
        25.0, color="#7f8c8d", linestyle=":", lw=1.2, label="25% MAC (Aero Center)"
    )

    (line_fwd,) = ax_load.plot(
        fwd_mac,
        fwd_m,
        "-o",
        color="#2980b9",
        markersize=5,
        lw=1.8,
        label="Front-to-Back Loading",
    )
    (line_aft,) = ax_load.plot(
        aft_mac,
        aft_m,
        "-s",
        color="#e67e22",
        markersize=5,
        lw=1.8,
        label="Back-to-Front Loading",
    )

    empty = cog.zero_payload_state
    mtom = cog.mtom_state
    most_fwd = cog.extreme_state("forward")
    most_aft = cog.extreme_state("aft")

    ax_load.scatter(
        [empty.mac_fraction * 100.0, mtom.mac_fraction * 100.0],
        [empty.mass, mtom.mass],
        color=["#8e44ad", "#c0392b"],
        s=90,
        zorder=5,
    )
    for label_text, state, offset, ha, color, use_arrow in (
        ("Empty + Bat", empty, (10, -10), "left", "#8e44ad", False),
        ("MTOM", mtom, (10, -10), "left", "#c0392b", False),
        (f"Most Fwd: {most_fwd.name}", most_fwd, (14, 6), "left", "#1f618d", True),
        (f"Most Aft: {most_aft.name}", most_aft, (-14, 6), "right", "#a04000", True),
    ):
        ax_load.annotate(
            f"{label_text}\n({state.mac_fraction * 100:.1f}% MAC)",
            (state.mac_fraction * 100.0, state.mass),
            textcoords="offset points",
            xytext=offset,
            ha=ha,
            fontsize=8.5 if not use_arrow else 8.0,
            fontweight="bold" if not use_arrow else "normal",
            color=color,
            arrowprops={"arrowstyle": "->", "color": color, "lw": 0.9}
            if use_arrow
            else None,
        )

    ax_load.set_xlabel("Center of Gravity Position [% MAC]", fontsize=10.5)
    ax_load.set_ylabel("Aircraft Mass [kg]", fontsize=10.5)
    ax_load.set_title("Loading Excursion Diagram", fontsize=11.5, fontweight="bold")
    ax_load.grid(True, linestyle=":", alpha=0.6)
    ax_load.legend(loc="lower right", fontsize=8.5)

    # Right panel: Component CG locations along fuselage length
    comps = cog.components
    y_pos = list(range(len(comps)))
    x_vals = [c.x_cg for c in comps]
    masses = [c.mass for c in comps]
    names = [f"{c.name} ({c.mass:.0f})" for c in comps]

    l_fus = cog.aircraft.fuselage.length
    lemac = cog.aircraft.wing.x_lemac
    temac = lemac + cog.aircraft.wing.mean_aerodynamic_chord

    ax_comp.axvspan(
        lemac, temac, color="#3498db", alpha=0.14, label="Wing MAC (LEMAC–TEMAC)"
    )
    ax_comp.axvline(
        mtom.x_cg,
        color="#c0392b",
        linestyle="--",
        lw=1.5,
        label=f"MTOM CoG ({mtom.x_cg:.2f})",
    )
    ax_comp.axvline(
        l_fus, color="#34495e", linestyle="-", lw=1.2, label=f"Tail End ({l_fus:.2f})"
    )

    sizes = [max(35.0, m * 0.14) for m in masses]
    comp_scatter = ax_comp.scatter(x_vals, y_pos, s=sizes, color="#2c3e50", zorder=4)
    for x_c, y_c in zip(x_vals, y_pos):
        ax_comp.plot([0, x_c], [y_c, y_c], color="#bdc3c7", lw=0.8, zorder=1)

    ax_comp.set_yticks(y_pos)
    ax_comp.set_yticklabels(names, fontsize=8.5)
    ax_comp.invert_yaxis()
    ax_comp.set_xlim(0, l_fus * 1.05)
    ax_comp.set_xlabel("Longitudinal Station from Nose x [m]", fontsize=10.5)
    ax_comp.set_title("Component Mass & CG Stations", fontsize=11.5, fontweight="bold")
    ax_comp.grid(axis="x", linestyle=":", alpha=0.6)
    ax_comp.legend(loc="lower right", fontsize=8.5)

    def _create_tooltip(ax):
        tip = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox={
                "boxstyle": "round,pad=0.4",
                "fc": "white",
                "ec": "#34495e",
                "alpha": 0.95,
            },
            arrowprops={"arrowstyle": "->", "color": "#34495e", "lw": 0.8},
            fontsize=8.5,
            zorder=10,
        )
        tip.set_visible(False)
        return tip

    tooltip_load = _create_tooltip(ax_load)
    tooltip_comp = _create_tooltip(ax_comp)

    def _on_hover(event) -> None:
        changed = False
        if event.inaxes == ax_load:
            matched = False
            for artist, states in ((line_fwd, fwd), (line_aft, aft)):
                hit, info = artist.contains(event)
                if hit and info.get("ind"):
                    idx = info["ind"][0]
                    state = states[idx]
                    tooltip_load.xy = (state.mac_fraction * 100.0, state.mass)
                    if state.added_item is not None:
                        added = state.added_item
                        lever = added.x_cg - state.x_cg
                        tooltip_text = (
                            f"{state.name}\n"
                            f"+{added.name}: {added.mass:.1f}\n"
                            f"Station: {added.x_cg:.2f} (Lever: {lever:+.2f} m)"
                        )
                    else:
                        tooltip_text = (
                            f"{state.name}\n"
                            f"Mass: {state.mass:.1f}\n"
                            f"CoG: {state.mac_fraction * 100:.1f}% MAC ({state.x_cg:.2f})"
                        )
                    tooltip_load.set_text(tooltip_text)
                    tooltip_load.set_visible(True)
                    matched = True
                    changed = True
                    break
            if not matched and tooltip_load.get_visible():
                tooltip_load.set_visible(False)
                changed = True
        elif tooltip_load.get_visible():
            tooltip_load.set_visible(False)
            changed = True

        if event.inaxes == ax_comp:
            hit, info = comp_scatter.contains(event)
            if hit and info.get("ind"):
                idx = info["ind"][0]
                comp = comps[idx]
                tooltip_comp.xy = (comp.x_cg, idx)
                tooltip_comp.set_text(
                    f"{comp.name}\n"
                    f"Mass: {comp.mass:.1f}\n"
                    f"x_CG: {comp.x_cg:.2f}"
                )
                tooltip_comp.set_visible(True)
                changed = True
            elif tooltip_comp.get_visible():
                tooltip_comp.set_visible(False)
                changed = True
        elif tooltip_comp.get_visible():
            tooltip_comp.set_visible(False)
            changed = True

        if changed:
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", _on_hover)

    plt.tight_layout()
    plt.show()
