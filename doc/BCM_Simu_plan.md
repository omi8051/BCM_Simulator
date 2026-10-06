# BCM Simulator PoC - Implementation Plan

Status: Planned; implementation has not started.

## 1. Baseline and Scope

Follow [copilot-instruction.md](copilot-instruction.md) for tooling and process,
and [doc/requirement.md](doc/requirement.md) for product requirements.

Build a Windows-first Python desktop simulator using PySide6, python-can, and
cantools. The main workflow is:

```text
Switch/sensor input -> Mapping rule -> Arbitration/protection -> HSD/LSD -> Simulated load
Virtual CAN command -----------------> Arbitration/protection
```

Static configuration uses TOML via tomllib. GUI-saved mappings use JSON via json,
with schema and semantic validation. Use virtual CAN within one process by default.
Physical CAN, external CAN tools, CAN FD, UDS, production firmware, and automotive
safety certification are outside the initial PoC.

Deliver small increments, running focused tests after each change. Do not treat
planned acceptance coverage as evidence that tests have passed.

## 2. Confirmed Behavior Decisions

The following user-approved decisions need to be reflected in the requirements
before their implementation:

- Normal Stop immediately stops motors and wipers, but fades the lamp to zero.
  Introduce a short Stopping state, then transition to Stopped.
- During Stopping, new requests must not energize outputs, Start is unavailable,
  and mapping edits remain disabled until fully Stopped with outputs OFF.
- Protective faults and All Outputs OFF bypass lamp fade immediately.
- Normal wiper-mode OFF while Running finishes parking, then removes drive.
  Stop, protective faults, and All Outputs OFF stop the wiper immediately.
- Park timeout removes drive and reports a diagnostic rather than leaving it ON.
- Latched faults survive Stop/Start and require removal of the injected condition
  followed by an explicit Clear.
- CAN watchdog expiry removes only CAN authority; healthy local rules remain active.
- Local GUI-held inputs do not expire merely because their values are unchanged.

## 3. Phase 1 - Baseline and Project Foundation

### Work

1. Align FR-09, FR-10, FR-13, FR-16, FR-17, NFR-02, and related acceptance tests
   with the confirmed fade, Stopping, and parking policies.
2. Clarify that the two-tick response criterion measures request/target acceptance,
   not completion of an intentional fade or parking cycle.
3. Configure a project-local Python 3.11+ environment and verify compatible packages.
4. Create src-layout packaging, an application entry point, quality-tool settings,
   and ignore rules for environments, caches, local logs, and generated artifacts.
5. Create typed configuration models, static demo TOML, JSON mappings, and their schema.
6. Validate input ranges, finite numbers, timing values, channel references,
   capabilities, source types, and conflicting priorities.
7. Save mappings atomically; a failed load or save must preserve the last valid data.
8. Package demo assets so application launch does not depend on the working directory.

### Planned Files

```text
pyproject.toml
.gitignore
src/bcm_simulator/__init__.py
src/bcm_simulator/__main__.py
src/bcm_simulator/config.py
configs/demo.toml
configs/mappings.json
configs/mappings.schema.json
tests/unit/test_config.py
```

### Exit Criteria

- Demo configuration contains DP-01 through DP-13 and rules R1 through R5.
- Mapping round trips preserve behavior; invalid configuration is rejected.
- Default configuration cannot select a physical CAN interface.
- Focused configuration tests, lint, formatting checks, and type checks pass.

Coverage: FR-01 through FR-07; foundation for AT-01 and AT-04.

## 4. Phase 2 - Deterministic Simulation Core

Depends on Phase 1.

### Work

1. Implement enums/dataclasses for input quality, rules, output requests, states,
   snapshots, driver capabilities, and faults without Qt or CAN dependencies.
2. Give simulation state one owner and use an injected monotonic clock.
3. Implement debounce, thresholds/hysteresis, sensor-to-PWM scaling, NONE
   fall-through, inactive actions, and invalid/stale fallbacks.
4. Implement Stopped, Running, Stopping, and the independent All Outputs OFF latch.
5. Implement arbitration: state/override inhibits, fault/interlock inhibits,
   fresh CAN request, highest-priority local request, otherwise OFF.
6. Distinguish requested output, effective output, active source, and inhibit reason.
7. Implement per-channel CAN leases and reject commands while Stopped/Stopping
   without refreshing their watchdog. Clear old CAN authority when starting.
8. Implement fault applicability, injection, latching, recovery, and guarded clearing.
9. Implement lamp fade, unidirectional motor speed/current estimates, and wiper modes.
10. Generate local wiper parking requests before final arbitration; never let
    a load model bypass CAN authority or protection.
11. Apply low/high interlocking after candidate resolution. Conflicting energized
    wiper channels inhibit both and produce a diagnostic.
12. Provide automatic park feedback plus stuck/missing overrides for testing.

### Planned Files

```text
src/bcm_simulator/domain/bcm.py
src/bcm_simulator/domain/inputs.py
src/bcm_simulator/domain/mappings.py
src/bcm_simulator/domain/drivers.py
src/bcm_simulator/domain/loads.py
src/bcm_simulator/domain/faults.py
tests/unit/test_inputs.py
tests/unit/test_mappings.py
tests/unit/test_arbitration.py
tests/unit/test_states.py
tests/unit/test_faults.py
tests/unit/test_loads.py
tests/unit/test_wiper.py
```

### Exit Criteria

- Switches operate HSD and LSD loads offline with bounded PWM and deterministic timing.
- Fake-clock tests cover debounce, hysteresis, priorities, lease expiry, and fallback.
- Lamp Stop fades; fault/All Outputs OFF cuts immediately.
- Wiper normal OFF parks within its limit; Stop and protection bypass parking.
- Fault latches cannot be bypassed by Clear, Start, mappings, or CAN commands.

Coverage: FR-08 through FR-14 and FR-16 through FR-18; AT-02, AT-03, AT-05,
AT-08, AT-10, and the domain portion of NFR-02.

## 5. Phase 3 - Demo CAN Protocol and Transport

Protocol design can run alongside Phase 2 once input/output identifiers are stable.
Integration depends on the tested arbitration and watchdog interfaces.

### Work

1. Define a demo DBC and message table before implementing the codec.
2. Specify standard 11-bit IDs, exact payload lengths, channel codes, signal bits,
   byte order, scaling, units, enum values, reserved values, periods, and timeout.
3. Define separate command, feedback, input-status, and heartbeat message families.
4. Verify DBC encoding against known expected bytes, not only encode/decode round trips.
5. Implement virtual transport with bounded queues and receive timestamps.
6. Keep CAN workers separate from the state owner; enqueue events rather than mutating state.
7. Reject malformed commands without changing outputs or refreshing leases.
8. Prevent stale queued commands from being replayed; expire them before application.
9. Define overflow handling, count discarded frames, and rate-limit diagnostics.
10. Coalesce replaceable periodic feedback and keep transport work nonblocking
    for the simulation owner.
11. Implement periodic/event-driven feedback and prevent feedback-to-command loops.
12. Test two virtual clients in one process with unique test channels and clean bus closure.

### Planned Files

```text
dbc/bcm_demo.dbc
doc/can_protocol.md
src/bcm_simulator/can/transport.py
src/bcm_simulator/can/protocol.py
src/bcm_simulator/can/scheduler.py
tests/unit/test_protocol.py
tests/integration/test_virtual_can.py
tests/integration/test_can_failures.py
```

### Exit Criteria

- Known commands traverse virtual CAN and produce correct output/status feedback.
- Valid OFF commands refresh leases; invalid frames do not.
- Expiry, disconnect, overload, and shutdown leave the application responsive.
- Fake-clock tests verify configured periodic status and heartbeat scheduling.

Coverage: CAN-01 through CAN-07; AT-06 and AT-07.

## 6. Phase 4 - PySide6 Desktop Interface

Depends on stable simulation command/snapshot interfaces. GUI construction may
overlap transport development, but complete integration depends on Phase 3.

### Work

1. Open directly to an offline, Stopped simulator workspace.
2. Add switch/mode controls and bounded analog inputs with units and quality status.
3. Show output type, load, requested/effective state, PWM, source, estimates, and faults.
4. Add visual lamp brightness, wiper motion/park, and motor running/speed indicators.
5. Add Start/Stop, All Outputs OFF/release, and distinct transport/state indications.
6. Add a schema-backed mapping editor with stopped-only Apply and JSON load/save.
7. Add fault injection/removal/clear controls and useful diagnostics.
8. Add a bounded CAN monitor with filtering, pause, decoded values, and log export.
9. Pause only monitor rendering; export a bounded snapshot without stopping processing.
10. Tick the state owner with monotonic time and marshal worker updates via Qt signals.
11. Stop timers/workers and close transport resources cleanly on exit.

### Planned Files

```text
src/bcm_simulator/app.py
src/bcm_simulator/gui/main_window.py
src/bcm_simulator/gui/input_panel.py
src/bcm_simulator/gui/output_panel.py
src/bcm_simulator/gui/mapping_editor.py
src/bcm_simulator/gui/can_monitor.py
src/bcm_simulator/gui/fault_panel.py
tests/gui/
```

### Exit Criteria

- Offline inputs, mappings, outputs, and visual loads work end to end.
- Invalid edits are reported without replacing valid configuration.
- Repeated connect/disconnect, pause/export, resize, and close operations are tested.
- GUI remains usable during virtual CAN traffic; controls and text do not overlap.

Coverage: FR-02, FR-08, FR-15; GUI portions of AT-01 through AT-04,
AT-08 through AT-10, NFR-03, and NFR-04.

## 7. Phase 5 - Acceptance and Handoff

Depends on all previous phases.

1. Trace AT-01 through AT-11 to automated checks or explicit manual review evidence.
2. Demonstrate switch-to-HSD/LSD operation, dimmer PWM, configuration reload,
   lamp/wiper/motor behavior, CAN feedback, watchdog fallback, and protection.
3. Demonstrate normal Stop fade versus immediate forced shutdown and wiper parking timeout.
4. Run full tests, lint, formatting, type checks, and the desktop launch smoke test.
5. Review virtual-only defaults, sanitized artifacts, dependency licensing, and resource cleanup.
6. Document installation, launch, the in-process virtual peer workflow, protocol,
   model equations, and simulation limitations.

Planned handoff files: README.md and doc/simulation_model.md.
Completion requires successful AT-01 through AT-11 verification, not physical hardware.

## 8. Verification Commands

Run commands with the configured project interpreter. These are planned commands,
not a record of successful execution.

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest tests/gui
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m bcm_simulator
```

Run the narrow test for each touched component before broader checks. Use fake
time for domain logic; bounded wall-clock waits are allowed only for worker/GUI handoff.

## 9. Implementation Decisions to Finalize

- Select verified package versions when configuring the environment; do not invent pins.
- Add jsonschema for schema enforcement if selected; declare and verify compatibility.
- Define positive queue capacities, history size, log rotation, and overflow behavior.
- Define the high-speed wiper cycle duration so LOW and HIGH have distinct behavior.
- Confirm demo DBC layouts and fault applicability before their implementation.
- Keep the initial system offline and virtual-only; do not add a hardware backend by default.