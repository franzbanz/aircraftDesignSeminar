# Aircraft Design Seminar

Preliminary design, mass estimation, and performance sizing for a 19-passenger battery-electric commuter aircraft.

## Configuration Files (`config/`)

All parameters in the JSON files are stored as `[value, "unit"]` pairs and are loaded into unit-aware `UnitValue` / `SiValue` objects (subclassing `float`, so they can be used directly in arithmetic while preserving `.value` and `.unit`).

- **`config/constraints.json`**: Design requirements and regulatory/mission constraints (e.g., payload, mission range and reserves, take-off/landing field lengths, maximum take-off mass, maximum wingspan, battery energy density limits, and CS-23 requirements).
- **`config/design_parameters.json`**: Chosen design parameters and configuration assumptions for the target electric aircraft (wing, empennage, fuselage cabin layout, propulsion, mission profile, and CFRP technology factors).
- **`config/design_parameters_baseline.json`**: Baseline configuration parameter set for comparison studies (`--baseline`).
- **`config/reference_aircraft.json`**: Datasheet specifications and assumptions of the reference aircraft (Dornier 228-212), used as the baseline to calibrate the empirical Torenbeek mass estimation formulas.

## Source Code (`src/`)

- **`aircraft_design.py`**: Main entry point for the iterative MTOM convergence, calibrated mass breakdown, sizing diagram evaluation, and interactive visualization menu.
- **`aircraft.py`**: Core `BatteryAircraft` model combining component sizing, mass estimation, mission energy, and MTOM convergence.
- **`reference_aircraft.py`**: `ReferenceAircraft` model computing derived geometric properties, cruise aerodynamics, and component mass calibration factors.
- **`wing.py` / `fuselage.py` / `empennage.py`**: Component-level geometry, aerodynamic polar, and calibrated structural mass models (including physical wing-battery root bending moment relief and CS-23 cabin layout sizing).
- **`sizing_diagram.py`**: Thrust- and power-loading matching chart calculator (stall, landing distance, take-off distance, OEI climb, and cruise constraints).
- **`mission_energy.py`**: Reference fuel-fraction analysis and electric mission energy / battery mass calculation.
- **`data/`**: Typed dataclasses (`Constraints`, `DesignParameters`, `ReferenceAircraftData`), JSON loader (`loader.py`), and unit conversion (`unit_value.py`).
- **`formulas/`**: Pure mathematical formulas for Torenbeek component masses (`mass.py`), geometry (`geometry.py`), aerodynamics (`aerodynamics.py`), propulsion (`propulsion.py`), and Breguet range (`breguet.py`).
- **`visualizations/`**: Terminal summary printers and Matplotlib plotting functions.

## Standalone Scripts (`scripts/`)

- **`cl_max.py`** & **`landing_gear_estimation.py`**: Standalone analysis tools for high-lift $C_{L,\max}$ requirements and landing gear concept trade-offs.
- **`fuselage/`**, **`ideas/`**, **`verification/`**: Exploration and verification scripts (e.g., wing bending relief, polar Oswald factor fitting).
- **`approximateMass.py`**, **`calculateRemainingDrag.py`**, **`generateSizingDiagram.py`**: Additional standalone calculation scripts operating on `scripts/parameters.json` and `scripts/battery_aircraft.json`.

## Usage

Run the main aircraft design tool from the project root using `uv`:

```bash
uv run python src/aircraft_design.py
```

Use `--baseline` to evaluate the baseline parameter set or `--design` for a custom JSON file:

```bash
uv run python src/aircraft_design.py --baseline
```

Inspect individual modules directly:

```bash
uv run python src/reference_aircraft.py
uv run python src/fuselage.py
uv run python src/mission_energy.py
```
