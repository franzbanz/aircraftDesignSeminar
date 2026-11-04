"""Unit-aware numeric value with automatic conversion capabilities."""

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

    _CONVERSIONS: dict[tuple[str, str], float] = {
        # Length
        ("m", "km"): 1e-3,
        ("km", "m"): 1e3,
        ("m", "nm"): 1.0 / 1852.0,
        ("nm", "m"): 1852.0,
        ("km", "nm"): 1.0 / 1.852,
        ("nm", "km"): 1.852,
        ("m", "ft"): 1.0 / 0.3048,
        ("ft", "m"): 0.3048,
        ("km", "ft"): 1e3 / 0.3048,
        ("ft", "km"): 0.3048 / 1e3,
        ("ft", "nm"): 0.3048 / 1852.0,
        ("nm", "ft"): 1852.0 / 0.3048,
        # Speed
        ("kt", "m/s"): 1852.0 / 3600.0,
        ("m/s", "kt"): 3600.0 / 1852.0,
        ("kts", "m/s"): 1852.0 / 3600.0,
        ("m/s", "kts"): 3600.0 / 1852.0,
        ("kt", "km/h"): 1.852,
        ("km/h", "kt"): 1.0 / 1.852,
        ("kts", "km/h"): 1.852,
        ("km/h", "kts"): 1.0 / 1.852,
        ("km/h", "m/s"): 1.0 / 3.6,
        ("m/s", "km/h"): 3.6,
        # Mass
        ("kg", "t"): 1e-3,
        ("t", "kg"): 1e3,
        ("kg", "lb"): 2.20462262185,
        ("lb", "kg"): 1.0 / 2.20462262185,
        ("kg", "lbs"): 2.20462262185,
        ("lbs", "kg"): 1.0 / 2.20462262185,
        # Time
        ("s", "min"): 1.0 / 60.0,
        ("min", "s"): 60.0,
        ("min", "h"): 1.0 / 60.0,
        ("h", "min"): 60.0,
        ("s", "h"): 1.0 / 3600.0,
        ("h", "s"): 3600.0,
        # Power
        ("w", "kw"): 1e-3,
        ("kw", "w"): 1e3,
        ("kw", "mw"): 1e-3,
        ("mw", "kw"): 1e3,
        ("w", "mw"): 1e-6,
        ("mw", "w"): 1e6,
        ("kw", "hp"): 1.0 / 0.745699872,
        ("hp", "kw"): 0.745699872,
        ("w", "hp"): 1.0 / 745.699872,
        ("hp", "w"): 745.699872,
        # Energy
        ("j", "kj"): 1e-3,
        ("kj", "j"): 1e3,
        ("j", "mj"): 1e-6,
        ("mj", "j"): 1e6,
        ("kj", "mj"): 1e-3,
        ("mj", "kj"): 1e3,
        ("j", "wh"): 1.0 / 3600.0,
        ("wh", "j"): 3600.0,
        ("j", "kwh"): 1.0 / 3.6e6,
        ("kwh", "j"): 3.6e6,
        ("wh", "kwh"): 1e-3,
        ("kwh", "wh"): 1e3,
        ("mj", "kwh"): 1.0 / 3.6,
        ("kwh", "mj"): 3.6,
        # Energy Density
        ("wh/kg", "kwh/kg"): 1e-3,
        ("kwh/kg", "wh/kg"): 1e3,
        ("mj/kg", "kwh/kg"): 1.0 / 3.6,
        ("kwh/kg", "mj/kg"): 3.6,
        ("j/kg", "kwh/kg"): 1.0 / 3.6e6,
        ("kwh/kg", "j/kg"): 3.6e6,
        ("j/kg", "mj/kg"): 1e-6,
        ("mj/kg", "j/kg"): 1e6,
        ("wh/kg", "j/kg"): 3600.0,
        ("j/kg", "wh/kg"): 1.0 / 3600.0,
        # Volume
        ("l", "m^3"): 1e-3,
        ("m^3", "l"): 1e3,
        ("liters", "m^3"): 1e-3,
        ("m^3", "liters"): 1e3,
        ("l", "liters"): 1.0,
        ("liters", "l"): 1.0,
        # Pressure
        ("pa", "kpa"): 1e-3,
        ("kpa", "pa"): 1e3,
        ("pa", "bar"): 1e-5,
        ("bar", "pa"): 1e5,
        ("pa", "mbar"): 1e-2,
        ("mbar", "pa"): 1e2,
        ("pa", "hpa"): 1e-2,
        ("hpa", "pa"): 1e2,
        # Fuel consumption (TSFC)
        ("lb/(h*lbf)", "kg/(n*s)"): 1.0 / (3600.0 * 9.80665),
        ("kg/(n*s)", "lb/(h*lbf)"): 3600.0 * 9.80665,
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

        Args:
            target_unit: Target unit string (e.g. 'm', 'km', 'kts', 'kwh', 'degC', 'K').

        Returns:
            A new UnitValue instance with the converted value and target_unit.

        Raises:
            ValueError: If conversion between the units is not supported.
        """
        src = self.unit.strip().lower()
        dst = target_unit.strip().lower()

        if src == dst:
            return type(self)(self._raw, target_unit)

        temp_units = {"degc", "c", "k", "degf", "f"}
        if src in temp_units or dst in temp_units:
            return type(self)(self._convert_temperature(float(self._raw), src, dst), target_unit)

        if (src, dst) in self._CONVERSIONS:
            factor = self._CONVERSIONS[(src, dst)]
            return type(self)(float(self._raw) * factor, target_unit)

        for (u1, u2), f1 in self._CONVERSIONS.items():
            if u1 == src and (u2, dst) in self._CONVERSIONS:
                f2 = self._CONVERSIONS[(u2, dst)]
                return type(self)(float(self._raw) * f1 * f2, target_unit)

        raise ValueError(f"Unsupported unit conversion from '{self.unit}' to '{target_unit}'")

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

