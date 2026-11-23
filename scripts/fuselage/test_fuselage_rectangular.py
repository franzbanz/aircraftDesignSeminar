"""Run the 2-seats-per-row example from Excel sheet 'square', row 3."""

from math import isclose
from fuselage_rectangular import calculate_rectangular_fuselage


def main() -> None:
    # Inputs A3:M3 from the original workbook.
    result = calculate_rectangular_fuselage(
        pax=19,
        seats_per_row=2,
        cabin_inner_height=1.6,
        cabin_floor_thickness=0.15,
        under_cabin_room_height=0.3,
        seat_width=0.5,
        seat_pitch=0.8,
        aisle_width=0.45,
        rest_length_main_door=0.4,
        rest_length_emergency_exit=0.3,
        wall_thickness=0.1,
        extra_length_crew=0,
        luggage_rack_height=1.4,
    )

    # Check each output against the Excel row-3 cached result.
    expected = {
        "rows": 10,
        "cabin_width": 1.45,
        "width": 1.55,
        "front_fuselage": 2.325,
        "rear_fuselage": 3.5185,
        "cabin_length": 8.7,
        "length": 14.5435,
        "fuselage_fineness_ratio": 9.382903225806452,
        "fuselage_height": 2.25,
        "volume_excluding_cabin": 3.7845,
        "luggage_space_above_seat": 1.74,
        "fuselage_cross_sectional_area": 3.4875,
        "fuselage_wetted_area": 94.16885480325253,
    }
    for name, expected_value in expected.items():
        assert isclose(result[name], expected_value, rel_tol=1e-10, abs_tol=1e-10), (
            f"{name}: Python={result[name]}, Excel={expected_value}"
        )

    print("Rectangular fuselage sizing — 2 seats per row")
    print("---------------------------------------------")
    units = {
        "rows": "rows",
        "fuselage_fineness_ratio": "(dimensionless)",
        "volume_excluding_cabin": "m^3",
        "luggage_space_above_seat": "m^3",
        "fuselage_cross_sectional_area": "m^2",
        "fuselage_wetted_area": "m^2",
    }
    for name, value in result.items():
        unit = units.get(name, "m")
        shown = str(value) if isinstance(value, int) else f"{value:.6f}"
        print(f"{name:33s}: {shown:>12s} {unit}")
    print("\nAll 13 outputs match the Excel 2-seats-per-row case.")


if __name__ == "__main__":
    main()
