from pathlib import Path

import pytest

from bcm_simulator.config import ConfigurationError, load_static_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_CONFIG = PROJECT_ROOT / "configs" / "demo.toml"


def test_load_demo_config() -> None:
    config = load_static_config(DEMO_CONFIG)

    assert config.can_backend == "virtual"
    assert config.tick_ms == 20
    assert config.supply_voltage == 13.5
    assert len(config.inputs) == 9
    assert len(config.outputs) == 4
    assert config.inputs[6].minimum == 0.0
    assert config.inputs[6].maximum == 100.0
    assert config.outputs[0].driver == "HSD"
    assert config.outputs[3].driver == "LSD"


def test_rejects_physical_can_backend(tmp_path: Path) -> None:
    config_text = DEMO_CONFIG.read_text(encoding="utf-8").replace(
        'backend = "virtual"', 'backend = "socketcan"'
    )
    config_path = tmp_path / "physical.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises(ConfigurationError, match="must be 'virtual'"):
        load_static_config(config_path)


def test_rejects_invalid_analog_range(tmp_path: Path) -> None:
    config_text = DEMO_CONFIG.read_text(encoding="utf-8").replace(
        "maximum = 100.0", "maximum = 0.0", 1
    )
    config_path = tmp_path / "invalid_range.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises(ConfigurationError, match="minimum must be less than maximum"):
        load_static_config(config_path)


def test_rejects_duplicate_input_output_identifier(tmp_path: Path) -> None:
    config_text = DEMO_CONFIG.read_text(encoding="utf-8").replace('id = "DP-10"', 'id = "DP-01"')
    config_path = tmp_path / "duplicate_id.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises(ConfigurationError, match="identifiers must be unique"):
        load_static_config(config_path)


def test_rejects_non_positive_simulation_tick(tmp_path: Path) -> None:
    config_text = DEMO_CONFIG.read_text(encoding="utf-8").replace("tick_ms = 20", "tick_ms = 0")
    config_path = tmp_path / "invalid_tick.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises(ConfigurationError, match="simulation.tick_ms must be a positive integer"):
        load_static_config(config_path)


def test_rejects_non_finite_supply_voltage(tmp_path: Path) -> None:
    config_text = DEMO_CONFIG.read_text(encoding="utf-8").replace(
        "supply_voltage = 13.5", "supply_voltage = nan"
    )
    config_path = tmp_path / "invalid_voltage.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises(
        ConfigurationError, match="simulation.supply_voltage must be a finite number"
    ):
        load_static_config(config_path)


def test_rejects_invalid_output_driver(tmp_path: Path) -> None:
    config_text = DEMO_CONFIG.read_text(encoding="utf-8").replace(
        'driver = "HSD"', 'driver = "relay"', 1
    )
    config_path = tmp_path / "invalid_driver.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises(ConfigurationError, match=r"outputs\[0\].driver must be HSD or LSD"):
        load_static_config(config_path)


def test_rejects_analog_input_without_unit(tmp_path: Path) -> None:
    config_text = DEMO_CONFIG.read_text(encoding="utf-8").replace(
        'kind = "analog"\nunit = "%"\n', 'kind = "analog"\n', 1
    )
    config_path = tmp_path / "missing_unit.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises(ConfigurationError, match=r"inputs\[6\].unit is required for analog inputs"):
        load_static_config(config_path)
