"""Print summary for the reference aircraft (Dornier 228)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reference_aircraft import ReferenceAircraft


def print_reference_aircraft(ref: ReferenceAircraft) -> None:
    """Prints a structured summary of reference aircraft given inputs and calculated values."""
    print("=" * 65)
    print("                      REFERENCE AIRCRAFT")
    print("=" * 65)

    print("\n--- GIVEN PARAMETERS (FROM JSON) ---")
    print(f"MTOM:                            {ref.data.mass.takeOffMassMax}")
    print(f"MLM:                             {ref.data.mass.landingMassMax}")
    print(f"MZFM:                            {ref.data.mass.zeroFuelMassMax}")
    print(f"Payload:                         {ref.data.mass.payload}")
    print(f"Wing area (S_W):                 {ref.data.dimensions.wingArea}")
    print(f"Wingspan (b_W):                  {ref.data.dimensions.wingspan}")
    print(f"Fuselage length (l_R):           {ref.data.dimensions.fuselageLength}")
    print(f"Fuselage width (b_R):            {ref.data.dimensions.fuselageWidth}")
    print(f"Fuselage height (h_R):           {ref.data.dimensions.fuselageHeight}")
    print(f"Horizontal tail area (S_HTP):    {ref.data.dimensions.horizontalTailArea}")
    print(f"Vertical tail area (S_VTP):      {ref.data.dimensions.verticalTailArea}")
    print(f"Limit load factor (n_max):       {ref.data.assumptions.limitLoad}")
    print(
        f"Zero-lift drag (c_W0):           {ref.data.aerodynamics.zeroLiftDragCoefficient:.4f}"
    )

    print("\n--- CALCULATED VALUES (DERIVED) ---")
    print(f"Aspect ratio (AR):                   {ref.aspect_ratio:.3f}")
    print(f"Mean aerodynamic chord (c_mu):       {ref.mean_aerodynamic_chord:.3f}")
    print(f"Ultimate load factor (n_ult):        {ref.ultimate_load_factor:.2f}")
    print(f"Horizontal tail arm (r_H):           {ref.horizontal_tail_lever_arm}")
    print(
        f"Horizontal tail volume coeff (c_HT): {ref.horizontal_tail_volume_coefficient:.4f}"
    )
    print(f"Vertical tail arm (r_V):             {ref.vertical_tail_lever_arm}")
    print(
        f"Vertical tail volume coeff (c_VT):   {ref.vertical_tail_volume_coefficient:.4f}"
    )
    print(f"Cruise lift coefficient (c_A):       {ref.cruise_lift_coefficient:.4f}")
    print(f"Induced drag coeff (c_Wi):           {ref.induced_drag_coefficient:.4f}")
    print(
        f"Wing zero-lift drag (c_W0,wing):     {ref.wing_zero_lift_drag_coefficient:.4f}"
    )

    print("\n--- FORMULA MASS ESTIMATIONS & CALIBRATION FACTORS ---")
    print(
        f"Wing:         Catalog: {ref.data.mass.wing:>7} | Formula: {ref.wing_estimated_mass:>10.2f} | Factor: {ref.wing_calibration_factor:.4f}"
    )
    print(
        f"Fuselage:     Catalog: {ref.data.mass.fuselage:>7} | Formula: {ref.fuselage_estimated_mass:>10.2f} | Factor: {ref.fuselage_calibration_factor:.4f}"
    )
    print(
        f"Empennage:    Catalog: {ref.data.mass.empennage:>7} | Formula: {ref.empennage_estimated_mass:>10.2f} | Factor: {ref.empennage_calibration_factor:.4f}"
    )
    print(
        f"Landing gear: Catalog: {ref.data.mass.landingGear:>7} | Formula: {ref.landing_gear_estimated_mass:>10.2f} | Factor: {ref.landing_gear_calibration_factor:.4f}"
    )
    print(
        f"Pylons:       Catalog: {ref.data.mass.pylons:>7} | Formula: {ref.pylons_estimated_mass:>10.2f} | Factor: {ref.pylons_calibration_factor:.4f}"
    )
    print(
        f"Systems:      Catalog: {ref.data.mass.systems:>7} | Formula: {ref.systems_estimated_mass:>10.2f} | Factor: {ref.systems_calibration_factor:.4f}"
    )
    print("=" * 65 + "\n")
