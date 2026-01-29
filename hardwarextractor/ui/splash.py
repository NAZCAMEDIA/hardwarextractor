"""Lightweight splash screen for HardwareXtractor.

This module uses only standard library to ensure instant startup.
Heavy imports are deferred to background loading.

IMPORTANT: Tkinter is NOT thread-safe. All widget creation/manipulation
must happen in the main thread. This module only does imports in background.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Callable, Optional, Type


class SplashScreen:
    """Lightweight splash screen that appears instantly while app loads.

    Uses a two-phase loading approach to avoid tkinter threading issues:
    1. Background thread does heavy imports (no tkinter)
    2. Main thread creates widgets after imports complete
    """

    # App branding
    APP_NAME = "HardwareXtractor"
    APP_VERSION = "0.2.0"
    APP_TAGLINE = "Fichas técnicas con trazabilidad"
    COPYRIGHT = "© 2026 NAZCAMEDIA"

    # Splash dimensions
    WIDTH = 400
    HEIGHT = 280

    # Colors (matching main app theme)
    BG_COLOR = "#1f1d1c"
    TEXT_COLOR = "#f7f4ef"
    ACCENT_COLOR = "#1f6feb"
    MUTED_COLOR = "#6b6561"

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()  # Hide initially

        # Configure window
        self.root.title(self.APP_NAME)
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes("-topmost", True)  # Keep on top

        # Center on screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - self.WIDTH) // 2
        y = (screen_h - self.HEIGHT) // 2
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        # Main frame
        self.frame = tk.Frame(self.root, bg=self.BG_COLOR)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # App icon/logo placeholder (text-based for now)
        logo_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        logo_frame.pack(pady=(40, 20))

        # Icon symbol
        icon_label = tk.Label(
            logo_frame,
            text="⚙",
            font=("Helvetica Neue", 48),
            fg=self.ACCENT_COLOR,
            bg=self.BG_COLOR,
        )
        icon_label.pack()

        # App name
        name_label = tk.Label(
            self.frame,
            text=self.APP_NAME,
            font=("Helvetica Neue", 24, "bold"),
            fg=self.TEXT_COLOR,
            bg=self.BG_COLOR,
        )
        name_label.pack()

        # Tagline
        tagline_label = tk.Label(
            self.frame,
            text=self.APP_TAGLINE,
            font=("Helvetica Neue", 12),
            fg=self.MUTED_COLOR,
            bg=self.BG_COLOR,
        )
        tagline_label.pack(pady=(4, 20))

        # Status label
        self.status_var = tk.StringVar(value="Iniciando...")
        self.status_label = tk.Label(
            self.frame,
            textvariable=self.status_var,
            font=("Helvetica Neue", 10),
            fg=self.MUTED_COLOR,
            bg=self.BG_COLOR,
        )
        self.status_label.pack()

        # Progress bar frame
        progress_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        progress_frame.pack(pady=(8, 0))

        # Simple progress indicator (canvas-based for lightweight)
        self.progress_canvas = tk.Canvas(
            progress_frame,
            width=200,
            height=4,
            bg=self.MUTED_COLOR,
            highlightthickness=0,
        )
        self.progress_canvas.pack()
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 4, fill=self.ACCENT_COLOR, outline=""
        )
        self._progress = 0

        # Version and copyright
        footer_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        footer_frame.pack(side=tk.BOTTOM, pady=(0, 20))

        version_label = tk.Label(
            footer_frame,
            text=f"v{self.APP_VERSION}",
            font=("Helvetica Neue", 9),
            fg=self.MUTED_COLOR,
            bg=self.BG_COLOR,
        )
        version_label.pack()

        copyright_label = tk.Label(
            footer_frame,
            text=self.COPYRIGHT,
            font=("Helvetica Neue", 9),
            fg=self.MUTED_COLOR,
            bg=self.BG_COLOR,
        )
        copyright_label.pack()

        # State
        self._app_ready = False
        self._main_app: Optional[tk.Tk] = None
        self._app_class: Optional[Type[tk.Tk]] = None
        self._import_error: Optional[str] = None
        self._imports_done = False

    def set_progress(self, value: int, status: str = "") -> None:
        """Update progress bar and status text.

        Args:
            value: Progress percentage (0-100)
            status: Status message to display
        """
        self._progress = max(0, min(100, value))
        bar_width = int(200 * self._progress / 100)
        self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 4)

        if status:
            self.status_var.set(status)

        self.root.update_idletasks()

    def show(self) -> None:
        """Show the splash screen."""
        self.root.deiconify()
        self.root.update()

    def close(self) -> None:
        """Close the splash screen."""
        self.root.destroy()

    def transition_to_app(self, app: tk.Tk) -> None:
        """Transition from splash to main app.

        Args:
            app: The main application window
        """
        self._main_app = app
        self._app_ready = True

        # Brief pause for visual feedback
        self.set_progress(100, "¡Listo!")
        self.root.after(200, self._do_transition)

    def _do_transition(self) -> None:
        """Perform the actual transition."""
        if self._main_app:
            self.close()
            self._main_app.deiconify()

    def run_with_loading(self, import_fn: Callable[[], Type[tk.Tk]]) -> None:
        """Run splash with background import loading.

        IMPORTANT: The import_fn should ONLY do imports and return the app class,
        NOT instantiate the app. App instantiation happens in main thread.

        Args:
            import_fn: Function that imports modules and returns the app CLASS
                       (not an instance). Example:
                       def do_imports():
                           from myapp.ui.app import MyApp
                           return MyApp

        Note:
            Uses after() scheduling to ensure thread-safe tkinter operations.
            The app instance is created in the main thread after imports complete.
        """
        self.show()
        self._import_fn = import_fn
        self._app_class = None
        self._import_error = None
        self._imports_done = False

        # Start import sequence
        self.root.after(50, self._start_imports)

        # Run splash event loop
        self.root.mainloop()

    def _start_imports(self) -> None:
        """Start the background import process."""
        self.set_progress(10, "Cargando módulos...")

        def do_imports_in_thread() -> None:
            """Only do imports here - NO tkinter widget creation."""
            try:
                # Import heavy modules and get the app class
                self._app_class = self._import_fn()
            except Exception as e:
                self._import_error = str(e)
            finally:
                self._imports_done = True

        # Start import thread
        thread = threading.Thread(target=do_imports_in_thread, daemon=True)
        thread.start()

        # Check import progress
        self.root.after(100, lambda: self._check_imports(thread))

    def _check_imports(self, thread: threading.Thread) -> None:
        """Check if imports are complete."""
        if thread.is_alive():
            # Still loading - animate progress
            current = self._progress
            if current < 70:
                self.set_progress(current + 5, "Inicializando scrapers...")
            self.root.after(100, lambda: self._check_imports(thread))
        else:
            # Imports complete - now create app in main thread
            if self._import_error:
                self.set_progress(0, f"Error: {self._import_error}")
                self.root.after(3000, self.close)
            elif self._app_class:
                self.set_progress(80, "Preparando interfaz...")
                # Schedule app creation in main thread
                self.root.after(50, self._create_app_in_main_thread)

    def _create_app_in_main_thread(self) -> None:
        """Create the app instance in the main thread (thread-safe)."""
        try:
            self.set_progress(90, "Iniciando aplicación...")
            # Create app instance here - in the main thread
            app = self._app_class()
            app.withdraw()  # Keep hidden until transition
            self.transition_to_app(app)
        except Exception as e:
            self.set_progress(0, f"Error: {e}")
            self.root.after(3000, self.close)


class SingleInstance:
    """Prevents multiple instances of the application.

    Cross-platform implementation that works on macOS, Linux, and Windows.
    """

    def __init__(self, app_name: str = "hardwarextractor") -> None:
        self.app_name = app_name
        self.lock_file = Path.home() / ".cache" / f"{app_name}.lock"
        self._lock_fd: Optional[int] = None

    def acquire(self) -> bool:
        """Try to acquire single instance lock.

        Returns:
            True if lock acquired, False if another instance is running
        """
        try:
            # Ensure cache directory exists
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)

            # Try to create/open lock file exclusively
            self._lock_fd = os.open(
                str(self.lock_file),
                os.O_CREAT | os.O_EXCL | os.O_RDWR,
                0o600
            )

            # Write PID
            os.write(self._lock_fd, str(os.getpid()).encode())
            return True

        except FileExistsError:
            # Check if the other instance is still running
            try:
                with open(self.lock_file) as f:
                    pid = int(f.read().strip())

                # Check if process exists (cross-platform)
                if self._is_process_running(pid):
                    return False  # Process is running

                # Stale lock file, remove and try again
                os.unlink(self.lock_file)
                return self.acquire()

            except (ValueError, OSError):
                # Stale lock file or read error, try to remove
                try:
                    os.unlink(self.lock_file)
                    return self.acquire()
                except OSError:
                    return False

        except OSError:
            return False

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running (cross-platform).

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise
        """
        if sys.platform == "win32":
            # Windows: use ctypes to check process
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            except (AttributeError, OSError):
                # Fallback: assume not running if we can't check
                return False
        else:
            # Unix/macOS: use kill with signal 0
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False

    def release(self) -> None:
        """Release the single instance lock."""
        try:
            if self._lock_fd is not None:
                os.close(self._lock_fd)
                self._lock_fd = None

            if self.lock_file.exists():
                os.unlink(self.lock_file)
        except OSError:
            pass

    def __enter__(self) -> "SingleInstance":
        return self

    def __exit__(self, *args) -> None:
        self.release()


def show_already_running_dialog() -> None:
    """Show a dialog indicating the app is already running."""
    root = tk.Tk()
    root.withdraw()

    # Simple message using tk.messagebox equivalent
    dialog = tk.Toplevel(root)
    dialog.title("HardwareXtractor")
    dialog.geometry("300x120")
    dialog.resizable(False, False)

    # Center
    screen_w = dialog.winfo_screenwidth()
    screen_h = dialog.winfo_screenheight()
    x = (screen_w - 300) // 2
    y = (screen_h - 120) // 2
    dialog.geometry(f"300x120+{x}+{y}")

    tk.Label(
        dialog,
        text="HardwareXtractor ya está en ejecución",
        font=("Helvetica Neue", 12),
        pady=20,
    ).pack()

    tk.Button(
        dialog,
        text="Aceptar",
        command=lambda: (dialog.destroy(), root.destroy()),
        width=10,
    ).pack()

    dialog.transient(root)
    dialog.grab_set()
    root.wait_window(dialog)
