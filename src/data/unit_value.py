"""Unit-aware numeric value and SI value types with automatic conversion capabilities."""

from typing import Self


class UnitValue(float):
    """Numeric value with an associated physical unit.

    Subclasses ``float`` so instances can be used directly in standard arithmetic
    expressions while preserving the original raw value and physical unit string.

    Attributes:
        _raw: Original numeric value (int or float) as loaded from JSON or initialized.
        unit: Physical unit string (e.g., ``"kg"``, ``"m"``, ``"kts"``, ``""``).
    """

    _raw: int | float
    unit: str

    _TEMP_UNITS: set[str] = {"degc", "c", "k", "degf", "f"}

    # Canonical SI base unit mapping: unit -> (canonical_si_base, factor_to_base)
    _UNITS: dict[str, tuple[str, float]] = {
        # Speed (SI: m/s)
        "m/s": ("m/s", 1.0),
        "kt": ("m/s", 1852.0 / 3600.0),
        "kts": ("m/s", 1852.0 / 3600.0),
        "km/h": ("m/s", 1.0 / 3.6),
        # Length (SI: m)
        "m": ("m", 1.0),
        "km": ("m", 1e3),
        "nm": ("m", 1852.0),
        "ft": ("m", 0.3048),
        # Area (SI: m^2)
        "m^2": ("m^2", 1.0),
        # Volume (SI: m^3)
        "m^3": ("m^3", 1.0),
        "l": ("m^3", 1e-3),
        "liters": ("m^3", 1e-3),
        # Mass (SI: kg)
        "kg": ("kg", 1.0),
        "t": ("kg", 1e3),
        "lb": ("kg", 0.45359237),
        "lbs": ("kg", 0.45359237),
        # Time (SI: s)
        "s": ("s", 1.0),
        "min": ("s", 60.0),
        "h": ("s", 3600.0),
        # Power (SI: W)
        "w": ("w", 1.0),
        "kw": ("w", 1e3),
        "mw": ("w", 1e6),
        "hp": ("w", 745.699872),
        # Energy (SI: J)
        "j": ("j", 1.0),
        "kj": ("j", 1e3),
        "mj": ("j", 1e6),
        "wh": ("j", 3600.0),
        "kwh": ("j", 3.6e6),
        # Energy Density (SI: J/kg)
        "j/kg": ("j/kg", 1.0),
        "wh/kg": ("j/kg", 3600.0),
        "kwh/kg": ("j/kg", 3.6e6),
        "mj/kg": ("j/kg", 1e6),
        # Pressure (SI: Pa)
        "pa": ("pa", 1.0),
        "hpa": ("pa", 100.0),
        "kpa": ("pa", 1e3),
        "bar": ("pa", 1e5),
        "mbar": ("pa", 100.0),
        # Surface density / Wing loading (SI: kg/m^2)
        "kg/m^2": ("kg/m^2", 1.0),
        # Density (SI: kg/m^3)
        "kg/m^3": ("kg/m^3", 1.0),
        # Acceleration (SI: m/s^2)
        "m/s^2": ("m/s^2", 1.0),
        # Force (SI: N)
        "n": ("n", 1.0),
        "kn": ("n", 1e3),
        "mn": ("n", 1e6),
        "lbf": ("n", 4.4482216152605),
        # Fuel consumption (TSFC) (SI: kg/(N*s))
        "kg/(n*s)": ("kg/(n*s)", 1.0),
        "lb/(h*lbf)": ("kg/(n*s)", 1.0 / (3600.0 * 9.80665)),
        # Dimensionless
        "": ("", 1.0),
    }

    def __new__(cls, value: int | float, unit: str = "") -> Self:
        """Creates a new UnitValue instance with a numeric value and unit.

        Args:
            value: Numeric value.
            unit: Physical unit string associated with the value.
        """
        obj = super().__new__(cls, value)
        obj._raw = value
        obj.unit = unit
        return obj

    def to(self, target_unit: str) -> "UnitValue":
        """Converts the value to another compatible physical unit.

        Returns an ``SiValue`` if ``target_unit`` is the canonical SI base unit,
        or a standard ``UnitValue`` otherwise.

        Args:
            target_unit: Target unit string (e.g. 'm', 'km', 'kts', 'kwh', 'degC', 'K').

        Returns:
            A new SiValue or UnitValue instance with the converted value and target_unit.

        Raises:
            ValueError: If the unit is unknown or conversion is incompatible.
        """
        src = self.unit.strip().lower()
        dst = target_unit.strip().lower()

        if src == dst:
            converted_val = self._raw
            dst_base = src
        elif src in self._TEMP_UNITS or dst in self._TEMP_UNITS:
            converted_val = self._convert_temperature(float(self._raw), src, dst)
            dst_base = "k"
        else:
            if src not in self._UNITS:
                raise ValueError(f"Unknown source unit: '{self.unit}'")
            if dst not in self._UNITS:
                raise ValueError(f"Unknown target unit: '{target_unit}'")

            src_base, src_factor = self._UNITS[src]
            dst_base, dst_factor = self._UNITS[dst]

            if src_base != dst_base:
                raise ValueError(
                    f"Incompatible unit conversion from '{self.unit}' ({src_base}) to '{target_unit}' ({dst_base})"
                )

            converted_val = float(self._raw) * (src_factor / dst_factor)

        if dst == dst_base:
            return SiValue(converted_val, target_unit)
        return UnitValue(converted_val, target_unit)

    @property
    def si(self) -> "SiValue":
        """Converts the value to its canonical SI base unit and returns an SiValue instance."""
        return SiValue(self._raw, self.unit)

    @staticmethod
    def _convert_temperature(val: float, src: str, dst: str) -> float:
        """Converts temperature between degC/C, K, and degF/F."""
        if src in ("degc", "c"):
            k = val + 273.15
        elif src == "k":
            k = val
        elif src in ("degf", "f"):
            k = (val - 32.0) * (5.0 / 9.0) + 273.15
        else:
            raise ValueError(f"Unknown source temperature unit: '{src}'")

        if dst in ("degc", "c"):
            return k - 273.15
        if dst == "k":
            return k
        if dst in ("degf", "f"):
            return (k - 273.15) * 1.8 + 32.0
        raise ValueError(f"Unknown target temperature unit: '{dst}'")

    @property
    def value(self) -> int | float:
        """Returns the original numeric value without unit formatting."""
        return self._raw

    def __str__(self) -> str:
        """Returns a formatted string combining the value and unit (e.g., ``'8618 kg'``)."""
        return f"{self._raw} {self.unit}".strip() if self.unit else str(self._raw)

    def __repr__(self) -> str:
        """Returns the unambiguous developer representation of the UnitValue."""
        return f"{type(self).__name__}({self._raw}, {self.unit!r})"


class SiValue(UnitValue):
    """Numeric quantity guaranteed to be in its canonical SI base unit.

    Subclasses ``UnitValue`` (and therefore ``float``) so instances can be used directly
    in standard arithmetic and physical formulas without unwrapping.

    When initialized with a non-SI unit (e.g. ``SiValue(5, "t")`` or ``SiValue(170, "kt")``),
    it automatically converts the value to its canonical SI base unit.
    """

    def __new__(cls, value: int | float, unit: str = "") -> Self:
        norm = unit.strip().lower()
        if norm:
            if norm in cls._TEMP_UNITS:
                if norm != "k":
                    converted = UnitValue(value, unit).to("k")
                    value, unit = converted._raw, "K"
                else:
                    unit = "K"
            elif norm in cls._UNITS:
                base_unit, factor = cls._UNITS[norm]
                if norm != base_unit:
                    value = float(value) * factor
                    unit = base_unit
            else:
                raise ValueError(f"Unknown unit: '{unit}'")
        return super().__new__(cls, value, unit)

    @property
    def si(self) -> Self:
        """Returns itself since it is already in its canonical SI unit."""
        return self
