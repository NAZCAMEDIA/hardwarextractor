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
from pathlib import Path

# Debug logging
_DEBUG_LOG = Path.home() / "Library" / "Logs" / "HardwareXtractor_debug.log"

def _log(msg: str) -> None:
    try:
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_DEBUG_LOG, "a") as f:
            f.write(f"{msg}\n")
            f.flush()
    except:
        pass

_log("[MAIN] Module loaded")


def main() -> None:
    """Main entry point with CLI/GUI dispatch."""
    _log(f"[MAIN] main() called, argv={sys.argv}")
    # Check for CLI mode
    if "--cli" in sys.argv or "-c" in sys.argv:
        _log("[MAIN] CLI mode")
        run_cli()
    else:
        _log("[MAIN] GUI mode")
        run_gui()


def run_gui() -> None:
    """Launch the Tkinter GUI.

    For PyInstaller bundles, launches directly without splash to avoid
    issues with multiple Tk instances. For development, uses splash screen.
    """
    _log("[MAIN] run_gui() called")

    from hardwarextractor.ui.splash import SingleInstance, show_already_running_dialog

    # Check for existing instance
    _log("[MAIN] Checking single instance...")
    instance = SingleInstance()
    if not instance.acquire():
        _log("[MAIN] Another instance running, showing dialog")
        show_already_running_dialog()
        return
    _log("[MAIN] Single instance acquired")

    try:
        # Check if running as PyInstaller bundle
        is_frozen = getattr(sys, 'frozen', False)
        _log(f"[MAIN] frozen={is_frozen}")

        if is_frozen:
            # Direct launch for PyInstaller (avoid multiple Tk instances)
            _log("[MAIN] PyInstaller mode - direct launch")
            from hardwarextractor.ui.app import HardwareXtractorApp
            _log("[MAIN] HardwareXtractorApp imported")
            app = HardwareXtractorApp()
            _log("[MAIN] App created, starting mainloop")
            app.mainloop()
            _log("[MAIN] mainloop ended")
        else:
            # Development mode with splash screen
            _log("[MAIN] Dev mode - using splash")
            from hardwarextractor.ui.splash import SplashScreen
            splash = SplashScreen()

            def do_imports():
                _log("[MAIN] do_imports() called in thread")
                from hardwarextractor.ui.app import HardwareXtractorApp
                _log("[MAIN] HardwareXtractorApp imported")
                return HardwareXtractorApp

            splash.run_with_loading(do_imports)
            _log("[MAIN] run_with_loading() returned")

    except Exception as e:
        _log(f"[MAIN] Exception in run_gui: {e}")
        import traceback
        _log(traceback.format_exc())
        raise
    finally:
        _log("[MAIN] Releasing instance lock")
        instance.release()


def run_cli() -> None:
    """Launch the interactive CLI."""
    from hardwarextractor.cli.interactive import InteractiveCLI

    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()
