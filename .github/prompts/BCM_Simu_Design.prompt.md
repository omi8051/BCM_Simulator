---
name: BCM Simulator Design
description: Create or update editable high-level and low-level architecture diagrams for the BCM Simulator, grounded in its requirements and current implementation.
agent: agent
model: Auto (copilot)
tools: [execute, read, edit, search, web, agent, todo]
output: BCM_Simulator_Design_high_level.drawio, BCM_Simulator_Design_low_level.drawio
---

# BCM Simulator Design

Create or update both diagrams below as native, editable draw.io files:

- `BCM_Simulator_Design_high_level.drawio`
- `BCM_Simulator_Design_low_level.drawio`

## Sources and design authority

1. Read `doc/BCM_Simu_requirement.md`, `doc/BCM_Simu_plan.md`, and the current source/configuration files before drawing. Check for existing diagrams first and update them in place when present.
2. Treat the requirements document as the product-behavior baseline. Treat source code and configuration as evidence of what is currently implemented; label planned or proposed behavior as such.
3. Where the plan, requirements, and implementation disagree, do not silently choose or invent behavior. Show the relevant item as unresolved/TBD and briefly report the discrepancy after generating the diagrams.
4. Do not invent CAN identifiers, signal bit layouts, DBC details, hardware interfaces, or vehicle behavior. The demo CAN IDs and bit layouts are intentionally deferred. Show the CAN boundary, message purposes, validation, watchdog, and feedback flows at the level supported by the sources, and mark unspecified protocol details as TBD.
5. Keep the diagrams consistent with the documented PoC boundary: offline desktop simulation, virtual CAN by default, and no physical vehicle control or live vehicle-network connection.

## High-level diagram

Show the system boundary, users, major components, and the principal input-to-output paths. Include, where supported by the sources:

- Desktop GUI and user inputs/controls.
- Configuration and mapping rules.
- Simulation core, arbitration, protection/interlocks, and simulation state.
- HSD/LSD driver and simulated load models (lamp, wiper, and motor).
- Virtual CAN transport, protocol/DBC handling, commands, and feedback.
- Diagnostics, logging, and tests as supporting components.

Make ownership and external boundaries clear. Label arrows with the data or command being exchanged; distinguish local input/mapping flow from CAN command flow.

## Low-level diagram

Show the modules and interactions needed to understand runtime behavior. Include:

- Input validation/debounce and mapping evaluation, including priority and `NONE` fall-through where applicable.
- CAN receive/decode/validation and transmit/encode/feedback paths, with bounded queues and watchdog expiry where specified.
- The documented arbitration precedence: stopped/All Outputs OFF; protective faults and interlocks; unexpired CAN request; highest-priority local rule; otherwise OFF.
- Requested versus effective output state, inhibit/fault handling, and the driver-to-load feedback path.
- Relevant state ownership, timing/tick flow, and thread/worker boundaries where documented.
- The lamp fade, wiper mode/parking, and motor behavior only to the detail established by the requirements or implementation. Clearly mark configurable demo values as illustrative, not validated vehicle parameters.

Use labels on connectors to identify signals, events, requests, or feedback. Show direction and distinguish control flow from status/feedback flow. Do not imply that load models bypass arbitration or protection.

## Diagram quality

- Use clear titles, a small legend, consistent shapes and connector styles, and readable text at normal zoom.
- Group related components and keep flow direction consistent. Avoid crossing lines where practical.
- Add concise notes for assumptions, TBDs, and important limitations; link labels to requirement IDs (for example `FR-17` or `CAN-07`) when directly supported.
- Preserve a layout that is easy to edit. Do not put long prose, training procedures, or speculative design rationale in the diagrams.
- Validate that both files open as draw.io diagrams and that each diagram agrees with its cited source requirements.

After updating the files, summarize the main architecture decisions reflected and list any unresolved conflicts or TBD protocol details. Do not claim that a design review, automated validation, or implementation has occurred unless it was actually performed.