from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from hardwarextractor.app.config import AppConfig
from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.export.csv_exporter import export_ficha_csv


class HardwareXtractorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("HardwareXtractor")
        self.geometry("960x640")
        self.minsize(840, 560)
        self.configure(bg="#f7f4ef")

        self.cache = SQLiteCache("./data/cache.sqlite")
        self.config = AppConfig(enable_tier2=True)
        self.orchestrator = Orchestrator(cache=self.cache, config=self.config)

        self.input_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Listo")
        self.log_var = tk.StringVar(value="")
        self.banner_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f7f4ef")
        style.configure("TLabel", background="#f7f4ef", foreground="#2c2a29", font=("Helvetica Neue", 12))
        style.configure("Header.TLabel", font=("Helvetica Neue", 20, "bold"), foreground="#1f1d1c")
        style.configure("Sub.TLabel", font=("Helvetica Neue", 12), foreground="#6b6561")
        style.configure("TButton", font=("Helvetica Neue", 12), padding=8)
        style.configure("Primary.TButton", font=("Helvetica Neue", 12, "bold"), background="#1f6feb", foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", "#1554b0")])

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

        header = ttk.Frame(container)
        header.pack(fill=tk.X)
        ttk.Label(header, text="HardwareXtractor", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header,
            text="Completa fichas técnicas con trazabilidad y sin inventar datos.",
            style="Sub.TLabel",
        ).pack(anchor=tk.W, pady=(2, 12))

        input_card = ttk.Frame(container)
        input_card.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(input_card, text="Componente", style="Sub.TLabel").pack(anchor=tk.W)
        input_row = ttk.Frame(input_card)
        input_row.pack(fill=tk.X, pady=(6, 0))

        entry = ttk.Entry(input_row, textvariable=self.input_var, font=("Helvetica Neue", 13))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_row, text="Procesar", style="Primary.TButton", command=self._process).pack(side=tk.LEFT, padx=8)

        status_row = ttk.Frame(container)
        status_row.pack(fill=tk.X, pady=(4, 8))
        ttk.Label(status_row, textvariable=self.status_var, style="Sub.TLabel").pack(side=tk.LEFT)
        ttk.Label(status_row, textvariable=self.log_var, style="Sub.TLabel").pack(side=tk.LEFT, padx=12)

        banner = ttk.Label(container, textvariable=self.banner_var, style="Sub.TLabel", foreground="#b45309")
        banner.pack(anchor=tk.W, pady=(0, 8))

        body = ttk.Frame(container)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        ttk.Label(left, text="Ficha actual", style="Sub.TLabel").pack(anchor=tk.W)
        self.output = tk.Text(left, height=18, wrap=tk.WORD, font=("Menlo", 11))
        self.output.configure(bg="#ffffff", relief=tk.FLAT)
        self.output.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        right = ttk.Frame(body)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        ttk.Label(right, text="Candidatos", style="Sub.TLabel").pack(anchor=tk.W)
        self.candidate_list = tk.Listbox(right, height=10, font=("Helvetica Neue", 12))
        self.candidate_list.pack(fill=tk.BOTH, expand=False, pady=(6, 8))
        ttk.Button(right, text="Seleccionar", command=self._select_candidate).pack(fill=tk.X)

        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(footer, text="Exportar CSV", command=self._export).pack(side=tk.RIGHT)

    def _process(self) -> None:
        input_value = self.input_var.get()
        self.output.delete("1.0", tk.END)
        events = self.orchestrator.process_input(input_value)
        for event in events:
            self.status_var.set(event.status)
            self.log_var.set(event.log)
            if event.status.startswith("ERROR"):
                self.output.insert(tk.END, f"ERROR: {event.log}\n")
            if event.candidates:
                self.output.insert(tk.END, "Candidatos:\n")
                self.candidate_list.delete(0, tk.END)
                for idx, candidate in enumerate(event.candidates):
                    self.output.insert(tk.END, f"{idx}. {candidate.canonical}\n")
                    self.candidate_list.insert(tk.END, f"{idx}. {candidate.canonical}")
            if event.ficha_update:
                self.output.insert(tk.END, "Ficha actualizada\n")
                for field in event.ficha_update.fields_by_template:
                    self.output.insert(tk.END, f"{field.section} - {field.field}: {field.value}\n")
                self.banner_var.set("REFERENCE activa" if event.ficha_update.has_reference else "")

    def _select_candidate(self) -> None:
        if not self.orchestrator.last_candidates:
            return
        selection = self.candidate_list.curselection()
        if not selection:
            self.log_var.set("Selecciona un candidato")
            return
        index = selection[0]
        events = self.orchestrator.select_candidate(index)
        for event in events:
            self.status_var.set(event.status)
            self.log_var.set(event.log)
            if event.status.startswith("ERROR"):
                self.output.insert(tk.END, f"ERROR: {event.log}\n")
            if event.ficha_update:
                self.output.insert(tk.END, "Ficha actualizada\n")
                for field in event.ficha_update.fields_by_template:
                    self.output.insert(tk.END, f"{field.section} - {field.field}: {field.value}\n")
                self.banner_var.set("REFERENCE activa" if event.ficha_update.has_reference else "")

    def _export(self) -> None:
        if not self.orchestrator.components:
            self.log_var.set("No hay componentes para exportar")
            return
        ficha = self.orchestrator.process_input(self.input_var.get())[-1].ficha_update
        if ficha:
            export_ficha_csv(ficha, "./data/ficha.csv")
            self.log_var.set("CSV exportado a ./data/ficha.csv")


if __name__ == "__main__":
    app = HardwareXtractorApp()
    app.mainloop()
