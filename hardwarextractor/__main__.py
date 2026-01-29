"""Entry point for HardwareXtractor.

Supports two modes:
- GUI mode (default): Launches the Tkinter UI with splash screen
- CLI mode (--cli): Launches the interactive CLI

The GUI uses a lightweight splash screen for instant feedback while
heavy modules load in the background.

IMPORTANT: Tkinter is NOT thread-safe. The splash screen only does
imports in the background thread, then creates the app in main thread.
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
    """Launch the Tkinter GUI with splash screen.

    Uses lightweight splash for instant startup while heavy modules
    (scrapy, parsel, requests, etc.) load in the background.

    The splash only does imports in background thread, then creates
    the app instance in the main thread (tkinter thread-safety).
    """
    # Import splash first (lightweight, stdlib only)
    from hardwarextractor.ui.splash import (
        SingleInstance,
        SplashScreen,
        show_already_running_dialog,
    )

    # Check for existing instance
    instance = SingleInstance()
    if not instance.acquire():
        show_already_running_dialog()
        return

    try:
        # Show splash and load app
        splash = SplashScreen()

        def do_imports():
            """Import heavy modules and return the app CLASS (not instance).

            IMPORTANT: This runs in a background thread.
            Only do imports here - NO tkinter widget creation.
            The app instance is created in the main thread by the splash.
            """
            # This import pulls in scrapy, parsel, requests, etc.
            from hardwarextractor.ui.app import HardwareXtractorApp
            return HardwareXtractorApp  # Return CLASS, not instance

        splash.run_with_loading(do_imports)

    finally:
        instance.release()


def run_cli() -> None:
    """Launch the interactive CLI."""
    from hardwarextractor.cli.interactive import InteractiveCLI

    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()
