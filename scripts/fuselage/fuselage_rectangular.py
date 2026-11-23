"""Rectangular fuselage sizing model converted from Excel sheet 'square'.

Source: Comparison of different fuselage sizing_Aurora.xlsx, cells A2:Z4.
All lengths are in meters, areas in m^2, volumes in m^3.
The formulas deliberately match the original workbook (including its
simplified wetted-area estimate and its single-thickness width increment).
"""

from math import ceil, pi, sqrt


def calculate_rectangular_fuselage(
    pax: int,
    seats_per_row: int,
    cabin_inner_height: float,
    cabin_floor_thickness: float,
    under_cabin_room_height: float,
    seat_width: float,
    seat_pitch: float,
    aisle_width: float,
    rest_length_main_door: float,
    rest_length_emergency_exit: float,
    wall_thickness: float,
    extra_length_crew: float,
    luggage_rack_height: float,
) -> dict:
    """Calculate the 13 outputs of the workbook's rectangular fuselage model.

    Inputs correspond, in order, to cells A:M on the 'square' worksheet.
    Output keys correspond to cells N:Z. This is a direct formula translation,
    not a correction or reinterpretation of the workbook's assumptions.
    """
    if pax <= 0 or seats_per_row <= 0:
        raise ValueError("pax and seats_per_row must be positive integers")
    if not isinstance(pax, int) or not isinstance(seats_per_row, int):
        raise TypeError("pax and seats_per_row must be integers")
    if any(v < 0 for v in (
        cabin_inner_height, cabin_floor_thickness, under_cabin_room_height,
        seat_width, seat_pitch, aisle_width, rest_length_main_door,
        rest_length_emergency_exit, wall_thickness, extra_length_crew,
        luggage_rack_height,
    )):
        raise ValueError("Dimension inputs must be non-negative")

    # Excel columns N:P: number of rows and transverse dimensions.
    rows = ceil(pax / seats_per_row)
    cabin_width = seats_per_row * seat_width + aisle_width
    width = cabin_width + wall_thickness  # Excel P3 (one thickness, as written)
    if width == 0:
        raise ValueError("Calculated fuselage width must be greater than zero")

    # Excel columns Q:U: longitudinal dimensions.
    front_fuselage = 1.5 * width
    rear_fuselage = 2.27 * width
    cabin_length = (rows * seat_pitch + rest_length_main_door
                    + extra_length_crew + rest_length_emergency_exit)
    length = cabin_length + rear_fuselage + front_fuselage
    fuselage_fineness_ratio = length / width

    # Excel columns V:Y: height, volumes and cross-section.
    fuselage_height = (cabin_inner_height + cabin_floor_thickness
                       + under_cabin_room_height + 2 * wall_thickness)
    volume_excluding_cabin = under_cabin_room_height * cabin_width * cabin_length
    luggage_space_above_seat = (
        (cabin_inner_height - luggage_rack_height)
        * seat_width * seats_per_row * cabin_length
    )
    fuselage_cross_sectional_area = fuselage_height * width

    # Excel Z3: four triangular-pyramid side areas plus PI()*P3*T3.
    # Note: PI()*width*length is preserved exactly even though this is a
    # rectangular fuselage (it is an approximation in the source spreadsheet).
    fuselage_wetted_area = (
        width * sqrt(front_fuselage**2 + (fuselage_height / 2)**2)
        + fuselage_height * sqrt(front_fuselage**2 + (width / 2)**2)
        + width * sqrt(rear_fuselage**2 + (fuselage_height / 2)**2)
        + fuselage_height * sqrt(rear_fuselage**2 + (width / 2)**2)
        + pi * width * length
    )

    return {
        "rows": rows,  # N: row
        "cabin_width": cabin_width,  # O
        "width": width,  # P
        "front_fuselage": front_fuselage,  # Q
        "rear_fuselage": rear_fuselage,  # R
        "cabin_length": cabin_length,  # S
        "length": length,  # T
        "fuselage_fineness_ratio": fuselage_fineness_ratio,  # U
        "fuselage_height": fuselage_height,  # V
        "volume_excluding_cabin": volume_excluding_cabin,  # W
        "luggage_space_above_seat": luggage_space_above_seat,  # X
        "fuselage_cross_sectional_area": fuselage_cross_sectional_area,  # Y
        "fuselage_wetted_area": fuselage_wetted_area,  # Z
    }
