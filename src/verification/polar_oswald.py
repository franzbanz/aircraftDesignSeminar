"""Verification script demonstrating that the reference drag polar follows a parabolic polar with constant Oswald factor e."""

import math
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reference_aircraft import load_reference_aircraft

# Reference drag polar table from specification
POLAR_CL = (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
POLAR_CD = (
    0.0260,
    0.0276,
    0.0295,
    0.0322,
    0.0357,
    0.0400,
    0.0450,
    0.0508,
    0.0574,
    0.0648,
)


def verify_polar_oswald_approximation() -> None:
    """Prints point-by-point Oswald factors, least-squares fit e_fit, and drag deviations."""
    ref = load_reference_aircraft()
    ar = ref.aspect_ratio
    cd0 = POLAR_CD[0]

    # Point-by-point Oswald efficiency factors e(C_L) for C_L > 0
    e_pts = [
        (cl**2) / (math.pi * ar * (cd - cd0))
        for cl, cd in zip(POLAR_CL[1:], POLAR_CD[1:])
    ]

    # Least-squares fit for constant k = 1 / (pi * AR * e)
    x = np.array(POLAR_CL[1:]) ** 2
    y = np.array(POLAR_CD[1:]) - cd0
    k_fit = float(np.sum(x * y) / np.sum(x**2))
    e_fit = 1.0 / (math.pi * ar * k_fit)

    e_json = float(ref.data.assumptions.oswaldFactor)

    print("=" * 95)
    print(
        "         VERIFICATION: PARABOLIC POLAR & OSWALD EFFICIENCY FACTOR APPROXIMATION"
    )
    print("=" * 95)
    print(
        f"Reference Wing Aspect Ratio (AR):    {ar:.4f} (b = {ref.data.dimensions.wingspan}, S = {ref.data.dimensions.wingArea})"
    )
    print(f"Zero-Lift Drag Coefficient (C_D0):   {cd0:.4f} (from polar at C_L = 0)")
    print(
        f"Derived Cruise C_W0 (Reference):     {ref.zero_lift_drag_coefficient:.4f} (from L/D_cruise = {ref.data.aerodynamics.liftToDragRatioCruise})"
    )
    print(f"Least-Squares Fitted Oswald (e_fit): {e_fit:.4f}")
    print(f"Configured JSON Oswald (e_json):     {e_json:.4f}\n")

    print(
        f"{'C_L':>4} | {'C_D (Tab)':>9} | {'e(C_L)':>7} || "
        f"{'C_D(e_fit)':>10} | {'ΔC_D [cts]':>10} | {'ΔC_D [%]':>8} | {'L/D(e_fit)':>10} || "
        f"{'C_D(e_json)':>11} | {'ΔC_D(json)':>10}"
    )
    print("-" * 95)

    for i, (cl, cd) in enumerate(zip(POLAR_CL, POLAR_CD)):
        e_str = f"{e_pts[i - 1]:.4f}" if i > 0 else "   -  "

        cd_fit = cd0 + (cl**2) / (math.pi * ar * e_fit)
        d_fit_cts = (cd_fit - cd) * 1e4  # 1 drag count = 1e-4
        d_fit_pct = ((cd_fit - cd) / cd) * 100.0
        ld_fit = cl / cd_fit if cl > 0 else 0.0

        cd_j = cd0 + (cl**2) / (math.pi * ar * e_json)
        d_j_pct = ((cd_j - cd) / cd) * 100.0

        print(
            f"{cl:4.1f} | {cd:9.4f} | {e_str:>7} || "
            f"{cd_fit:10.4f} | {d_fit_cts:+10.2f} | {d_fit_pct:+7.2f}% | {ld_fit:10.1f} || "
            f"{cd_j:11.4f} | {d_j_pct:+9.2f}%"
        )
    print("=" * 95)


if __name__ == "__main__":
    verify_polar_oswald_approximation()
