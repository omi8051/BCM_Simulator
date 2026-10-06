# BCM Simulator Unit Test Report

## Repository State

- Framework: pytest and pytest-qt, configured in [pyproject.toml](pyproject.toml); Python source is under `src/bcm_simulator`.
- Unit tests: [test_config.py](tests/unit/test_config.py) and [test_simulation.py](tests/unit/test_simulation.py).
- GUI tests: [test_load_visualization.py](tests/gui/test_load_visualization.py).
- The requirements baseline is [BCM_Simu_requirement.md](doc/BCM_Simu_requirement.md). The implementation plan is [BCM_Simu_plan.md](doc/BCM_Simu_plan.md), but its “implementation has not started” status is stale: configuration, a small simulation core, and a starter GUI are present.
- No integration-test directory, CAN transport/protocol, configurable JSON mapping layer, fault subsystem, or persistent pytest/JUnit report destination is configured. Test results currently print in the terminal; `.pytest_cache` is pytest cache data, not a test log.
- Current production behavior is a starter slice, not the full requirements baseline. Tests below assert only behavior present in the code.

## Coverage Map

| Test cases / location | Level | Requirements | Status |
| --- | --- | --- | --- |
| Demo TOML loads with expected profile, virtual backend, HSD/LSD outputs; rejects physical backend, invalid analog range, duplicate identifiers, nonpositive tick, non-finite voltage, invalid driver, and missing analog unit. `tests/unit/test_config.py` | Unit | FR-02, FR-03, FR-06 (partial), CAN-01, NFR-05 | Pass |
| Stopped requests remain visible while effective outputs are OFF; Running enables local rules; All Outputs OFF latches and releases independently; higher-priority light-switch rule wins over door rule. `tests/unit/test_simulation.py` | Unit | FR-04 (partial), FR-13, FR-16, FR-17 (partial) | Pass |
| Dimmer hysteresis and fall-through to the demo light-switch/door logic; dimmer bounds and invalid wiper mode are rejected. `tests/unit/test_simulation.py` | Unit | FR-02, FR-05 (partial), FR-17 (partial) | Pass |
| Wiper modes do not request both speeds; intermittent mode repeats on the demo cycle. `tests/unit/test_simulation.py` | Unit | FR-10 (partial) | Pass |
| Motor-enable controls the configured LSD output and Stopped inhibits its effective output. `tests/unit/test_simulation.py` | Unit | FR-03, FR-11 (partial), FR-16 | Pass |
| Truck visualization follows effective lamp/wiper/motor state plus door and indicator inputs; command events are logged; door, windshield wiper, and tire motion change rendered pixels in their own image regions; log clearing and Reset synchronize GUI/state; Start is accessible while stopped outputs are clearly marked inhibited. `tests/gui/test_load_visualization.py` | GUI | FR-08 (partial), FR-13, FR-16 (partial), AT-05 (partial) | Pass |
| JSON mapping schema/round-trip and atomic failure behavior; input debounce, invalid/stale fallback, full sensor scaling and mapping conflict validation. | Unit | FR-04 to FR-07, AT-03, AT-04 | Planned / not executable: mapping implementation is absent. |
| Fault injection, protection, latching, guarded clear, and recovery. | Unit | FR-12, AT-08 | Planned / not executable: fault implementation is absent. |
| Lamp fade/interruption, wiper parking/timeout and model feedback, motor speed/direction/load estimates. | Unit | FR-08 to FR-11, AT-05 | Planned / not executable: these load models are absent. |
| CAN command codec validation, watchdog expiry/fallback, feedback scheduling, bounded queues and two-client virtual transport exchange. | Unit / integration | FR-14, FR-17, CAN-01 to CAN-07, AT-06, AT-07 | Planned / not executable: no CAN protocol, DBC, or transport implementation exists. |
| Full GUI input-quality, mapping, CAN monitor/export, fault controls and shutdown/resource lifecycle. | GUI | FR-02, FR-06, FR-07, FR-12 to FR-16, NFR-03, NFR-04, AT-01, AT-04, AT-08, AT-09 | Planned / not executable: the starter GUI does not implement these workflows. |

## Execution Results

| Command | Outcome |
| --- | --- |
| `\.venv\Scripts\python.exe -m pytest tests\unit` | Pass: 19 tests. |
| `\.venv\Scripts\python.exe -m pytest` | Pass: 26 tests, including GUI tests. |
| `\.venv\Scripts\python.exe -m ruff check .` | Pass: all checks passed. |
| `\.venv\Scripts\python.exe -m ruff format --check .` | Pass: 18 files already formatted. |
| `\.venv\Scripts\python.exe -m mypy src` | Pass: no issues in 7 source files. |
| `\.venv\Scripts\python.exe -m bcm_simulator --smoke-test` | Pass: GUI initialized and exited cleanly. |

The GUI control surface still consists of local Qt inputs; no external text-command parser or active CAN receive path is implemented. The event log records state changes made through the existing GUI controls using command-style names. No known test failures remain in the executed checks.

## Gaps and Limits

- This report records tests that exist and were run; it does not claim the unimplemented acceptance tests pass. Most acceptance criteria, especially AT-04 through AT-10, remain only partially covered or not executable.
- The simulation tests use the `now_ms` argument to check current wiper scheduling deterministically, but the simulation has no injected clock, debounce, or state tick owner yet. The GUI animation test uses a short Qt wait to observe a rendered frame; it is a GUI animation check, not a domain timing test.
- The animated truck is a schematic side elevation, not a photorealistic or dimensionally accurate vehicle model. The animation speed control affects visual motion only; it does not scale simulation timing.
- The plan describes a `Stopping` state, lamp fade, and wiper parking policies that are not in the requirements baseline’s two-state model and are not implemented in production. They are not asserted as current behavior; reconcile the documents before implementing or testing those policy changes.
- No pytest log or JUnit XML artifact is generated by these commands. The exact results above were observed in the terminal during this run.
