import pytest

from bcm_simulator.simulation import SimulationState, Simulator


def test_stopped_state_shows_requests_but_keeps_effective_outputs_off() -> None:
    simulator = Simulator()
    simulator.door_open = True

    lamp = simulator.outputs(now_ms=0)[0]

    assert simulator.state is SimulationState.STOPPED
    assert lamp.requested == "ON"
    assert lamp.effective == "OFF"


def test_running_uses_local_rules_and_all_outputs_off_latch() -> None:
    simulator = Simulator()
    simulator.start()
    simulator.door_open = True

    lamp = simulator.outputs(now_ms=0)[0]
    assert lamp.effective == "ON"
    assert lamp.source == "R1 IN_DOOR"

    simulator.all_outputs_off = True
    assert simulator.outputs(now_ms=0)[0].effective == "OFF"


def test_higher_priority_light_switch_rule_wins_over_door_rule() -> None:
    simulator = Simulator()
    simulator.start()
    simulator.door_open = True
    simulator.light_switch_on = True

    lamp = simulator.outputs(now_ms=0)[0]

    assert lamp.requested == "ON"
    assert lamp.effective == "ON"
    assert lamp.source == "R2 IN_LIGHT_SW"


def test_all_outputs_off_release_is_independent_of_running_state() -> None:
    simulator = Simulator()
    simulator.start()
    simulator.door_open = True
    simulator.all_outputs_off = True

    assert simulator.outputs(now_ms=0)[0].effective == "OFF"

    simulator.all_outputs_off = False
    assert simulator.state is SimulationState.RUNNING
    assert simulator.outputs(now_ms=0)[0].effective == "ON"

    simulator.stop()
    assert simulator.outputs(now_ms=0)[0].requested == "ON"
    assert simulator.outputs(now_ms=0)[0].effective == "OFF"


def test_motor_enable_drives_low_side_output_only_while_running() -> None:
    simulator = Simulator()
    simulator.start()
    simulator.motor_enabled = True

    motor = simulator.outputs(now_ms=0)[3]
    assert motor.identifier == "OUT_MOTOR"
    assert motor.driver == "LSD"
    assert motor.requested == "ON"
    assert motor.effective == "ON"

    simulator.stop()
    motor = simulator.outputs(now_ms=0)[3]
    assert motor.requested == "ON"
    assert motor.effective == "OFF"


def test_dimmer_hysteresis_and_rule_fallthrough() -> None:
    simulator = Simulator()
    simulator.start()
    simulator.light_switch_on = True
    simulator.set_dimmer(5)
    assert simulator.outputs(now_ms=0)[0].requested == "PWM 5%"

    simulator.set_dimmer(4)
    assert simulator.outputs(now_ms=0)[0].requested == "PWM 4%"

    simulator.set_dimmer(3)
    lamp = simulator.outputs(now_ms=0)[0]
    assert lamp.requested == "ON"
    assert lamp.source == "R2 IN_LIGHT_SW"


def test_wiper_modes_never_request_both_speeds() -> None:
    simulator = Simulator()
    simulator.start()

    for mode in ("OFF", "INT", "LOW", "HIGH"):
        simulator.set_wiper_mode(mode)
        low, high = simulator.outputs(now_ms=0)[1:3]
        assert not (low.requested == "ON" and high.requested == "ON")


def test_intermittent_wiper_repeats_on_configured_demo_cycle() -> None:
    simulator = Simulator()
    simulator.start()
    simulator.set_wiper_mode("INT")

    assert simulator.outputs(now_ms=0)[1].effective == "ON"
    assert simulator.outputs(now_ms=1000)[1].effective == "OFF"
    assert simulator.outputs(now_ms=3000)[1].effective == "ON"


def test_rejects_out_of_range_dimmer() -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        Simulator().set_dimmer(101)


def test_rejects_unsupported_wiper_mode() -> None:
    with pytest.raises(ValueError, match="Unsupported wiper mode"):
        Simulator().set_wiper_mode("AUTO")


def test_vehicle_state_snapshot_tracks_inputs_and_effective_outputs() -> None:
    simulator = Simulator()
    simulator.start()
    simulator.door_open = True
    simulator.motor_enabled = True
    simulator.left_indicator = True

    state = simulator.vehicle_state(now_ms=0)

    assert state.door_open is True
    assert state.left_indicator is True
    assert state.interior_light_level == 100
    assert state.motor_running is True
    assert state.outputs[3].effective == "ON"

    simulator.all_outputs_off = True
    inhibited_state = simulator.vehicle_state(now_ms=0)
    assert inhibited_state.door_open is True
    assert inhibited_state.interior_light_level == 0
    assert inhibited_state.motor_running is False
