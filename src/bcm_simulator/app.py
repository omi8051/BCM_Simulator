"""PySide6 desktop window for the offline BCM simulator starter slice."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from bcm_simulator.config import load_static_config
from bcm_simulator.simulation import Simulator
from bcm_simulator.truck_visualization import TruckVisualization


class SimulatorWindow(QMainWindow):
    """A basic interactive GUI for the implemented offline demo behavior."""

    def __init__(self) -> None:
        super().__init__()
        project_root = Path(__file__).resolve().parents[2]
        self.config = load_static_config(project_root / "configs" / "demo.toml")
        self.simulator = Simulator()
        self.setWindowTitle("Northline | Vehicle Systems Simulator")
        self.resize(1480, 980)
        self._event_limit = 150
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_outputs)
        self._timer.start(self.config.tick_ms)
        self.refresh_outputs()

    def _build_ui(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("NORTHLINE  /  VEHICLE SYSTEMS SIMULATOR")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #dce7e2;")
        self.state_label = QLabel(self.simulator.state.value)
        self.state_label.setStyleSheet("font-weight: 700; color: #e2b363;")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(QLabel("SIMULATION STATE"))
        header.addWidget(self.state_label)
        layout.addLayout(header)

        run_controls = QHBoxLayout()
        self.run_button = QPushButton("Start simulation")
        self.run_button.clicked.connect(self.toggle_running)
        self.all_off_button = QPushButton("All Outputs OFF")
        self.all_off_button.setCheckable(True)
        self.all_off_button.setStyleSheet(
            "QPushButton:checked { background: #b42318; color: white; font-weight: 600; }"
        )
        self.all_off_button.toggled.connect(self.set_all_outputs_off)
        run_controls.addWidget(self.run_button)
        run_controls.addWidget(self.all_off_button)
        run_controls.addStretch(1)
        layout.addLayout(run_controls)

        panels = QHBoxLayout()
        panels.addWidget(self._build_input_panel(), 0)
        vehicle_panel = QGroupBox("VEHICLE OVERVIEW  /  SIDE ELEVATION")
        vehicle_layout = QVBoxLayout(vehicle_panel)
        self.load_visuals = TruckVisualization()
        vehicle_layout.addWidget(self.load_visuals, 1)
        self.vehicle_summary = QLabel(
            "Door closed  |  Cabin light off  |  Wiper parked  |  Motor stopped"
        )
        self.vehicle_summary.setWordWrap(True)
        vehicle_layout.addWidget(self.vehicle_summary)
        panels.addWidget(vehicle_panel, 1)
        layout.addLayout(panels, 1)

        lower_panels = QHBoxLayout()
        lower_panels.addWidget(self._build_output_panel(), 2)
        lower_panels.addWidget(self._build_event_panel(), 1)
        layout.addLayout(lower_panels)

        controls = QHBoxLayout()
        reset_button = QPushButton("Reset vehicle")
        reset_button.clicked.connect(self.reset_vehicle)
        controls.addWidget(reset_button)
        self.animation_toggle = QCheckBox("Animation")
        self.animation_toggle.setChecked(True)
        self.animation_toggle.toggled.connect(self.set_animation_enabled)
        controls.addWidget(self.animation_toggle)
        controls.addWidget(QLabel("Animation speed"))
        self.animation_speed = QSlider(Qt.Orientation.Horizontal)
        self.animation_speed.setRange(25, 200)
        self.animation_speed.setValue(100)
        self.animation_speed.setMaximumWidth(150)
        self.animation_speed.valueChanged.connect(self.set_animation_speed)
        controls.addWidget(self.animation_speed)
        self.animation_speed_label = QLabel("1.00x")
        controls.addWidget(self.animation_speed_label)
        controls.addStretch(1)
        clear_log_button = QPushButton("Clear event log")
        clear_log_button.clicked.connect(self.clear_event_log)
        controls.addWidget(clear_log_button)
        self.status_label = QLabel("LOCAL INPUTS  |  VIRTUAL CAN DISCONNECTED")
        controls.addWidget(self.status_label)
        layout.addLayout(controls)

        content.setStyleSheet(
            "QWidget { background: #182326; color: #dce7e2; }"
            "QGroupBox { border: 1px solid #40524e; border-radius: 4px;"
            " margin-top: 10px; padding: 10px 8px 8px; font-weight: 700; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"
            "QTableWidget, QListWidget { background: #202d30; gridline-color: #3b4b49;"
            " border: 1px solid #40524e; }"
            "QHeaderView::section { background: #2d3c3e; color: #dce7e2;"
            " padding: 6px; border: 0; }"
            "QPushButton { min-height: 32px; padding: 0 12px; background: #334542;"
            " border: 1px solid #566b64; border-radius: 3px; }"
            "QPushButton:hover { background: #405650; }"
            "QPushButton:checked { background: #813f33; border-color: #bd7056; }"
            "QCheckBox, QLabel { background: transparent; }"
        )
        self.setCentralWidget(content)

    def _build_input_panel(self) -> QGroupBox:
        panel = QGroupBox("Inputs")
        panel.setMinimumWidth(300)
        form = QFormLayout(panel)

        self.door_input = QCheckBox("Open")
        self.door_input.toggled.connect(self._set_door)
        form.addRow("Door", self.door_input)

        self.light_input = QCheckBox("On")
        self.light_input.toggled.connect(self._set_light)
        form.addRow("Interior light switch", self.light_input)

        self.ignition_status = QLabel("OFF (status only)")
        form.addRow("Ignition", self.ignition_status)

        self.motor_input = QCheckBox("Enable")
        self.motor_input.toggled.connect(self._set_motor)
        form.addRow("Motor enable", self.motor_input)

        self.left_indicator_input = QCheckBox("Left")
        self.left_indicator_input.toggled.connect(self._set_left_indicator)
        form.addRow("Left indicator", self.left_indicator_input)

        self.right_indicator_input = QCheckBox("Right")
        self.right_indicator_input.toggled.connect(self._set_right_indicator)
        form.addRow("Right indicator", self.right_indicator_input)

        self.wiper_input = QComboBox()
        self.wiper_input.addItems(["OFF", "INT", "LOW", "HIGH"])
        self.wiper_input.currentTextChanged.connect(self._set_wiper_mode)
        form.addRow("Wiper mode", self.wiper_input)

        dimmer_layout = QHBoxLayout()
        self.dimmer_input = QSlider(Qt.Orientation.Horizontal)
        self.dimmer_input.setRange(0, 100)
        self.dimmer_input.valueChanged.connect(self._set_dimmer)
        self.dimmer_value = QLabel("0 %")
        self.dimmer_value.setMinimumWidth(48)
        dimmer_layout.addWidget(self.dimmer_input, 1)
        dimmer_layout.addWidget(self.dimmer_value)
        form.addRow("Dimmer", dimmer_layout)

        can_status = QLabel("Virtual backend configured\nTransport disconnected")
        can_status.setWordWrap(True)
        form.addRow("CAN", can_status)
        return panel

    def _build_output_panel(self) -> QGroupBox:
        panel = QGroupBox("OUTPUT CHANNELS")
        layout = QVBoxLayout(panel)
        self.output_table = QTableWidget(4, 5)
        self.output_table.setHorizontalHeaderLabels(
            ["Channel", "Driver", "Load", "Requested", "Effective"]
        )
        self.output_table.verticalHeader().setVisible(False)
        self.output_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.output_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.output_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.output_table.setMinimumHeight(156)
        self.output_table.setMaximumHeight(190)
        layout.addWidget(self.output_table)
        self.source_label = QLabel("Active source: none")
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)
        return panel

    def _build_event_panel(self) -> QGroupBox:
        panel = QGroupBox("COMMAND / EVENT LOG")
        layout = QVBoxLayout(panel)
        self.event_log = QListWidget()
        self.event_log.setMinimumHeight(170)
        self.event_log.setMaximumHeight(220)
        layout.addWidget(self.event_log)
        return panel

    def _set_door(self, value: bool) -> None:
        self.simulator.door_open = value
        self._record_event("DOOR_OPEN" if value else "DOOR_CLOSE")

    def _set_light(self, value: bool) -> None:
        self.simulator.light_switch_on = value
        self._record_event("INTERIOR_LIGHT_ON" if value else "INTERIOR_LIGHT_OFF")

    def _set_motor(self, value: bool) -> None:
        self.simulator.motor_enabled = value
        self._record_event("MOTOR_ON" if value else "MOTOR_OFF")

    def _set_left_indicator(self, value: bool) -> None:
        self.simulator.left_indicator = value
        self._record_event("INDICATOR_LEFT_ON" if value else "INDICATOR_LEFT_OFF")

    def _set_right_indicator(self, value: bool) -> None:
        self.simulator.right_indicator = value
        self._record_event("INDICATOR_RIGHT_ON" if value else "INDICATOR_RIGHT_OFF")

    def _set_wiper_mode(self, value: str) -> None:
        self.simulator.set_wiper_mode(value)
        self._record_event(f"WIPER_{value}")

    def _set_dimmer(self, value: int) -> None:
        self.simulator.set_dimmer(value)
        self.dimmer_value.setText(f"{value} %")
        self._record_event(f"DIMMER_SET {value}%")

    def toggle_running(self) -> None:
        if self.simulator.state.value == "Running":
            self.simulator.stop()
        else:
            self.simulator.start()
        self.run_button.setText(
            "Stop simulation" if self.simulator.state.value == "Running" else "Start simulation"
        )
        self.state_label.setText(self.simulator.state.value)
        self.state_label.setStyleSheet(
            "font-weight: 700; color: #68d2a2;"
            if self.simulator.state.value == "Running"
            else "font-weight: 700; color: #e2b363;"
        )
        self._record_event(
            "SIMULATION_START" if self.simulator.state.value == "Running" else "SIMULATION_STOP"
        )
        self.refresh_outputs()

    def set_all_outputs_off(self, active: bool) -> None:
        self.simulator.all_outputs_off = active
        self._record_event("ALL_OUTPUTS_OFF" if active else "ALL_OUTPUTS_OFF_RELEASED")
        self.refresh_outputs()

    def set_animation_enabled(self, enabled: bool) -> None:
        self.load_visuals.set_animation(
            enabled=enabled,
            speed=self.animation_speed.value() / 100,
        )

    def set_animation_speed(self, value: int) -> None:
        speed = value / 100
        self.animation_speed_label.setText(f"{speed:.2f}x")
        self.load_visuals.set_animation(enabled=self.animation_toggle.isChecked(), speed=speed)

    def reset_vehicle(self) -> None:
        widgets = (
            self.door_input,
            self.light_input,
            self.motor_input,
            self.left_indicator_input,
            self.right_indicator_input,
            self.wiper_input,
            self.dimmer_input,
            self.all_off_button,
        )
        blockers = [QSignalBlocker(widget) for widget in widgets]
        self.simulator = Simulator()
        self.door_input.setChecked(False)
        self.light_input.setChecked(False)
        self.motor_input.setChecked(False)
        self.left_indicator_input.setChecked(False)
        self.right_indicator_input.setChecked(False)
        self.wiper_input.setCurrentIndex(0)
        self.dimmer_input.setValue(0)
        self.dimmer_value.setText("0 %")
        self.all_off_button.setChecked(False)
        del blockers
        self.state_label.setText(self.simulator.state.value)
        self.state_label.setStyleSheet("font-weight: 700; color: #e2b363;")
        self.run_button.setText("Start simulation")
        self._record_event("VEHICLE_RESET")
        self.refresh_outputs()

    def clear_event_log(self) -> None:
        self.event_log.clear()

    def _record_event(self, event: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.event_log.addItem(f"{timestamp}   {event}")
        while self.event_log.count() > self._event_limit:
            self.event_log.takeItem(0)
        self.event_log.scrollToBottom()

    def refresh_outputs(self) -> None:
        now_ms = time.monotonic_ns() // 1_000_000
        state = self.simulator.vehicle_state(now_ms)
        output_states = state.outputs
        for row, output in enumerate(output_states):
            values = (
                output.identifier,
                output.driver,
                output.load,
                output.requested,
                output.effective,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 4 and value != "OFF":
                    item.setForeground(Qt.GlobalColor.darkGreen)
                self.output_table.setItem(row, column, item)
        active_sources = sorted(
            {output.source for output in output_states if output.requested != "OFF"}
        )
        self.source_label.setText(
            "Active source: " + (", ".join(active_sources) if active_sources else "none")
        )
        self.load_visuals.set_vehicle_state(state)
        self.vehicle_summary.setText(
            f"Door {'open' if state.door_open else 'closed'}  |  "
            f"Cabin {'lit' if state.interior_light_level else 'dark'}"
            f" {state.interior_light_level}%  |  Wiper {state.wiper_mode}  |  "
            f"Motor {'running' if state.motor_running else 'stopped'}  |  "
            + (
                "OUTPUTS INHIBITED: start simulation"
                if state.simulation_state.value == "Stopped"
                else "OUTPUTS INHIBITED: release All Outputs OFF"
                if self.simulator.all_outputs_off
                else "OUTPUTS ACTIVE"
            )
        )
