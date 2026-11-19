"""Terminal reporting and 2D layout plot for fuselage sizing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.patches as patches
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from fuselage_sizing import FuselageDesign


def print_fuselage_summary(fuselage: FuselageDesign) -> None:
    """Prints a detailed terminal report of the fuselage sizing result."""
    fuse = fuselage.design.fuselage
    print("=" * 68)
    print(
        f"             FUSELAGE SIZING REPORT: {fuselage.n_pax}-PAX (1+1 CABIN LAYOUT)"
    )
    print("=" * 68)
    print(
        f"Passenger Capacity:          {fuselage.n_pax} PAX in {fuselage.n_rows} rows "
        f"({fuselage.n_front_rows}x 1+1, 1x 0+{fuselage.n_door_seats} RH at LH door, 3-seat rear bench)"
    )
    print(
        f"Seat Pitch:                  {fuse.seatPitch.si * 100:.1f} cm ({fuse.seatPitch.si / 0.0254:.1f} in)"
    )
    print(
        f"Seat Width / Aisle Width:    {fuse.seatWidth.si * 100:.1f} cm / {fuse.aisleWidth.si * 100:.1f} cm"
    )
    print("-" * 68)
    print("CROSS-SECTION DIMENSIONS (RECTANGULAR BOX):")
    print(f"  Cabin Internal Width:      {fuselage.cabin_width:.2f}")
    print(f"  Fuselage External Width:   {fuselage.width:.2f}")
    print(f"  Aisle Headroom (Interior): {fuse.aisleHeadroom.si:.2f}")
    print(f"  Fuselage External Height:  {fuselage.height:.2f}")
    print(f"  Fuselage Frontal Area:     {fuselage.frontal_area:.2f}")
    print("-" * 68)
    print("LONGITUDINAL SEGMENT BREAKDOWN:")
    print(f"  1. Nose & Cockpit:         {fuse.noseLength.si:.2f}")
    print(
        f"  2. Passenger Cabin:        {fuselage.cabin_length:.2f} ({fuselage.n_rows} rows)"
    )
    print(
        f"  3. Aft Baggage:            {fuselage.baggage_length:.2f} "
        f"(Vol: {fuselage.aft_baggage_volume:.2f}, Total: {fuselage.baggage_volume:.2f}, Req: {fuselage.cargo_volume_required:.2f})"
    )
    if fuse.underfloorBaggageHeight.si > 0:
        print(
            f"     Underfloor Hold:        {fuse.underfloorBaggageHeight.si:.2f} height "
            f"(Vol: {fuselage.underfloor_baggage_volume:.2f})"
        )
    print(f"  4. Tailcone:               {fuselage.tail_length:.2f}")
    print(f"  --> TOTAL FUSELAGE LENGTH: {fuselage.length:.2f}")
    print("-" * 68)
    print("AERODYNAMIC PROPERTIES:")
    print(f"  Slenderness Ratio (l/d):   {fuselage.slenderness_ratio:.2f}")
    print(f"  Fuselage Wetted Area:      {fuselage.wetted_area:.2f}")
    print("=" * 68)


def _add_rect(
    ax: Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    facecolor: str,
    edgecolor: str = "black",
    linewidth: float = 0.8,
    alpha: float = 1.0,
) -> None:
    """Adds a styled rectangular patch to the given axes."""
    ax.add_patch(
        patches.Rectangle(
            (x, y),
            width,
            height,
            fc=facecolor,
            ec=edgecolor,
            lw=linewidth,
            alpha=alpha,
        )
    )


def _plot_planform_shell(ax: Axes, fuselage: FuselageDesign, color: str) -> None:
    """Draws the planform fuselage contour, centerline, and section bulkheads."""
    w2 = fuselage.width / 2.0
    nose_length = fuselage.design.fuselage.noseLength.si
    x_nose_taper = nose_length * 0.35
    x_cockpit = nose_length
    x_cabin = x_cockpit + fuselage.cabin_length
    x_baggage = x_cabin + fuselage.baggage_length
    x_tail = fuselage.length

    xs = [0.0, x_nose_taper, x_cockpit, x_baggage, x_tail]
    ys_top = [0.0, w2 * 0.72, w2, w2, 0.06]
    ys_bot = [-y for y in ys_top]

    ax.plot(xs, ys_top, color=color, lw=2.5)
    ax.plot(xs, ys_bot, color=color, lw=2.5)
    ax.fill_between(xs, ys_bot, ys_top, color=color, alpha=0.10)
    ax.plot([0.0, x_tail], [0.0, 0.0], color="gray", ls="-.", lw=0.7, alpha=0.35)

    for x_part, label in (
        (x_cockpit, "Cockpit"),
        (x_cabin, f"Cabin ({fuselage.n_rows} rows)"),
        (x_baggage, "Aft Baggage"),
    ):
        ax.axvline(x_part, color="gray", ls="--", lw=1.1, alpha=0.8)
        ax.text(
            x_part - 0.15,
            w2 + 0.10,
            label,
            va="bottom",
            ha="right",
            fontsize=8.5,
            color="dimgray",
        )

    ax.text(
        x_cockpit + 0.15,
        w2 + 0.08,
        "RH (Starboard)",
        fontsize=8,
        color="gray",
        va="bottom",
    )
    ax.text(
        x_cockpit + 0.15,
        -w2 - 0.12,
        "LH (Port)",
        fontsize=8,
        color="gray",
        va="top",
    )


def _plot_planform_doors(ax: Axes, fuselage: FuselageDesign) -> None:
    """Draws the 1-row port (LH) rear passenger entry door in planform."""
    fuse = fuselage.design.fuselage
    w2 = fuselage.width / 2.0
    row_start = fuse.noseLength.si + fuse.frontBulkheadClearance.si
    seat_pitch = fuse.seatPitch.si
    door_start = row_start + fuselage.n_front_rows * seat_pitch - 0.15
    door_end = door_start + seat_pitch

    ax.plot(
        [door_start, door_end],
        [-w2, -w2],
        color="#d35400",
        lw=4.5,
        label="LH Entry Door",
    )


def _plot_planform_seats(ax: Axes, fuselage: FuselageDesign, color: str) -> None:
    """Draws cockpit crew seats and passenger cabin seats in 1:1 lateral scale."""
    fuse = fuselage.design.fuselage
    w2 = fuselage.width / 2.0
    nose_length = fuse.noseLength.si
    seat_pitch = fuse.seatPitch.si
    seat_width = fuse.seatWidth.si
    wall_clearance = fuse.wallClearance.si

    cockpit_x = nose_length * 0.55
    for y_crew in (-w2 * 0.55, w2 * 0.55 - 0.36):
        _add_rect(ax, cockpit_x, y_crew, 0.42, 0.36, facecolor="gray", alpha=0.7)

    row_start = nose_length + fuse.frontBulkheadClearance.si
    seat_len = min(0.50, 0.65 * seat_pitch)
    half_cabin = fuselage.cabin_width / 2.0

    y_left = -half_cabin + wall_clearance
    y_right = half_cabin - wall_clearance - seat_width
    y_bench_left = -half_cabin + wall_clearance
    y_bench_center = -seat_width / 2.0
    y_bench_right = half_cabin - wall_clearance - seat_width
    y_door_inner = y_bench_right - seat_width

    seat_coords: list[tuple[float, float]] = []
    for row_idx in range(fuselage.n_front_rows):
        x_seat = row_start + row_idx * seat_pitch
        seat_coords.append((x_seat, y_left))
        seat_coords.append((x_seat, y_right))

    x_door_row = row_start + fuselage.n_front_rows * seat_pitch
    door_ys = (
        (y_bench_right, y_door_inner) if fuselage.n_door_seats == 2 else (y_right,)
    )
    for y_seat in door_ys:
        seat_coords.append((x_door_row, y_seat))

    x_bench = row_start + (fuselage.n_rows - 1) * seat_pitch
    for y_seat in (y_bench_left, y_bench_center, y_bench_right):
        seat_coords.append((x_bench, y_seat))

    for x_seat, y_seat in seat_coords:
        _add_rect(ax, x_seat, y_seat, seat_len, seat_width, facecolor=color)


def _draw_planform(ax: Axes, fuselage: FuselageDesign, color: str) -> None:
    """Draws the top-down fuselage planform layout."""
    _plot_planform_shell(ax, fuselage, color)
    _plot_planform_doors(ax, fuselage)
    _plot_planform_seats(ax, fuselage, color)

    ax.set_xlim(-0.5, fuselage.length + 0.8)
    ax.set_ylim(-1.35, 1.50)
    ax.set_aspect("equal")
    ax.set_xlabel("Fuselage Station (Nose to Tail) [m]", fontsize=10)
    ax.set_ylabel("Lateral Width [m]", fontsize=9.5)
    ax.set_title(
        f"Planform (1+1 Cabin Layout) – Length: {fuselage.length:.2f} | Width: {fuselage.width:.2f}",
        fontsize=11,
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(True, linestyle=":", alpha=0.5)


def _plot_cross_section_shell(ax: Axes, fuselage: FuselageDesign, color: str) -> float:
    """Draws the rectangular fuselage cross-section shell, floor, and aisle headroom."""
    fuse = fuselage.design.fuselage
    w2 = fuselage.width / 2.0
    h2 = fuselage.height / 2.0
    wall_thickness = fuse.wallThickness.si
    floor_height = fuse.floorStructuralDepth.si
    underfloor_height = fuse.underfloorBaggageHeight.si
    belly_wall = wall_thickness if underfloor_height > 0 else 0.0
    aisle_headroom = fuse.aisleHeadroom.si
    aisle_width = fuse.aisleWidth.si
    y_floor = -h2 + belly_wall + underfloor_height + floor_height

    outer_box = patches.FancyBboxPatch(
        (-w2, -h2),
        fuselage.width,
        fuselage.height,
        boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=fuselage.corner_radius),
        fc=color,
        alpha=0.15,
        ec=color,
        lw=2.5,
    )
    ax.add_patch(outer_box)

    inner_r = max(0.05, fuselage.corner_radius - wall_thickness)
    inner_box = patches.FancyBboxPatch(
        (-fuselage.cabin_width / 2.0, y_floor),
        fuselage.cabin_width,
        aisle_headroom,
        boxstyle=patches.BoxStyle("Round", pad=0, rounding_size=inner_r),
        fc="none",
        ec="gray",
        ls="--",
        lw=1.0,
    )
    ax.add_patch(inner_box)

    if underfloor_height > 0:
        underfloor_box = patches.Rectangle(
            (-fuselage.cabin_width / 2.0, -h2 + belly_wall),
            fuselage.cabin_width,
            underfloor_height,
            fc="#d35400",
            alpha=0.12,
            ec="#d35400",
            ls="--",
            lw=1.0,
        )
        ax.add_patch(underfloor_box)
        ax.text(
            0.0,
            -h2 + belly_wall + underfloor_height / 2.0,
            f"Underfloor Hold ({underfloor_height:.2f})",
            ha="center",
            va="center",
            fontsize=8,
            color="#a04000",
        )

    ax.plot(
        [-fuselage.cabin_width / 2.0, fuselage.cabin_width / 2.0],
        [y_floor, y_floor],
        color="black",
        lw=2.0,
    )
    ax.plot(
        [-aisle_width / 2.0, aisle_width / 2.0],
        [y_floor, y_floor],
        color="#c0392b",
        lw=3.0,
        label=f"Aisle ({aisle_width * 100:.0f} cm)",
    )

    ax.annotate(
        "",
        xy=(0, y_floor),
        xytext=(0, y_floor + aisle_headroom),
        arrowprops=dict(arrowstyle="<->", color="darkred", lw=1.5),
    )
    ax.text(
        0.05,
        y_floor + aisle_headroom / 2.0,
        f"Headroom\n{aisle_headroom:.2f}",
        color="darkred",
        fontsize=8.5,
        va="center",
    )
    return y_floor


def _plot_cross_section_seats(
    ax: Axes,
    fuselage: FuselageDesign,
    y_floor: float,
    color: str,
) -> None:
    """Draws elevated 1+1 seats in the cross-section aligned with planform coordinates."""
    fuse = fuselage.design.fuselage
    seat_width = fuse.seatWidth.si
    wall_clearance = fuse.wallClearance.si

    half_cabin = fuselage.cabin_width / 2.0
    left_seat_x = -half_cabin + wall_clearance
    right_seat_x = half_cabin - wall_clearance - seat_width

    pedestal_h = 0.35
    cushion_h = 0.10
    backrest_h = 0.67

    for seat_x in (left_seat_x, right_seat_x):
        for leg_x in (seat_x + 0.08, seat_x + seat_width - 0.12):
            _add_rect(ax, leg_x, y_floor, 0.04, pedestal_h, facecolor="dimgray")

        _add_rect(
            ax,
            seat_x,
            y_floor + pedestal_h,
            seat_width,
            cushion_h,
            facecolor=color,
            linewidth=1.0,
        )
        _add_rect(
            ax,
            seat_x,
            y_floor + pedestal_h + cushion_h,
            seat_width,
            backrest_h,
            facecolor=color,
            linewidth=1.0,
            alpha=0.75,
        )


def _draw_cross_section(ax: Axes, fuselage: FuselageDesign, color: str) -> None:
    """Draws the rectangular fuselage cross-section with elevated 1+1 seats."""
    h2 = fuselage.height / 2.0
    y_floor = _plot_cross_section_shell(ax, fuselage, color)
    _plot_cross_section_seats(ax, fuselage, y_floor, color)

    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-h2 * 1.18, h2 * 1.18)
    ax.set_aspect("equal")
    ax.set_xlabel("Width [m]", fontsize=9.5)
    ax.set_ylabel("Height [m]", fontsize=9.5)
    ax.set_title(
        f"Cross-Section (1+1 Rectangular Box) – Area: {fuselage.frontal_area:.2f}",
        fontsize=10,
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(True, linestyle=":", alpha=0.5)


def plot_fuselage_sizing(fuselage: FuselageDesign) -> None:
    """Plots 2D planform and cross-section for the fuselage layout."""
    fig = plt.figure(figsize=(15, 4.8))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.0, 1])

    ax_plan = fig.add_subplot(gs[0, 0])
    ax_cs = fig.add_subplot(gs[0, 1])

    _draw_planform(ax_plan, fuselage, "#2980b9")
    _draw_cross_section(ax_cs, fuselage, "#2980b9")

    fig.suptitle(
        f"{fuselage.n_pax}-Passenger Commuter Fuselage Sizing (1+1 Layout)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    plt.show()
