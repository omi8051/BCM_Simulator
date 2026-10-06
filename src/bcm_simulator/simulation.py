"""Small deterministic offline simulation core for the starter GUI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SimulationState(StrEnum):
    STOPPED = "Stopped"
    RUNNING = "Running"


@dataclass(frozen=True, slots=True)
class OutputState:
    identifier: str
    driver: str
    load: str
    requested: str
    effective: str
    source: str


@dataclass(frozen=True, slots=True)
class VehicleState:
    simulation_state: SimulationState
    door_open: bool
    interior_light_level: int
    left_indicator: bool
    right_indicator: bool
    wiper_mode: str
    wiper_active: bool
    motor_running: bool
    outputs: tuple[OutputState, ...]


class Simulator:
    """Evaluate the starter demo mappings and output inhibits without Qt or CAN."""

    def __init__(self) -> None:
        self.state = SimulationState.STOPPED
        self.all_outputs_off = False
        self.door_open = False
        self.light_switch_on = False
        self.motor_enabled = False
        self.wiper_mode = "OFF"
        self.dimmer_percent = 0
        self._dimmer_rule_active = False
        self.left_indicator = False
        self.right_indicator = False

    def start(self) -> None:
        self.state = SimulationState.RUNNING

    def stop(self) -> None:
        self.state = SimulationState.STOPPED

    def set_dimmer(self, value: int) -> None:
        if not 0 <= value <= 100:
            raise ValueError("Dimmer value must be between 0 and 100 percent")
        self.dimmer_percent = value

    def set_wiper_mode(self, value: str) -> None:
        if value not in {"OFF", "INT", "LOW", "HIGH"}:
            raise ValueError(f"Unsupported wiper mode: {value}")
        self.wiper_mode = value

    def outputs(self, now_ms: int) -> tuple[OutputState, ...]:
        if self.dimmer_percent >= 5:
            self._dimmer_rule_active = True
        elif self.dimmer_percent <= 3:
            self._dimmer_rule_active = False

        if self._dimmer_rule_active:
            lamp_request = f"PWM {self.dimmer_percent}%"
            lamp_source = "R3 AIN_DIMMER"
        elif self.light_switch_on:
            lamp_request = "ON"
            lamp_source = "R2 IN_LIGHT_SW"
        elif self.door_open:
            lamp_request = "ON"
            lamp_source = "R1 IN_DOOR"
        else:
            lamp_request = "OFF"
            lamp_source = "R1 IN_DOOR"

        intermittent_on = self.wiper_mode == "INT" and now_ms % 3000 < 1000
        low_requested = self.wiper_mode == "LOW" or intermittent_on
        high_requested = self.wiper_mode == "HIGH"
        motor_request = "ON" if self.motor_enabled else "OFF"
        requests = (
            ("OUT_LAMP", "HSD", "interior_lamp", lamp_request, lamp_source),
            (
                "OUT_WIPER_LOW",
                "HSD",
                "wiper_low",
                "ON" if low_requested else "OFF",
                f"R5 IN_WIPER_MODE={self.wiper_mode}",
            ),
            (
                "OUT_WIPER_HIGH",
                "HSD",
                "wiper_high",
                "ON" if high_requested else "OFF",
                f"R5 IN_WIPER_MODE={self.wiper_mode}",
            ),
            (
                "OUT_MOTOR",
                "LSD",
                "motor",
                motor_request,
                "R4 IN_MOTOR_EN" if self.motor_enabled else "R4 IN_MOTOR_EN",
            ),
        )

        inhibited = self.state is SimulationState.STOPPED or self.all_outputs_off
        return tuple(
            OutputState(
                identifier=identifier,
                driver=driver,
                load=load,
                requested=requested,
                effective="OFF" if inhibited else requested,
                source=source,
            )
            for identifier, driver, load, requested, source in requests
        )

    def vehicle_state(self, now_ms: int) -> VehicleState:
        output_states = self.outputs(now_ms)
        lamp_level = self._lamp_level(output_states[0].effective)
        return VehicleState(
            simulation_state=self.state,
            door_open=self.door_open,
            interior_light_level=lamp_level,
            left_indicator=self.left_indicator,
            right_indicator=self.right_indicator,
            wiper_mode=self.wiper_mode,
            wiper_active=any(output.effective == "ON" for output in output_states[1:3]),
            motor_running=output_states[3].effective == "ON",
            outputs=output_states,
        )

    @staticmethod
    def _lamp_level(effective_state: str) -> int:
        if effective_state == "ON":
            return 100
        if effective_state.startswith("PWM ") and effective_state.endswith("%"):
            return int(effective_state[4:-1])
        return 0
