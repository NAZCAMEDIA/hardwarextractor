"""HardwareXtractor Tkinter UI application."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from hardwarextractor.app.config import AppConfig
from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.core.events import Event, EventType
from hardwarextractor.engine.ficha_manager import FichaManager
from hardwarextractor.export.factory import ExporterFactory


# Color scheme
COLORS = {
    "bg": "#f7f4ef",
    "text": "#2c2a29",
    "text_muted": "#6b6561",
    "accent": "#1f6feb",
    "accent_hover": "#1554b0",
    "warning": "#b45309",
    "success": "#16a34a",
    "error": "#dc2626",
    "card": "#ffffff",
}


class HardwareXtractorApp(tk.Tk):
    """Main application window for HardwareXtractor."""

    def __init__(self) -> None:
        super().__init__()
        self.title("HardwareXtractor")
        self.geometry("1024x720")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg"])

        # Initialize services
        self.cache = SQLiteCache("./data/cache.sqlite")
        self.config = AppConfig(enable_tier2=True)
        self.orchestrator = Orchestrator(
            cache=self.cache,
            config=self.config,
            event_callback=self._on_event,
        )
        self.ficha_manager = FichaManager()

        # UI state variables
        self.input_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Listo")
        self.progress_var = tk.IntVar(value=0)
        self.banner_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the main UI layout."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Helvetica Neue", 12))
        style.configure("Header.TLabel", font=("Helvetica Neue", 20, "bold"), foreground="#1f1d1c")
        style.configure("Sub.TLabel", font=("Helvetica Neue", 12), foreground=COLORS["text_muted"])
        style.configure("Log.TLabel", font=("Menlo", 10), foreground=COLORS["text_muted"])
        style.configure("TButton", font=("Helvetica Neue", 12), padding=8)
        style.configure("Primary.TButton", font=("Helvetica Neue", 12, "bold"))
        style.configure("TProgressbar", thickness=6)

        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

        # Header
        header = ttk.Frame(container)
        header.pack(fill=tk.X)
        ttk.Label(header, text="HardwareXtractor", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header,
            text="Completa fichas técnicas con trazabilidad y sin inventar datos.",
            style="Sub.TLabel",
        ).pack(anchor=tk.W, pady=(2, 12))

        # Input card
        input_card = ttk.Frame(container)
        input_card.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(input_card, text="Componente", style="Sub.TLabel").pack(anchor=tk.W)
        input_row = ttk.Frame(input_card)
        input_row.pack(fill=tk.X, pady=(6, 0))

        entry = ttk.Entry(input_row, textvariable=self.input_var, font=("Helvetica Neue", 13))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.bind("<Return>", lambda e: self._process())

        self.process_btn = ttk.Button(
            input_row, text="Procesar", style="Primary.TButton", command=self._process
        )
        self.process_btn.pack(side=tk.LEFT, padx=8)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            container, variable=self.progress_var, maximum=100, mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, pady=(4, 8))

        # Status row
        status_row = ttk.Frame(container)
        status_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(status_row, textvariable=self.status_var, style="Sub.TLabel").pack(side=tk.LEFT)

        # Warning banner
        banner = ttk.Label(
            container, textvariable=self.banner_var, style="Sub.TLabel", foreground=COLORS["warning"]
        )
        banner.pack(anchor=tk.W, pady=(0, 8))

        # Body (split view)
        body = ttk.Frame(container)
        body.pack(fill=tk.BOTH, expand=True)

        # Left: Output and logs
        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        ttk.Label(left, text="Ficha actual", style="Sub.TLabel").pack(anchor=tk.W)
        self.output = tk.Text(left, height=12, wrap=tk.WORD, font=("Menlo", 11))
        self.output.configure(bg=COLORS["card"], relief=tk.FLAT, state=tk.DISABLED)
        self.output.pack(fill=tk.BOTH, expand=True, pady=(6, 8))

        # Configure text tags for coloring
        self.output.tag_configure("section", font=("Menlo", 11, "bold"), foreground=COLORS["accent"])
        self.output.tag_configure("tier_official", foreground=COLORS["success"])
        self.output.tag_configure("tier_reference", foreground=COLORS["warning"])
        self.output.tag_configure("tier_calculated", foreground=COLORS["accent"])

        # Log area
        ttk.Label(left, text="Log de eventos", style="Sub.TLabel").pack(anchor=tk.W)
        log_frame = ttk.Frame(left)
        log_frame.pack(fill=tk.X, pady=(6, 0))

        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD, font=("Menlo", 10))
        self.log_text.configure(bg="#1f1d1c", fg="#a8a29e", relief=tk.FLAT, state=tk.DISABLED)
        self.log_text.pack(fill=tk.X)

        # Configure log text tags
        self.log_text.tag_configure("success", foreground="#4ade80")
        self.log_text.tag_configure("warning", foreground="#fbbf24")
        self.log_text.tag_configure("error", foreground="#f87171")
        self.log_text.tag_configure("info", foreground="#60a5fa")

        # Right: Candidates
        right = ttk.Frame(body)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        ttk.Label(right, text="Candidatos", style="Sub.TLabel").pack(anchor=tk.W)
        self.candidate_list = tk.Listbox(right, height=10, width=40, font=("Helvetica Neue", 11))
        self.candidate_list.configure(bg=COLORS["card"], relief=tk.FLAT)
        self.candidate_list.pack(fill=tk.BOTH, expand=False, pady=(6, 8))
        self.candidate_list.bind("<Double-1>", lambda e: self._select_candidate())

        ttk.Button(right, text="Seleccionar", command=self._select_candidate).pack(fill=tk.X)

        # Footer with export options
        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(footer, text="Reset", command=self._reset).pack(side=tk.LEFT)

        export_frame = ttk.Frame(footer)
        export_frame.pack(side=tk.RIGHT)

        for fmt in ["CSV", "XLSX", "MD"]:
            ttk.Button(
                export_frame,
                text=f"Exportar {fmt}",
                command=lambda f=fmt.lower(): self._export(f),
            ).pack(side=tk.LEFT, padx=(4, 0))

    def _on_event(self, event: Event) -> None:
        """Handle events from the orchestrator."""
        # Update progress
        self.progress_var.set(event.progress)
        self.status_var.set(event.message)

        # Log the event
        self._log_event(event)

        # Update UI
        self.update_idletasks()

    def _log_event(self, event: Event) -> None:
        """Add an event to the log area."""
        self.log_text.configure(state=tk.NORMAL)

        # Determine tag based on event type
        tag = "info"
        if event.type in (EventType.SOURCE_SUCCESS, EventType.COMPLETE, EventType.VALIDATED):
            tag = "success"
        elif event.type in (EventType.SOURCE_ANTIBOT, EventType.SOURCE_TIMEOUT, EventType.VALIDATION_WARNING):
            tag = "warning"
        elif event.type in (EventType.ERROR_RECOVERABLE, EventType.ERROR_FATAL, EventType.FAILED):
            tag = "error"

        self.log_text.insert(tk.END, f"[{event.type.value}] {event.message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self) -> None:
        """Clear the log area."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _update_output(self) -> None:
        """Update the ficha output display."""
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)

        if not self.ficha_manager.components:
            self.output.insert(tk.END, "Sin componentes.\n")
            self.output.configure(state=tk.DISABLED)
            return

        ficha = self.ficha_manager.get_aggregated()
        current_section = None

        for field in ficha.fields_by_template:
            if field.value is None:
                continue

            if field.section != current_section:
                current_section = field.section
                self.output.insert(tk.END, f"\n{current_section}\n", "section")
                self.output.insert(tk.END, "-" * 40 + "\n")

            # Determine tier tag
            tier_tag = ""
            tier_label = ""
            if field.source_tier:
                tier_value = field.source_tier.value
                if "OFFICIAL" in tier_value:
                    tier_tag = "tier_official"
                    tier_label = "●"
                elif "REFERENCE" in tier_value:
                    tier_tag = "tier_reference"
                    tier_label = "◐"
                elif "CALCULATED" in tier_value:
                    tier_tag = "tier_calculated"
                    tier_label = "◇"

            value_str = str(field.value)
            if field.unit:
                value_str += f" {field.unit}"

            self.output.insert(tk.END, f"  {field.field}: {value_str} ")
            if tier_label:
                self.output.insert(tk.END, tier_label, tier_tag)
            self.output.insert(tk.END, "\n")

        # Update banner
        if ficha.has_reference:
            self.banner_var.set("⚠️ Ficha contiene datos REFERENCE (no oficiales)")
        else:
            self.banner_var.set("")

        self.output.configure(state=tk.DISABLED)

    def _process(self) -> None:
        """Process the current input."""
        input_value = self.input_var.get().strip()
        if not input_value:
            return

        # Clear previous state
        self._clear_log()
        self.progress_var.set(0)
        self.candidate_list.delete(0, tk.END)

        # Process
        events = self.orchestrator.process_input(input_value)

        for event in events:
            self.status_var.set(event.status)

            if event.status == "NEEDS_USER_SELECTION" and event.candidates:
                self.candidate_list.delete(0, tk.END)
                for idx, candidate in enumerate(event.candidates):
                    brand = candidate.canonical.get("brand", "")
                    model = candidate.canonical.get("model", "")
                    self.candidate_list.insert(tk.END, f"{idx + 1}. {brand} {model}")

            if event.status == "READY_TO_ADD" and event.component_result:
                self.ficha_manager.add_component(event.component_result)
                self._update_output()

            if event.status.startswith("ERROR"):
                self._log_event(Event.error_recoverable(event.log))

    def _select_candidate(self) -> None:
        """Select a candidate from the list."""
        if not self.orchestrator.last_candidates:
            return

        selection = self.candidate_list.curselection()
        if not selection:
            messagebox.showinfo("Selección", "Selecciona un candidato de la lista")
            return

        index = selection[0]
        events = self.orchestrator.select_candidate(index)

        for event in events:
            self.status_var.set(event.status)

            if event.status == "READY_TO_ADD" and event.component_result:
                self.ficha_manager.add_component(event.component_result)
                self._update_output()

            if event.status.startswith("ERROR"):
                self._log_event(Event.error_recoverable(event.log))

    def _export(self, format: str) -> None:
        """Export the ficha to a file."""
        if not self.ficha_manager.components:
            messagebox.showwarning("Exportar", "No hay componentes para exportar")
            return

        # Ask for file path
        extensions = {"csv": ".csv", "xlsx": ".xlsx", "md": ".md"}
        filetypes = {
            "csv": [("CSV files", "*.csv")],
            "xlsx": [("Excel files", "*.xlsx")],
            "md": [("Markdown files", "*.md")],
        }

        path = filedialog.asksaveasfilename(
            defaultextension=extensions[format],
            filetypes=filetypes[format],
            initialfile=f"ficha.{format}",
        )

        if not path:
            return

        try:
            exporter = ExporterFactory.get(format)
            result = exporter.export(self.ficha_manager, path)

            if result.success:
                messagebox.showinfo(
                    "Exportar",
                    f"Ficha exportada exitosamente\n\nArchivo: {result.path}\nFilas: {result.rows}",
                )
                self._log_event(Event.ficha_exported(format, str(result.path), result.rows))
            else:
                messagebox.showerror("Error", f"Error al exportar: {result.error}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

    def _reset(self) -> None:
        """Reset the ficha and UI state."""
        self.ficha_manager.reset()
        self.orchestrator.components.clear()
        self.input_var.set("")
        self.progress_var.set(0)
        self.status_var.set("Listo")
        self.banner_var.set("")
        self.candidate_list.delete(0, tk.END)
        self._clear_log()
        self._update_output()
        self._log_event(Event.ficha_reset())


if __name__ == "__main__":
    app = HardwareXtractorApp()
    app.mainloop()
