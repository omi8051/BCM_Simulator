"""Launch the BCM Simulator desktop application."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline BCM simulator")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="create and initialize the GUI, then exit",
    )
    arguments = parser.parse_args()

    font_directory = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if font_directory.is_dir():
        os.environ.setdefault("QT_QPA_FONTDIR", str(font_directory))

    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from bcm_simulator.app import SimulatorWindow

    application = QApplication(sys.argv[:1])
    application.setFont(QFont("Segoe UI", 10))
    window = SimulatorWindow()
    window.show()
    if arguments.smoke_test:
        QTimer.singleShot(0, application.quit)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
