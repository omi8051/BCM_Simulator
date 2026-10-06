# BCM Simulator Project Instructions

Before planning or changing this project, read and follow the project specification
in [copilot-instruction.md](../copilot-instruction.md) and the requirements baseline
in [doc/requirement.md](../doc/requirement.md).

That file is the source of truth for scope, architecture, CAN communication,
HSD/LSD simulation, GUI behavior, tests, safety, and sensitive-data handling.
Keep it current when requirements change.

Build a Python desktop proof of concept with PySide6, python-can, and cantools.
Use virtual CAN by default, keep domain logic independent of the GUI, and test
each small increment. Do not enable physical CAN transmission by default or
claim production automotive safety compliance.