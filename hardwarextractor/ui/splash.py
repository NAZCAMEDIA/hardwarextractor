"""Lightweight splash screen for HardwareXtractor.

This module uses only standard library to ensure instant startup.
Heavy imports are deferred to background loading.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Callable, Optional


class SplashScreen:
    """Lightweight splash screen that appears instantly while app loads."""

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
        self._loader: Optional[Callable[[], tk.Tk]] = None
        self._loaded_app: Optional[tk.Tk] = None
        self._load_error: Optional[str] = None

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

    def run_with_loading(self, loader: Callable[[], tk.Tk]) -> None:
        """Run splash with background loading.

        Args:
            loader: Function that loads and returns the main app

        Note:
            Uses after() scheduling to ensure thread-safe tkinter operations.
        """
        self.show()
        self._loader = loader
        self._loaded_app: Optional[tk.Tk] = None
        self._load_error: Optional[str] = None

        # Start loading sequence
        self.root.after(50, self._start_loading)

        # Run splash event loop
        self.root.mainloop()

    def _start_loading(self) -> None:
        """Start the background loading process."""
        self.set_progress(10, "Cargando módulos...")

        def load_in_thread() -> None:
            try:
                # Create main app (triggers heavy imports)
                self._loaded_app = self._loader()
                self._loaded_app.withdraw()  # Keep hidden
            except Exception as e:
                self._load_error = str(e)

        # Start loading thread
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

        # Check loading progress
        self.root.after(100, lambda: self._check_loading(thread))

    def _check_loading(self, thread: threading.Thread) -> None:
        """Check if loading is complete."""
        if thread.is_alive():
            # Still loading - animate progress
            current = self._progress
            if current < 70:
                self.set_progress(current + 5, "Inicializando scrapers...")
            self.root.after(100, lambda: self._check_loading(thread))
        else:
            # Loading complete
            if self._load_error:
                self.set_progress(0, f"Error: {self._load_error}")
                self.root.after(3000, self.close)
            elif self._loaded_app:
                self.set_progress(90, "Preparando interfaz...")
                self.root.after(100, lambda: self.transition_to_app(self._loaded_app))


class SingleInstance:
    """Prevents multiple instances of the application."""

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

                # Check if process exists
                os.kill(pid, 0)
                return False  # Process is running

            except (ValueError, OSError, ProcessLookupError):
                # Stale lock file, remove and try again
                try:
                    os.unlink(self.lock_file)
                    return self.acquire()
                except OSError:
                    return False

        except OSError:
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
