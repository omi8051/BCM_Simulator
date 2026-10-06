from PySide6.QtCore import QRect

from bcm_simulator.app import SimulatorWindow


def _scene_crop(window: SimulatorWindow, image, region: tuple[int, int, int, int]):
    widget = window.load_visuals
    scale = min(widget.width() / 1000, widget.height() / 500)
    origin_x = (widget.width() - 1000 * scale) / 2
    origin_y = (widget.height() - 500 * scale) / 2
    device_ratio = image.devicePixelRatio()
    x, y, width, height = region
    return image.copy(
        QRect(
            round((origin_x + x * scale) * device_ratio),
            round((origin_y + y * scale) * device_ratio),
            round(width * scale * device_ratio),
            round(height * scale * device_ratio),
        )
    )


def test_load_visuals_follow_effective_outputs(qtbot) -> None:
    window = SimulatorWindow()
    qtbot.addWidget(window)

    window.door_input.setChecked(True)
    window.motor_input.setChecked(True)
    window.left_indicator_input.setChecked(True)
    window.wiper_input.setCurrentText("LOW")
    window.run_button.click()
    window.refresh_outputs()

    assert window.load_visuals.lamp_level == 100
    assert window.load_visuals.wiper_active is True
    assert window.load_visuals.motor_running is True
    assert window.load_visuals.door_open is True
    assert window.load_visuals.left_indicator is True

    window.all_off_button.setChecked(True)
    window.refresh_outputs()

    assert window.load_visuals.lamp_level == 0
    assert window.load_visuals.wiper_active is False
    assert window.load_visuals.motor_running is False


def test_top_start_control_enables_requested_motor_and_wiper(qtbot) -> None:
    window = SimulatorWindow()
    qtbot.addWidget(window)
    window.show()

    window.motor_input.setChecked(True)
    window.wiper_input.setCurrentText("LOW")
    window.refresh_outputs()

    assert window.run_button.isVisible()
    assert window.simulator.vehicle_state(0).outputs[1].effective == "OFF"
    assert window.vehicle_summary.text().endswith("OUTPUTS INHIBITED: start simulation")

    window.run_button.click()
    window.refresh_outputs()

    assert window.load_visuals.motor_running is True
    assert window.load_visuals.wiper_active is True
    assert window.vehicle_summary.text().endswith("OUTPUTS ACTIVE")


def test_vehicle_commands_update_truck_state_and_event_log(qtbot) -> None:
    window = SimulatorWindow()
    qtbot.addWidget(window)

    window.door_input.setChecked(True)
    window.light_input.setChecked(True)
    window.right_indicator_input.setChecked(True)
    window.motor_input.setChecked(True)
    window.run_button.click()
    window.refresh_outputs()

    assert window.load_visuals.door_open is True
    assert window.load_visuals.lamp_level == 100
    assert window.load_visuals.right_indicator is True
    assert window.load_visuals.motor_running is True
    assert window.event_log.count() >= 5
    assert "DOOR_OPEN" in window.event_log.item(0).text()
    assert "MOTOR_ON" in window.event_log.item(3).text()

    window.clear_event_log()
    assert window.event_log.count() == 0


def test_door_command_animates_truck_and_reset_clears_vehicle(qtbot) -> None:
    window = SimulatorWindow()
    qtbot.addWidget(window)
    window.show()
    window.run_button.click()
    window.door_input.setChecked(True)
    window.refresh_outputs()

    initial_frame = window.load_visuals.grab().toImage()
    qtbot.wait(180)
    moving_frame = window.load_visuals.grab().toImage()

    assert initial_frame != moving_frame

    window.reset_vehicle()
    assert window.state_label.text() == "Stopped"
    assert window.run_button.text() == "Start simulation"
    assert window.door_input.isChecked() is False
    assert window.load_visuals.door_open is False
    assert "VEHICLE_RESET" in window.event_log.item(window.event_log.count() - 1).text()


def test_active_load_animation_changes_rendered_frame(qtbot) -> None:
    window = SimulatorWindow()
    qtbot.addWidget(window)
    window.simulator.start()
    window.simulator.set_wiper_mode("LOW")
    window.simulator.motor_enabled = True
    window.show()
    window.refresh_outputs()

    first_frame = window.load_visuals.grab().toImage()
    qtbot.wait(120)
    next_frame = window.load_visuals.grab().toImage()

    assert first_frame != next_frame


def test_wiper_sweep_changes_rendered_frame(qtbot) -> None:
    window = SimulatorWindow()
    qtbot.addWidget(window)
    window.simulator.start()
    window.simulator.set_wiper_mode("LOW")
    window.show()
    window.refresh_outputs()

    first_frame = _scene_crop(
        window,
        window.load_visuals.grab().toImage(),
        (740, 130, 90, 90),
    )
    qtbot.wait(140)
    next_frame = _scene_crop(
        window,
        window.load_visuals.grab().toImage(),
        (740, 130, 90, 90),
    )

    assert window.load_visuals.wiper_active is True
    assert first_frame != next_frame


def test_motor_rotation_changes_rendered_frame_without_wiper(qtbot) -> None:
    window = SimulatorWindow()
    qtbot.addWidget(window)
    window.simulator.start()
    window.simulator.motor_enabled = True
    window.show()
    window.refresh_outputs()

    first_frame = _scene_crop(
        window,
        window.load_visuals.grab().toImage(),
        (245, 305, 125, 120),
    )
    qtbot.wait(140)
    next_frame = _scene_crop(
        window,
        window.load_visuals.grab().toImage(),
        (245, 305, 125, 120),
    )

    assert window.load_visuals.motor_running is True
    assert window.load_visuals.wiper_active is False
    assert first_frame != next_frame
