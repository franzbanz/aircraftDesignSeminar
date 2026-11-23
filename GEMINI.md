# Project Guidelines & Coding Rules

## UnitValue and SiValue
- **No Redundant Type Casting**: Do **not** cast `UnitValue` or `SiValue` instances to `float(...)` or `int(...)` unnecessarily.
  - `UnitValue` and `SiValue` implement `__float__`, arithmetic operators (`+`, `-`, `*`, `/`, `**`), and formatting.
  - Do **not** access `.value` or `.si` unless strictly required (e.g. for specific unit conversions via `.to(...)` or for third-party libraries like numpy arrays that demand raw floats).
- **Default Parameters**: Do not hardcode magic numbers or fallback defaults when values can and should be loaded dynamically from `reference_aircraft.json` or `design_parameters.json`.

## Code Style & Formatting
- **No Backward-Compatibility Aliases**: Do **not** keep deprecated wrapper functions, compatibility shims, or legacy aliases. When refactoring or renaming a function, replace all usages across the codebase directly and delete the old name entirely.
- **No Visual Separator Banners**: Strictly do **not** add decorative section banner comments (e.g., `# ==============================================================================`).
- **Separation of Concerns**:
  - Keep numerical calculations, text output/printing, and plotting functions cleanly separated (e.g. `calc_*`, `print_*`, `plot_*`).
  - Do not mix plotting (`plt.show()`) or terminal prints into core calculation functions.
- **Documentation & Citations**:
  - Write concise, English docstrings.
  - When implementing formulas from lecture slides or literature, cite the exact source and page in docstrings: `[Strohmayer - Flugzeugentwurf 2 | p. <page>]`.

## Tooling & Package Management
- **Always use `uv`**:
  - Always use `uv` for package management, dependency locking, and running project commands (e.g. `uv run python ...`, `uv run ruff ...`, `uv run ty ...`).
  - Do not use raw `pip` or maintain a `requirements.txt`. All dependencies and developer tools are declared in `pyproject.toml` with `uv.lock`.


