"""Validated static configuration loading for the BCM simulator."""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when static simulator configuration is invalid."""


@dataclass(frozen=True, slots=True)
class InputConfig:
    identifier: str
    name: str
    kind: str
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    values: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OutputConfig:
    identifier: str
    name: str
    driver: str
    load: str
    pwm: bool


@dataclass(frozen=True, slots=True)
class StaticConfig:
    tick_ms: int
    supply_voltage: float
    can_command_timeout_ms: int
    can_backend: str
    can_channel: str
    can_bitrate: int
    inputs: tuple[InputConfig, ...]
    outputs: tuple[OutputConfig, ...]


def load_static_config(path: Path) -> StaticConfig:
    """Load and validate simulator settings from a TOML file."""
    try:
        with path.open("rb") as config_file:
            raw_config = tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ConfigurationError(f"Cannot load TOML configuration '{path}': {error}") from error

    simulation = _table(raw_config, "simulation")
    can = _table(raw_config, "can")
    input_data = _array_of_tables(raw_config, "inputs")
    output_data = _array_of_tables(raw_config, "outputs")

    tick_ms = _positive_int(simulation, "tick_ms", "simulation")
    supply_voltage = _number(simulation, "supply_voltage", "simulation")
    if not 6.0 <= supply_voltage <= 18.0:
        raise ConfigurationError("simulation.supply_voltage must be between 6.0 and 18.0 V")

    can_backend = _string(can, "backend", "can")
    if can_backend != "virtual":
        raise ConfigurationError("can.backend must be 'virtual'; physical CAN is out of scope")

    parsed_inputs = tuple(_parse_input(item, index) for index, item in enumerate(input_data))
    parsed_outputs = tuple(_parse_output(item, index) for index, item in enumerate(output_data))
    identifiers = [item.identifier for item in parsed_inputs]
    identifiers.extend(item.identifier for item in parsed_outputs)
    if len(identifiers) != len(set(identifiers)):
        raise ConfigurationError("Input and output identifiers must be unique")

    return StaticConfig(
        tick_ms=tick_ms,
        supply_voltage=supply_voltage,
        can_command_timeout_ms=_positive_int(can, "command_timeout_ms", "can"),
        can_backend=can_backend,
        can_channel=_string(can, "channel", "can"),
        can_bitrate=_positive_int(can, "bitrate", "can"),
        inputs=parsed_inputs,
        outputs=parsed_outputs,
    )


def _table(value: dict[str, Any], key: str) -> dict[str, Any]:
    section = value.get(key)
    if not isinstance(section, dict):
        raise ConfigurationError(f"'{key}' must be a TOML table")
    return section


def _array_of_tables(value: dict[str, Any], key: str) -> list[dict[str, Any]]:
    section = value.get(key)
    if not isinstance(section, list) or any(not isinstance(item, dict) for item in section):
        raise ConfigurationError(f"'{key}' must be an array of TOML tables")
    if not section:
        raise ConfigurationError(f"'{key}' must contain at least one entry")
    return section


def _string(value: dict[str, Any], key: str, section: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ConfigurationError(f"{section}.{key} must be a non-empty string")
    return item


def _positive_int(value: dict[str, Any], key: str, section: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
        raise ConfigurationError(f"{section}.{key} must be a positive integer")
    return item


def _number(value: dict[str, Any], key: str, section: str) -> float:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, (int, float)):
        raise ConfigurationError(f"{section}.{key} must be a finite number")
    parsed = float(item)
    if not math.isfinite(parsed):
        raise ConfigurationError(f"{section}.{key} must be a finite number")
    return parsed


def _parse_input(value: dict[str, Any], index: int) -> InputConfig:
    section = f"inputs[{index}]"
    identifier = _string(value, "id", section)
    name = _string(value, "name", section)
    kind = _string(value, "kind", section)
    if kind not in {"switch", "enumerated", "analog"}:
        raise ConfigurationError(f"{section}.kind must be switch, enumerated, or analog")

    unit = value.get("unit")
    if unit is not None and (not isinstance(unit, str) or not unit.strip()):
        raise ConfigurationError(f"{section}.unit must be a non-empty string when provided")

    minimum: float | None = None
    maximum: float | None = None
    values: tuple[str, ...] = ()
    if kind == "analog":
        minimum = _number(value, "minimum", section)
        maximum = _number(value, "maximum", section)
        if minimum >= maximum:
            raise ConfigurationError(f"{section}.minimum must be less than maximum")
        if unit is None:
            raise ConfigurationError(f"{section}.unit is required for analog inputs")
    else:
        raw_values = value.get("values")
        if (
            not isinstance(raw_values, list)
            or len(raw_values) < 2
            or any(not isinstance(item, str) or not item.strip() for item in raw_values)
            or len(raw_values) != len(set(raw_values))
        ):
            raise ConfigurationError(f"{section}.values must contain at least two unique strings")
        values = tuple(raw_values)

    return InputConfig(identifier, name, kind, unit, minimum, maximum, values)


def _parse_output(value: dict[str, Any], index: int) -> OutputConfig:
    section = f"outputs[{index}]"
    driver = _string(value, "driver", section)
    if driver not in {"HSD", "LSD"}:
        raise ConfigurationError(f"{section}.driver must be HSD or LSD")
    pwm = value.get("pwm")
    if not isinstance(pwm, bool):
        raise ConfigurationError(f"{section}.pwm must be a boolean")
    return OutputConfig(
        identifier=_string(value, "id", section),
        name=_string(value, "name", section),
        driver=driver,
        load=_string(value, "load", section),
        pwm=pwm,
    )
