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
        self.geometry("900x600")

        self.cache = SQLiteCache("./data/cache.sqlite")
        self.config = AppConfig(enable_tier2=True)
        self.orchestrator = Orchestrator(cache=self.cache, config=self.config)

        self.input_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.log_var = tk.StringVar(value="")
        self.banner_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        input_row = ttk.Frame(frame)
        input_row.pack(fill=tk.X)

        ttk.Label(input_row, text="Input componente:").pack(side=tk.LEFT)
        ttk.Entry(input_row, textvariable=self.input_var, width=60).pack(side=tk.LEFT, padx=8)
        ttk.Button(input_row, text="Procesar", command=self._process).pack(side=tk.LEFT)

        ttk.Label(frame, textvariable=self.status_var).pack(anchor=tk.W, pady=6)
        ttk.Label(frame, textvariable=self.log_var, foreground="#555").pack(anchor=tk.W)
        ttk.Label(frame, textvariable=self.banner_var, foreground="#b45309").pack(anchor=tk.W)

        self.output = tk.Text(frame, height=20)
        self.output.pack(fill=tk.BOTH, expand=True, pady=8)

        self.candidate_list = tk.Listbox(frame, height=5)
        self.candidate_list.pack(fill=tk.X)
        ttk.Button(frame, text="Seleccionar candidato", command=self._select_candidate).pack(anchor=tk.E)

        ttk.Button(frame, text="Exportar CSV", command=self._export).pack(anchor=tk.E)

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
