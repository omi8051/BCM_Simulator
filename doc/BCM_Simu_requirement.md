# BCM Simulator PoC - Technical Requirements

Version: 0.2 | Date: 2026-10-05 | Status: Proposed PoC baseline

## 1. Purpose and Boundary

Demonstrate a Python desktop Body Control Module (BCM) simulator in which a user
changes switches or sensors, maps those inputs to high-side drivers (HSD) or
low-side drivers (LSD), and observes simulated lights, wipers, and motors.
CAN commands and feedback provide a second interface to the same simulation.

This document is the requirements baseline for product behavior.
[The project specification](../copilot-instruction.md) governs implementation
tooling and process instructions. A conflict between them shall be resolved by
updating both. All requirements are mandatory for PoC completion unless marked
Should. Demo defaults below are not OEM requirements or validated vehicle parameters.

In this document, a request is a desired output state from a CAN command or a
local mapping rule; the effective state is the result after protection and inhibits.

In scope: offline GUI operation, configurable mappings, behavioral load models,
virtual CAN, fault injection, logging, and automated tests.

Out of scope for the initial PoC: physical load control, live vehicle networks,
production ECU firmware, CAN FD, UDS diagnostics, transistor-level models,
hard real-time guarantees, automotive safety certification, external or
cross-process CAN tools, and CAN alive counters, CRC, or security. A hardware CAN
backend is a later, explicitly approved isolated-bench extension.

## 2. End-to-End Architecture

```text
GUI switches/sensors --> Debounce/validation --> Mapping rules ----+
                                                                   |
Virtual CAN client --> Transport --> DBC decode --> CAN requests --+
                                                                   |
                                                                   v
                                   Arbitration --> Protection/interlocks
                                                                   |
                                                                   v
                                            HSD/LSD --> Simulated load
                                                                   |
                                                                   v
                                                GUI feedback + CAN status
```

| Component | Responsibility |
| --- | --- |
| GUI | Input controls, mapping editor, load indicators, CAN monitor, fault controls |
| Simulation core | Own state, evaluate inputs/rules, resolve requests, advance load models |
| Driver/load models | Requested versus effective output, PWM, estimates, protection, load behavior |
| CAN adapter | Receive/transmit bounded frames, validate and encode/decode demo signals |
| Configuration | Validate static TOML and GUI-saved JSON mappings before activation |

Domain logic shall not depend on Qt or a CAN backend. One simulation owner shall
serialize state updates. Blocking CAN operations shall stay off the GUI thread.
Time-dependent rules shall use an injectable monotonic clock for deterministic tests.

## 3. Functional Requirements

| ID | Requirement |
| --- | --- |
| FR-01 | The application shall launch on Windows without an ECU, CAN adapter, or CAN connection, in the Stopped state (FR-16) with all effective outputs OFF. |
| FR-02 | The GUI shall provide the inputs in the catalog in Section 5.1: door, interior-light switch, ignition, motor-enable, wiper mode, wiper park indication, and bounded analog values. Analog values shall show units and valid/invalid/stale status. Ignition is status-only in the PoC. |
| FR-03 | Each configured output shall have a unique ID, HSD/LSD type, connected load, supported actions, and optional PWM capability. HSD switches supply; LSD switches ground. |
| FR-04 | The GUI shall map a named input to an output or load using a condition (switch state, enumerated value, or sensor threshold), an action (ON/OFF, bounded PWM scaling, or load-mode selection), an inactive action (OFF or NONE), an invalid/stale fallback (OFF or NONE), an enabled flag, and a priority. NONE issues no request, so lower-priority rules apply. |
| FR-05 | Rules shall support switch states, enumerated values such as wiper mode, per-input debounce, sensor thresholds with hysteresis, and bounded sensor-to-PWM scaling from 0 to 100 percent. |
| FR-06 | Invalid references, incompatible actions, invalid ranges, and equal-priority rules sharing a target shall be rejected before activation. Mapping edits shall apply only while stopped with outputs OFF. |
| FR-07 | Static settings shall load from TOML via tomllib. Mappings shall save/load as JSON via json, validated against a defined schema before applying. Failed loads shall not replace the last valid configuration. |
| FR-08 | Outputs shall show requested/effective state, duty cycle, active source/rule, estimated current, and faults. Indicators shall show light brightness, wiper motion/park, and motor running/speed. |
| FR-09 | Interior light behavior shall support manual-switch and door operation, dimming, and configurable fade timing. Fade is a load-model behavior applied to the effective lamp duty regardless of the requesting rule or command; a fade interrupted by a new request continues from the current level. |
| FR-10 | Wiper behavior shall support OFF, intermittent, low, and high modes, low/high interlocking, and park feedback produced by the wiper model. The GUI may override park feedback to inject stuck or missing park. Intermittent mode shall repeat a wipe cycle at a configurable interval. If park is not reached within a configurable timeout after the wiper is requested OFF, a park-timeout diagnostic shall be raised. |
| FR-11 | Motor behavior shall support start/stop and configured speed control. Direction shall be available only with an explicitly configured reversible topology and its interlocks. |
| FR-12 | Applicable driver faults shall include open-load, short-to-ground, short-to-battery, overcurrent, and overtemperature, injected from the GUI. Configuration shall define the protective response (demo default: inhibit the affected output) and whether each fault latches. Non-latching faults recover when the condition is removed. Latched faults clear only by an explicit Clear after the condition is removed; a Clear attempt while the condition persists shall be rejected and logged. The PoC does not auto-retry. |
| FR-13 | Start/Stop and a latched All Outputs OFF override shall be available. Stop, shutdown, protective faults, and the override shall inhibit outputs as configured. The override applies in any state and requires explicit release. |
| FR-14 | Local mappings shall work with CAN disconnected. CAN commands shall use the same arbitration and protection path (FR-17) and a configurable watchdog (CAN-07); expiry shall remove stale CAN requests without disabling healthy local mappings. |
| FR-15 | The GUI shall provide CAN connection controls, frame filtering/pause, log export, and fault injection/clear controls. Pausing the monitor shall not pause CAN processing. |
| FR-16 | The simulation shall have Stopped and Running states plus an independent All Outputs OFF latch. In Stopped, inputs remain editable and rules are evaluated and shown as requested state, mapping edits are permitted, and effective outputs are OFF. In Running, effective outputs follow FR-17. Releasing All Outputs OFF shall not change Stopped/Running. Latched faults persist across Stop/Start until cleared per FR-12; no state persists across application restart. |
| FR-17 | Each output shall resolve its effective state in this order: (1) Stopped or All Outputs OFF forces OFF; (2) active protective faults and topology interlocks inhibit; (3) an unexpired CAN command; (4) the highest-priority active local rule, where NONE issues no request; (5) otherwise OFF. Equal-priority conflicts are rejected per FR-06. This is the PoC policy, not a vehicle requirement. |
| FR-18 | GUI-held local inputs shall remain valid until changed or explicitly marked invalid/stale; they shall not expire like CAN commands. |

## 4. CAN Interface Requirements

| ID | Requirement |
| --- | --- |
| CAN-01 | Use python-can virtual transport by default, with Classical CAN and a configurable channel. The demo profile shall use standard 11-bit IDs. |
| CAN-02 | A demo DBC shall define output commands, output feedback, sensor/switch status, and heartbeat. A message table shall specify IDs, DLC, signals, byte order, scaling, units, limits, cycle times, and timeouts. |
| CAN-03 | Command signals shall identify the target channel, supported action, and duty cycle where applicable. Feedback shall distinguish requested/effective output and fault status. |
| CAN-04 | Unknown IDs, unexpected frame types, incorrect lengths, invalid enums, and out-of-range command values shall not modify outputs or refresh the valid-command watchdog. Rejections shall be logged. |
| CAN-05 | Publish periodic feedback and event-driven changes. Feedback shall not be interpreted as commands. Receive/transmit queues shall be bounded, with overload and disconnect diagnostics. |
| CAN-06 | Integration tests shall use two virtual clients on the same channel within one process. python-can's virtual backend is not a cross-process network and does not model arbitration timing, electrical faults, or bus-off. External or cross-process CAN tools are out of scope; a cross-process backend (for example python-can's udp_multicast, suitability to be verified) may be evaluated later behind the transport abstraction. |
| CAN-07 | A CAN command shall hold only while refreshed within its command timeout (demo 500 ms, configurable per command/channel). A valid OFF command also refreshes the timeout. Expiry shall remove the CAN request without latching, so FR-17 falls back to local rules or OFF, and a diagnostic shall be logged. |

DBC IDs and bit layouts shall be defined in the demo protocol before CAN implementation;
they are intentionally not invented here. A nominal bitrate setting is metadata for
the virtual backend and does not establish real bus timing.

## 5. Proposed Demo Profile

All values are configurable demo defaults to be confirmed during implementation.
They are not vehicle data.

### 5.1 Input Catalog

| ID | Input | Type | Range / values | Default | Use |
| --- | --- | --- | --- | --- | --- |
| DP-01 | IN_DOOR | Switch | CLOSED / OPEN | CLOSED | Rule R1 |
| DP-02 | IN_LIGHT_SW | Switch | OFF / ON | OFF | Rule R2 |
| DP-03 | IN_IGNITION | Switch | OFF / ON | OFF | Status only |
| DP-04 | IN_MOTOR_EN | Switch | OFF / ON | OFF | Rule R4 |
| DP-05 | IN_WIPER_MODE | Enumerated | OFF / INT / LOW / HIGH | OFF | Rule R5 |
| DP-06 | IN_WIPER_PARK | Switch | NOT_PARKED / PARKED | PARKED | Produced by wiper model; GUI override for fault injection |
| DP-07 | AIN_DIMMER | Analog | 0 to 100 percent | 0 | Rule R3 |
| DP-08 | AIN_TEMP | Analog | -40 to 125 degC | 25 | Status only |
| DP-09 | AIN_RAIN | Analog | 0 to 100 percent | 0 | Status only |

### 5.2 Outputs

| ID | Output | Driver | Capability |
| --- | --- | --- | --- |
| DP-10 | OUT_LAMP | HSD | ON/OFF and PWM |
| DP-11 | OUT_WIPER_LOW | HSD | ON/OFF, interlocked with OUT_WIPER_HIGH |
| DP-12 | OUT_WIPER_HIGH | HSD | ON/OFF, interlocked with OUT_WIPER_LOW |
| DP-13 | OUT_MOTOR | LSD | ON/OFF and PWM, unidirectional |

Motor speed is commanded by CAN PWM in the demo; no local rule drives it.

### 5.3 Local Mapping Rules

| Rule | Source | Condition | Target | Action | Inactive | Invalid/stale | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | IN_DOOR | OPEN | OUT_LAMP | ON | OFF | OFF | 10 |
| R2 | IN_LIGHT_SW | ON | OUT_LAMP | ON | NONE | NONE | 20 |
| R3 | AIN_DIMMER | At least 5 percent on, 3 percent or below off | OUT_LAMP | PWM equals input percent | NONE | NONE | 30 |
| R4 | IN_MOTOR_EN | ON | OUT_MOTOR | ON (100 percent) | OFF | OFF | 10 |
| R5 | IN_WIPER_MODE | Enumerated value | Wiper (OUT_WIPER_LOW, OUT_WIPER_HIGH) | Select wiper mode | OFF | OFF | 10 |

### 5.4 Timing and Model Parameters

| Parameter | Default |
| --- | --- |
| Simulation tick | 20 ms |
| Switch debounce | 40 ms |
| Periodic CAN status | 100 ms |
| CAN command timeout | 500 ms |
| Heartbeat | 1 s |
| Lamp fade time | 1.0 s |
| Wiper intermittent interval | 3.0 s |
| Wiper wipe-cycle duration | 1.0 s |
| Wiper park timeout | 2.0 s |
| Supply voltage (simulation parameter) | 13.5 V, range 6.0 to 18.0 V |

Load-current estimates and motor speed/brightness responses shall use documented
configurable models, not claims of electrical accuracy. PWM is a duty-cycle
behavior model, not a high-frequency waveform simulation.

## 6. Quality and Safety Requirements

| ID | Requirement |
| --- | --- |
| NFR-01 | Use Python 3.11+, PySide6, python-can, and cantools. Use pytest/pytest-qt, Ruff, and mypy for verification. |
| NFR-02 | With a fake clock, an accepted local input (after its debounce) shall change the effective output within two simulation ticks (40 ms at demo defaults) unless inhibited. Debounce applies per switch input, including GUI-originated, and may be configured to 0. A nominal GUI update target of 200 ms is informational (Should), not a pass criterion; there is no hard real-time guarantee. |
| NFR-03 | The GUI shall remain usable during CAN traffic and faults. Queues, displayed frame history, and log retention shall have configured bounds. |
| NFR-04 | Exit shall stop timers/workers and close CAN resources cleanly. Domain tests shall use fake time, not wall-clock sleeps. |
| NFR-05 | No physical CAN interface shall be enabled by default; the default configuration shall contain only the virtual backend. The simulated All Outputs OFF function is not a hardware emergency stop. |
| NFR-06 | Use synthetic DBCs and captures. Do not commit secrets, proprietary vehicle data, VINs, or identifiable logs. Review dependency licensing before distribution. |

## 7. Acceptance Tests

| Test | Pass condition | Coverage |
| --- | --- | --- |
| AT-01 Offline start | Launch with no adapter; state is Stopped; effective outputs OFF; input controls update and show requested state. | FR-01, FR-02, FR-14, FR-16 |
| AT-02 Switch mapping | Map switches to HSD and LSD; toggle each; verify requested/effective state and matching load within the specified timing. | FR-03 to FR-05, FR-08, NFR-02 |
| AT-03 Sensor mapping | Using rule R3, vary the dimmer through minimum, midpoint, maximum, and the 5/3 percent hysteresis band; verify bounded PWM, NONE fall-through to lower-priority rules, and invalid/stale fallback. | FR-02, FR-04, FR-05, FR-17 |
| AT-04 Configuration | Save/reload JSON with identical behavior; reject malformed data, unknown channels, incompatible PWM, and priority conflicts without replacing valid state. | FR-06, FR-07 |
| AT-05 Body functions | With fake time, verify lamp fade including interruption, all wiper modes with intermittent interval and wipe cycle, park timeout, low/high interlock, CAN-commanded motor speed, and disabled unsupported direction. | FR-09 to FR-11 |
| AT-06 CAN exchange | A second virtual client sends known command bytes; effective output changes and correctly decoded feedback/status/heartbeat are received at their configured periods (within one tick, fake clock). | CAN-01 to CAN-03, CAN-06 |
| AT-07 CAN failures | Reject malformed commands without output changes/watchdog refresh; verify command expiry falls back to local rules or OFF per CAN-07, disconnect diagnostics, and continued local operation. | FR-14, CAN-04, CAN-05, CAN-07 |
| AT-08 Protection | Inject each applicable fault; verify configured response, latching, and recovery. A Clear while the condition persists is rejected; All Outputs OFF blocks local/CAN requests until release. | FR-12, FR-13 |
| AT-09 UI lifecycle | Filtering, pausing, and exporting do not stop processing; bounded traffic does not freeze the GUI; exit leaves no running workers. | FR-15, NFR-03, NFR-04 |
| AT-10 States and arbitration | Verify Stopped/Running/All OFF transitions and, for one output, each FR-17 level: Stopped/All OFF, fault/interlock, fresh CAN command, rule priority, default OFF. Latched faults persist across Stop/Start; GUI inputs do not expire. | FR-13, FR-14, FR-16 to FR-18 |
| AT-11 Quality gates | Ruff, Ruff format check, mypy, and pytest pass without hardware; the default configuration enables only the virtual backend; no secrets or proprietary vehicle data are committed; a dependency license review is recorded. | NFR-01, NFR-05, NFR-06 |

## 8. Delivery Approach

1. Build configuration and deterministic domain models with one HSD and one LSD.
2. Add switch/sensor mapping, validation, arbitration, and protection tests.
3. Add the demo DBC and in-process virtual CAN integration tests.
4. Add GUI controls, mapping editor, output/load indicators, and CAN monitor.
5. Add body-function models and run the complete acceptance demonstration.

PoC completion requires the above acceptance tests to pass and the model limitations
to be documented. Channel mappings, protocol layouts, and timing defaults shall be
confirmed during implementation; physical-bench integration is not a completion dependency.

## 9. Review Decisions

| ID | Decision |
| --- | --- |
| DEC-01 | Arbitration precedence is fixed as FR-17 for the PoC. |
| DEC-02 | External and cross-process CAN tools are out of scope; the in-process virtual backend is used. |
| DEC-03 | This document governs product behavior, the project specification governs tooling and process, and the documentation folder is `doc/`. |
| DEC-04 | Demo parameters, hysteresis, and timings are placeholders to be confirmed during implementation. |