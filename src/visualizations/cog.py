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
    print(f"Fuselage Length:   {cog.aircraft.fuselage.length:.2f} | LEMAC: {cog.x_lemac:.2f}")
    print(
        f"Wing MAC (c_mu):   {cog.aircraft.wing.mean_aerodynamic_chord:.2f} | "
        f"Wing AC (25%): {cog.x_wing_ac:.2f} | HTP AC: {cog.x_htp_ac:.2f}"
    )
    print("-" * 78)
    print(f"{'Component':<28} | {'Mass [kg]':>10} | {'x_CG [m]':>9} | {'Moment [kg*m]':>14}")
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
        cog.most_forward_state,
        cog.most_aft_state,
    ]
    print(f"{'Loading State':<28} | {'Mass [kg]':>10} | {'x_CG [m]':>9} | {'% MAC':>14}")
    print("-" * 78)
    for state in states:
        print(
            f"{state.name:<28} | {float(state.mass):10.1f} | "
            f"{float(state.x_cg):9.2f} | {state.mac_fraction * 100:13.1f}%"
        )
    print("-" * 78)
    print(
        f"CoG Travel (Fwd -> Aft):     {cog.cg_travel_mac * 100:.1f}% MAC "
        f"({float(cog.most_aft_state.x_cg - cog.most_forward_state.x_cg):.2f} m)"
    )
    print(
        f"Battery CG for 25.0% MAC:    {cog.required_battery_x_cg(0.25):.2f} "
        f"(Current: {cog.x_battery_cg:.2f})"
    )
    print("=" * 78 + "\n")


def plot_cog_excursion(cog: CenterOfGravity, label: str = "Electric Aircraft") -> None:
    """Plots the CoG loading excursion diagram (% MAC) and component CG positions."""
    fig, (ax_load, ax_comp) = plt.subplots(1, 2, figsize=(15, 6.5))
    fig.suptitle(f"Center of Gravity & Loading Diagram — {label}", fontsize=13, fontweight="bold")

    fwd = cog.forward_loading_curve
    aft = cog.aft_loading_curve

    fwd_mac = [s.mac_fraction * 100.0 for s in fwd]
    fwd_m = [float(s.mass) for s in fwd]
    aft_mac = [s.mac_fraction * 100.0 for s in aft]
    aft_m = [float(s.mass) for s in aft]

    ax_load.axvspan(15.0, 35.0, color="#2ecc71", alpha=0.12, label="Typical CoG Envelope (15–35% MAC)")
    ax_load.axvline(15.0, color="#27ae60", linestyle="--", lw=1.0)
    ax_load.axvline(35.0, color="#27ae60", linestyle="--", lw=1.0)
    ax_load.axvline(25.0, color="#7f8c8d", linestyle=":", lw=1.2, label="25% MAC (Aero Center)")

    ax_load.plot(fwd_mac, fwd_m, "-o", color="#2980b9", markersize=4, lw=1.8, label="Front-to-Back Loading")
    ax_load.plot(aft_mac, aft_m, "-s", color="#e67e22", markersize=4, lw=1.8, label="Back-to-Front Loading")

    empty = cog.zero_payload_state
    mtom = cog.mtom_state
    ax_load.scatter(
        [empty.mac_fraction * 100.0, mtom.mac_fraction * 100.0],
        [float(empty.mass), float(mtom.mass)],
        color=["#8e44ad", "#c0392b"],
        s=90,
        zorder=5,
    )
    ax_load.annotate(
        f"Empty + Bat\n({empty.mac_fraction * 100:.1f}% MAC)",
        (empty.mac_fraction * 100.0, float(empty.mass)),
        textcoords="offset points",
        xytext=(10, -10),
        fontsize=8.5,
        fontweight="bold",
        color="#8e44ad",
    )
    ax_load.annotate(
        f"MTOM\n({mtom.mac_fraction * 100:.1f}% MAC)",
        (mtom.mac_fraction * 100.0, float(mtom.mass)),
        textcoords="offset points",
        xytext=(10, -10),
        fontsize=8.5,
        fontweight="bold",
        color="#c0392b",
    )

    ax_load.set_xlabel("Center of Gravity Position [% MAC]", fontsize=10.5)
    ax_load.set_ylabel("Aircraft Mass [kg]", fontsize=10.5)
    ax_load.set_title("Loading Excursion Diagram", fontsize=11.5, fontweight="bold")
    ax_load.grid(True, linestyle=":", alpha=0.6)
    ax_load.legend(loc="lower right", fontsize=8.5)

    # Right panel: Component CG locations along fuselage length
    comps = cog.components
    y_pos = list(range(len(comps)))
    x_vals = [float(c.x_cg) for c in comps]
    masses = [float(c.mass) for c in comps]
    names = [f"{c.name} ({float(c.mass):.0f} kg)" for c in comps]

    l_fus = float(cog.aircraft.fuselage.length)
    lemac = float(cog.x_lemac)
    temac = lemac + float(cog.aircraft.wing.mean_aerodynamic_chord)

    ax_comp.axvspan(lemac, temac, color="#3498db", alpha=0.14, label="Wing MAC (LEMAC–TEMAC)")
    ax_comp.axvline(float(mtom.x_cg), color="#c0392b", linestyle="--", lw=1.5, label=f"MTOM CoG ({float(mtom.x_cg):.2f} m)")
    ax_comp.axvline(l_fus, color="#34495e", linestyle="-", lw=1.2, label=f"Tail End ({l_fus:.2f} m)")

    sizes = [max(35.0, m * 0.14) for m in masses]
    ax_comp.scatter(x_vals, y_pos, s=sizes, color="#2c3e50", zorder=4)
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

    plt.tight_layout()
    plt.show()
