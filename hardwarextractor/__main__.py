"""Entry point for HardwareXtractor.

Supports two modes:
- GUI mode (default): Launches the Tkinter UI
- CLI mode (--cli): Launches the interactive CLI
"""

from __future__ import annotations

import sys


def main() -> None:
    """Main entry point with CLI/GUI dispatch."""
    # Check for CLI mode
    if "--cli" in sys.argv or "-c" in sys.argv:
        run_cli()
    else:
        run_gui()


def run_gui() -> None:
    """Launch the Tkinter GUI."""
    from hardwarextractor.ui.app import HardwareXtractorApp

    app = HardwareXtractorApp()
    app.mainloop()


def run_cli() -> None:
    """Launch the interactive CLI."""
    from hardwarextractor.cli.interactive import InteractiveCLI

    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()
