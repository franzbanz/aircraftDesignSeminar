# Aircraft Design Seminar

Preliminary design, mass estimation, and performance sizing for an electric commuter aircraft.

## Configuration Files

All parameters in the JSON files are stored as `[value, "unit"]` pairs and are loaded into unit-aware `Parameter` objects (subclassing `float`, so they can be used directly in arithmetic while preserving `.value` and `.unit`).

- **`reference_aircraft.json`**: Contains all given data of the reference aircraft (masses, dimensions, aerodynamics, flight loads, propulsion). These values serve as the baseline and are used to calibrate the empirical estimation formulas.
- **`parameters.json`**: Contains the design requirements and constraints that must be met (e.g., mission range, field lengths, maximum take-off mass), as well as predefined assumptions and boundary conditions (e.g., mass per passenger, atmospheric conditions, battery energy density).

## Source Code (`src/`)

- **`read_parameters.py`**: Loads `parameters.json` into typed Python objects.
- **`read_reference_aircraft.py`**: Loads `reference_aircraft.json` and computes derived geometric properties and calibration factors.
- **`mass_formulas.py`**: Empirical (Torenbeek) mass estimation and aerodynamic geometry formulas.
- **`preliminary_estimation.py`**: Main calculation script for calibrated mass breakdown, range estimation, and wing sizing.

## Usage

Run the preliminary estimation from the project root:

```bash
python src/preliminary_estimation.py
```

Inspect the reference aircraft data and calibration factors:

```bash
python src/read_reference_aircraft.py
```
