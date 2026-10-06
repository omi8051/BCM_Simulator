---
name: BCM Simulator Unit Tests
description: Create or update maintainable BCM Simulator tests and document verified coverage, gaps, and execution results.
agent: agent
model: Auto (copilot)
tools: [execute, read, edit, search, web, agent, todo]
output: BCM_Simulator_Unit_Tests.md
---

# BCM Simulator Unit Tests

Use this prompt to add or update automated tests in the repository and produce `BCM_Simulator_Unit_Tests.md` as a concise coverage and execution report. Do not replace executable tests with documentation.

## Sources and scope

1. Read `doc/BCM_Simu_requirement.md`, `doc/BCM_Simu_plan.md`, applicable project instructions, and the production code/configuration before making changes. Inspect the existing test framework, naming conventions, and commands; extend the established patterns.
2. Treat the requirements as the product-behavior baseline and production code as the evidence of implemented behavior. The plan is not proof that a feature exists. Where sources disagree or a required behavior is not implemented, do not guess: document the discrepancy and write only tests whose expected behavior is established.
3. If production code is absent or a feature is still planned, do not create speculative tests or placeholder test files. Record suitable future cases as **Planned / not executable** in the report, and state what implementation is needed first.
4. Keep this task focused on tests and the report. Do not change production behavior, requirements, CAN protocol definitions, or dependencies unless that is necessary to make an existing test suite runnable; explain any such necessary change.
5. Use requirement IDs (for example, `FR-17`, `CAN-07`, `NFR-04`, and `AT-05`) when a test directly verifies them. Link to design diagrams only when those files exist and the link adds useful traceability.

## Test strategy

- **Unit tests:** Prefer small, isolated tests for configuration parsing/validation, input validation and debounce, mapping evaluation and `NONE` fall-through, arbitration precedence, state transitions, fault latching/clearing, driver behavior, and load models. Test CAN codec/protocol validation as unit tests only where those modules exist.
- **Integration tests:** Keep transport and multi-component behavior in integration tests. For CAN, use two `python-can` virtual clients in one process as required by `CAN-06`; do not describe this as cross-process or physical-bus testing.
- **GUI tests:** Keep widget, lifecycle, and Qt event-loop checks separate from domain unit tests. Use `pytest-qt` only when the project uses it.
- Use the repository's configured Python version and tools. For time-dependent domain behavior, use the injected/fake monotonic clock; do not use wall-clock sleeps. Keep tests deterministic, independent, and free of real hardware/network requirements.
- Cover meaningful boundaries, invalid inputs, failure paths, state transitions, and regression cases. Prefer clear arrange/act/assert behavior over tests coupled to private implementation details.
- Do not invent DBC IDs, payload layouts, timing values, or vehicle behavior. Use existing protocol definitions and configured values. Where a protocol detail is intentionally TBD, report it as a test blocker rather than fabricating expected bytes.
- Run the narrowest relevant test command after editing, then the repository's appropriate broader test command when practical. Report the exact commands and actual outcomes; never claim a test passed unless it was run successfully.

## Coverage report

Write or update `BCM_Simulator_Unit_Tests.md` with:

1. **Repository state:** test framework and relevant test locations found; identify missing implementation or test infrastructure.
2. **Coverage map:** test/module or case, test level (unit, integration, or GUI), linked requirement IDs, and status (`Pass`, `Fail`, `Not run`, or `Planned / not executable`).
3. **Execution results:** commands actually run and their outcomes, including failures that remain unresolved.
4. **Gaps and limits:** untested requirements, source conflicts, TBD protocol details, and any assumptions affecting validity.

Keep the report concise and consistent with the repository. Distinguish planned cases from existing tests and executed results. Do not fill in “actual result” or pass/fail fields for tests that have not run.