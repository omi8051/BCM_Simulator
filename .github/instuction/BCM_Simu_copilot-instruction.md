# Python CAN Body Control Module Simulator

## Project Description

Build a desktop proof-of-concept (PoC) simulator for an automotive Body Control
Module (BCM). Use CAN communication to command simulated high-side drivers (HSD)
and low-side drivers (LSD), operate loads, and exchange sensor and switch data.
The application must work without a vehicle, physical ECU, or CAN adapter.

An HSD switches the supply side of a load. An LSD switches its ground side.
Model these as logical electrical outputs; do not claim transistor-level accuracy.
This project is a simulator, not production firmware or a vehicle-control tool.

Requirements baseline: [doc/requirement.md](doc/requirement.md) governs product
behavior; this file governs implementation tooling and process. Resolve any
conflict by updating both.

## Scope and Assumptions

- Target Windows first, keeping the simulation core portable.
- Use Python 3.11 or newer as an initial project baseline.
- Start with Classical CAN, an explicitly configured bitrate, and demo messages.
- Treat channel counts, polarity, PWM capability, timing, and load mappings as configuration.
- Do not assume an OEM CAN database, pinout, or electrical specification.
- Label invented IDs, payloads, units, and scaling as demo definitions.
- Support CAN FD only as a separately requested and tested extension.
- Keep physical CAN transmission opt-in and restricted to an isolated test bench.

## Functional Requirements

### HSD and LSD Outputs

- Configure each output with a unique name, driver type, connected load, and capabilities.
- Support ON/OFF commands and PWM duty cycle from 0 to 100 percent where enabled.
- Display requested state separately from effective state, including fault inhibition.
- Model supply voltage, estimated current, and faults using configurable load parameters.
- Inject open-load, short-to-ground, short-to-battery, overcurrent, and overtemperature faults.
- Define fault applicability and resulting behavior per driver type in configuration.
- Latch protective faults where configured; clearing must not bypass an active fault condition.
- Start outputs OFF and return to the configured safe state on shutdown or watchdog expiry.

### Loads and BCM Behavior

- Wiper: OFF, intermittent, low-speed, and high-speed modes, with simulated park feedback.
- Prevent simultaneous low-speed and high-speed wiper outputs.
- Use a configurable park timeout and report a stuck or missing park signal.
- Interior light: manual ON/OFF, door-triggered operation, dimming, and configurable fade timing.
- Motors: start/stop and speed control when supported by the configured driver arrangement.
- Offer motor direction only when an explicit reversible topology supports it.
- Enforce topology-specific interlocks; do not assume a single HSD or LSD can reverse a motor.
- Define deterministic priority between manual switches, CAN requests, watchdogs, and faults.
- Use a CAN-command watchdog: stale commands cannot leave loads running indefinitely.

### Sensors and Switches

- Simulate door switches, ignition, wiper stalk position, and wiper park feedback.
- Provide configurable analog inputs such as supply voltage, temperature, and rain level.
- Include units, valid ranges, scaling, and invalid/stale status for sensor values.
- Allow GUI input changes and publish corresponding CAN status messages.
- Support switch debouncing and sensor fault injection without requiring hardware.

### Input-to-Output Mapping

- Primary workflow: GUI switch/sensor input -> BCM mapping rule -> HSD/LSD output -> simulated load.
- Evaluate local input mappings without requiring a CAN connection; publish CAN status when connected.
- Let the user map named switches and sensors to configured HSD or LSD channels in the GUI.
- Each rule must specify its source input, condition, target channel, output action,
	enabled state, and explicit priority when multiple rules share a target.
- Support switch active/inactive conditions and sensor thresholds with hysteresis.
- Support ON/OFF actions and bounded sensor-to-PWM scaling on PWM-capable channels.
- Define the inactive action (OFF, or NONE to issue no request) and invalid/stale-input fallback explicitly for every rule.
- Apply switch debounce before evaluating rules, and evaluate rules on simulation ticks.
- Validate input/channel references, sensor units/ranges, PWM capabilities, and rule conflicts.
- Reject ambiguous equal-priority rules for the same target rather than relying on list order.
- Save and reload mappings as validated JSON (standard-library json); validate against a schema and do not execute user-entered code.
- Apply mapping edits only while simulation is stopped with outputs OFF.
- Route mapping requests and CAN commands through the same output arbitration and interlocks.
- Fault protection and All Outputs OFF must override both mappings and CAN commands.
- Apply CAN-command watchdog expiry to CAN-controlled requests, not healthy local-input rules.
- Display the active rule and source input alongside requested/effective output state.
- Include demo mappings: door switch -> HSD interior light ON/OFF, motor-enable
	switch -> LSD motor ON/OFF, and a bounded sensor value -> PWM-capable output.

### CAN Communication

- Use a transport abstraction with virtual CAN as the default implementation.
- Keep transport, signal decoding, BCM decisions, and load simulation separate.
- Define command messages, output feedback, sensor/switch status, and heartbeat messages.
- Maintain a demo DBC and human-readable message table as the protocol contract.
- Record arbitration ID, standard/extended format, DLC, cycle time, byte order,
  signal bit positions, scaling, limits, units, and command timeout where applicable.
- Validate frame ID, frame type, payload length, enum values, and signal bounds before applying commands.
- Reject malformed commands without changing output states; log a useful diagnostic.
- Publish periodic status and event-driven updates using configurable timing.
- Prevent transmitted feedback frames from being interpreted as new commands.
- Provide bounded CAN receive/transmit queues and explicit overload diagnostics.
- Handle disconnects and transport errors without freezing the GUI or crashing the simulation.
- Use a second virtual CAN client in tests to prove commands actually traverse the transport.
- Do not claim that a virtual bus models arbitration timing, wiring faults, or bus-off behavior.

## Technology Stack

- GUI: PySide6 (Qt for Python), with native widgets and Qt signals/slots.
- CAN: python-can, starting with its virtual backend for in-process simulation.
- DBC encoding and decoding: cantools.
- Static configuration: TOML read with the standard-library tomllib; validate values at load time.
- GUI-saved mappings: JSON read/written with the standard-library json; validate before applying.
- Tests: pytest and pytest-qt for GUI-specific tests.
- Formatting and linting: Ruff.
- Static typing: mypy, with typed public APIs and domain models.
- Packaging and dependencies: pyproject.toml and a project-local virtual environment.
- Logging: standard-library logging with rotating files and structured context fields.

Verify compatible package versions when implementing; do not invent version pins.
Do not introduce a web backend or database unless a concrete requirement needs one.

## Architecture and Folder Structure

Use a src layout with the following proposed structure. These are planned files,
not files that already exist.

```text
pyproject.toml
README.md
src/bcm_simulator/
	__init__.py
	__main__.py
	app.py
	config.py
	domain/
		bcm.py
		drivers.py
		loads.py
		inputs.py
		faults.py
	can/
		transport.py
		protocol.py
		scheduler.py
	gui/
		main_window.py
		output_panel.py
		input_panel.py
		can_monitor.py
		fault_panel.py
configs/
	demo.toml
	mappings.json
	mappings.schema.json
dbc/
	bcm_demo.dbc
tests/
	unit/
	integration/
	gui/
doc/
	requirement.md
	can_protocol.md
	simulation_model.md
```

- Keep domain logic independent of Qt and CAN backend implementations.
- Drive time-dependent behavior with an injectable monotonic clock and simulation ticks.
- Avoid sleeps in domain code and tests; verify timeouts by advancing a fake clock.
- Give the simulation state one owner; serialize GUI and CAN requests through that owner.
- Keep blocking CAN operations off the GUI thread and marshal UI updates through Qt signals.
- Stop timers/workers, close the CAN bus, and release resources on application exit.

## GUI Requirements

- Open directly to the simulator workspace, not a landing page.
- Show CAN connection state, simulation state, and active faults prominently.
- Provide Connect/Disconnect, Start/Stop, and a simulated All Outputs OFF command.
- Treat All Outputs OFF as a latched simulation override that requires explicit release.
- Provide an output table with HSD/LSD type, load, requested/effective state,
  duty cycle, estimated current, and active faults.
- Use toggles for digital inputs, dropdowns for modes, and bounded numeric controls for analog values.
- Provide a mapping table/editor to select input, condition, HSD/LSD channel,
  action, priority, and fallback; show validation errors before applying changes.
- Show load behavior visually: light brightness, wiper motion/park state, and motor running/speed.
- Update input values, active mappings, output states, and load indicators during simulation.
- Disable commands unsupported by the selected output or motor topology.
- Provide a CAN monitor with timestamp, direction, ID, DLC, raw bytes, and decoded signals.
- Filter and pause the monitor, and export logs without stopping CAN processing.
- Bound displayed history so long sessions do not consume unlimited memory.
- Provide fault injection, fault clearing, and an event log with clear error messages.
- Label simulated measurements and demo protocol definitions clearly.

## Unit Test Framework and Acceptance Criteria

Use pytest for domain and CAN tests and pytest-qt for GUI behavior.
The default test suite must not require a physical CAN adapter or vehicle.

- Test HSD/LSD ON/OFF, PWM bounds, invalid commands, and requested/effective state differences.
- Test driver faults, protective shutdown, fault clearing, and safe startup/shutdown.
- Test wiper mode interlocks, park behavior, and park timeout.
- Test interior-light door logic, dimming, and fade timing.
- Test motor interlocks and configured direction/speed capabilities.
- Test switch debouncing, sensor limits, invalid values, and stale status.
- Test switch-to-HSD/LSD mappings, sensor thresholds/hysteresis, sensor-to-PWM scaling,
  inactive/fallback actions, rule priority, conflict rejection, and configuration reload.
- Test local mappings with CAN disconnected and arbitration between mappings and CAN requests.
- Test that faults and All Outputs OFF override mapped requests as well as CAN commands.
- Test DBC encoding/decoding with known expected payload bytes, not only round trips.
- Test virtual CAN commands and feedback using separate clients on the same channel.
- Test command watchdog expiry, disconnects, malformed frames, and queue overload.
- Test that the GUI remains responsive during CAN traffic and shuts down workers cleanly.
- Test that All Outputs OFF overrides new CAN requests until explicitly released.

PoC acceptance: launch offline, map a switch to an HSD channel and another switch
to an LSD channel, toggle each input, and observe the matching output and load.
Map a sensor to a PWM-capable channel and verify that changing its value changes
the simulated load response. Save/reload mappings and verify the same behavior.
Then connect a virtual CAN client, verify input/output status and CAN command
arbitration, inject a fault, and verify protective shutdown.

## Linting and Coding Standards

- Use descriptive names, PEP 8 conventions, and type annotations for public APIs.
- Prefer dataclasses and enums for state, commands, driver types, and fault types.
- Keep configuration separate from code; avoid hard-coded channel mappings or CAN IDs in widgets.
- Validate external data at boundaries and catch specific exceptions.
- Add dependencies only when needed; preserve separation between domain and GUI logic.
- Run Ruff checks, Ruff formatting checks, mypy, and the relevant pytest tests after changes.
- Document installation, launch, virtual CAN usage, protocol definitions, and model limitations.
- Deliver small, working increments with focused tests; do not build the entire application in one step.

## Compliance and Safety

- Do not claim ISO 26262, AUTOSAR, or automotive cybersecurity certification.
- This PoC does not replace electrical validation, real-time ECU testing, or safety analysis.
- Simulated faults are behavioral models, not electrical protection guarantees.
- Never transmit demo messages to a live vehicle or production network by default.
- Require explicit backend/channel selection and confirmation for physical bench CAN transmission.
- Review third-party licenses and document licensing obligations before distribution.

## Handling Sensitive Information

- Do not commit credentials, access tokens, proprietary DBCs, VINs, or identifiable vehicle logs.
- Use synthetic/demo signal definitions and sanitized example captures.
- Keep local bench configuration, secrets, and generated logs outside version control.
- Redact sensitive identifiers before exporting or sharing captures.

## Implementation Order

1. Create packaging, validated demo configuration, and typed domain models.
2. Implement one HSD and one LSD load, switch/sensor mapping rules, deterministic tests,
   and safe-state behavior.
3. Add a demo DBC, virtual CAN commands, feedback, and watchdog tests.
4. Add the PySide6 GUI for outputs, sensors, switches, mapping editor, load indicators,
   and the CAN monitor.
5. Add wiper, interior-light, motor behavior, and fault injection with focused tests.
6. Document and verify the complete offline PoC workflow.
7. Add an optional isolated-bench hardware backend only after its requirements are confirmed.