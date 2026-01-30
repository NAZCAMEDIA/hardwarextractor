"""HardwareXtractor Tkinter UI application."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from typing import Optional
import webbrowser

# Debug logging for PyInstaller troubleshooting
_DEBUG_LOG = Path.home() / "Library" / "Logs" / "HardwareXtractor_debug.log"

def _debug_log(msg: str) -> None:
    """Write debug message to log file."""
    try:
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_DEBUG_LOG, "a") as f:
            f.write(f"{msg}\n")
            f.flush()
    except:
        pass

from hardwarextractor.app.config import AppConfig
from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.app.paths import cache_db_path
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.core.events import Event, EventType
from hardwarextractor.core.feedback import get_feedback_collector
from hardwarextractor.core.github_reporter import send_feedback_report
from hardwarextractor.engine.ficha_manager import FichaManager
from hardwarextractor.export.factory import ExporterFactory
from hardwarextractor.models.schemas import (
    COMPONENT_SECTIONS,
    ComponentType,
    DataOrigin,
    get_data_origin,
    SourceTier,
    SpecStatus,
)


# Version info
__version__ = "0.2.1"
__build__ = "2026.01.30"
__copyright__ = "© 2026 NAZCAMEDIA. MIT License. | pip install hardwarextractor"


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

# Mapeo de DataOrigin a indicadores visuales (tag, symbol)
ORIGIN_INDICATORS = {
    DataOrigin.OFICIAL: ("tier_official", "●"),
    DataOrigin.CATALOGO: ("tier_official", "◆"),
    DataOrigin.REFERENCIA: ("tier_reference", "◐"),
    DataOrigin.CALCULADO: ("tier_calculated", "◇"),
    DataOrigin.DESCONOCIDO: ("", ""),
}


def _to_spec_status(value) -> SpecStatus:
    """Convert value to SpecStatus enum safely."""
    if isinstance(value, SpecStatus):
        return value
    if isinstance(value, str):
        try:
            return SpecStatus(value)
        except ValueError:
            pass
    return SpecStatus.UNKNOWN


def _to_source_tier(value) -> SourceTier:
    """Convert value to SourceTier enum safely."""
    if isinstance(value, SourceTier):
        return value
    if isinstance(value, str):
        try:
            return SourceTier(value)
        except ValueError:
            pass
    return SourceTier.NONE


# Translations for extra spec fields (key -> Spanish label)
SPEC_TRANSLATIONS = {
    # GPU
    "gpu.cuda_cores": "Núcleos CUDA",
    "gpu.boost_clock_ghz": "Frecuencia Boost (GHz)",
    "gpu.base_clock_ghz": "Frecuencia Base (GHz)",
    "gpu.vram_gb": "Memoria VRAM",
    "gpu.vram_type": "Tipo de VRAM",
    "gpu.engine_specs": "Motor gráfico",
    "gpu.shader_tflops": "Shader cores",
    "gpu.rt_tflops": "Núcleos Ray Tracing",
    "gpu.tensor_tops": "Núcleos Tensor (IA)",
    "gpu.tensor_cores": "Núcleos Tensor",
    "gpu.rt_cores": "Núcleos RT",
    "gpu.mem.bus_width_bits": "Ancho bus memoria",
    "gpu.mem.speed_gbps": "Velocidad memoria",
    "gpu.mem.bandwidth_gbps": "Ancho banda memoria",
    "gpu.architecture": "Arquitectura",
    "gpu.ray_tracing": "Ray Tracing",
    "gpu.dlss": "DLSS",
    "gpu.pcie.version": "Versión PCIe",
    "gpu.pcie.lanes": "Líneas PCIe",
    "gpu.cuda_capability": "Capacidad CUDA",
    "gpu.display_outputs": "Salidas de video",
    "gpu.max_monitors": "Monitores máx.",
    "gpu.hdcp_version": "Versión HDCP",
    "gpu.length_mm": "Longitud",
    "gpu.width_mm": "Ancho",
    "gpu.slots": "Ranuras ocupadas",
    "gpu.max_temp_c": "Temp. máxima (°C)",
    "gpu.gaming_power_w": "Consumo gaming (W)",
    "gpu.tdp_w": "TDP (W)",
    "gpu.recommended_psu_w": "PSU recomendada (W)",
    "gpu.power_connectors": "Conectores energía",
    "gpu.directx_version": "Versión DirectX",
    "gpu.opengl_version": "Versión OpenGL",
    "gpu.vulkan_version": "Versión Vulkan",
    # CPU
    "cpu.base_clock_mhz": "Frecuencia base (MHz)",
    "cpu.boost_clock_mhz": "Frecuencia Boost (MHz)",
    "cpu.cores_physical": "Núcleos físicos",
    "cpu.threads_logical": "Hilos lógicos",
    "cpu.cache_l1_kb": "Caché L1",
    "cpu.cache_l2_kb": "Caché L2",
    "cpu.cache_l3_kb": "Caché L3",
    "cpu.tdp_w": "TDP (W)",
    "cpu.socket": "Zócalo",
    "cpu.architecture": "Arquitectura",
    "cpu.process_nm": "Proceso (nm)",
    "cpu.integrated_graphics": "Gráficos integrados",
    "cpu.memory_type_supported": "Tipo RAM soportada",
    "cpu.max_memory_gb": "Memoria máx. (GB)",
    "cpu.memory_channels_max": "Canales de memoria",
    "cpu.pcie.version_max": "Versión PCIe máx.",
    "cpu.pcie.lanes_max": "Líneas PCIe máx.",
    # RAM
    "ram.type": "Tipo de RAM",
    "ram.speed_effective_mt_s": "Velocidad efectiva",
    "ram.clock_real_mhz": "Frecuencia real (MHz)",
    "ram.latency_cl": "Latencia CL",
    "ram.voltage_v": "Voltaje (V)",
    "ram.capacity_gb": "Capacidad (GB)",
    "ram.form_factor": "Factor de forma",
    "ram.pins": "Número de pines",
    # Mainboard
    "mb.socket": "Zócalo",
    "mb.chipset": "Chipset",
    "mb.max_memory_gb": "Memoria máx. (GB)",
    "mb.memory_slots": "Ranuras de memoria",
    # Disk
    "disk.type": "Tipo",
    "disk.interface": "Interfaz",
    "disk.capacity_gb": "Capacidad (GB)",
    "disk.rpm": "RPM",
    "disk.cache_mb": "Búfer (MB)",
}

# Import reference links from common location
from hardwarextractor.data.reference_urls import REFERENCE_LINKS


class HardwareXtractorApp(tk.Tk):
    """Main application window for HardwareXtractor."""

    def __init__(self) -> None:
        _debug_log("[APP] __init__ starting")
        super().__init__()
        self.title("HardwareXtractor")
        self.geometry("1200x850")
        self.minsize(1000, 700)
        self.configure(bg=COLORS["bg"])
        _debug_log("[APP] Window configured")

        # Initialize services
        _debug_log("[APP] Initializing services...")
        try:
            self.cache = SQLiteCache(str(cache_db_path()))
            _debug_log("[APP] SQLiteCache OK")
        except Exception as e:
            _debug_log(f"[APP] SQLiteCache ERROR: {e}")
            raise

        self.config = AppConfig(enable_tier2=True)
        _debug_log("[APP] AppConfig OK")

        self.orchestrator = Orchestrator(
            cache=self.cache,
            config=self.config,
            event_callback=self._on_event,
        )
        _debug_log("[APP] Orchestrator OK")

        self.ficha_manager = FichaManager()
        _debug_log("[APP] FichaManager OK")

        # Feedback collector for beta
        self.feedback = get_feedback_collector()
        _debug_log("[APP] FeedbackCollector OK")

        # UI state variables
        self.input_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Listo")
        self.progress_var = tk.IntVar(value=0)
        self.banner_var = tk.StringVar(value="")
        self.beta_banner_var = tk.StringVar(value="⚠️ VERSIÓN BETA - Tu feedback nos ayuda a mejorar")
        self.expanded_view_var = tk.BooleanVar(value=False)  # Toggle ficha ampliada
        self._source_urls = {}  # Store URLs for source links
        self._last_input = ""  # Store last search input
        self._last_component_type = ""  # Store last component type
        _debug_log("[APP] UI state vars OK")

        _debug_log("[APP] Building UI...")
        self._build_ui()
        _debug_log("[APP] __init__ complete")

    def _build_ui(self) -> None:
        """Build the main UI layout."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Helvetica Neue", 12))
        style.configure("Header.TLabel", font=("Helvetica Neue", 20, "bold"), foreground="#1f1d1c", background=COLORS["bg"])
        style.configure("Sub.TLabel", font=("Helvetica Neue", 12), foreground=COLORS["text_muted"], background=COLORS["bg"])
        style.configure("Log.TLabel", font=("Menlo", 10), foreground=COLORS["text_muted"], background=COLORS["bg"])
        style.configure("TButton", font=("Helvetica Neue", 12), padding=8, foreground=COLORS["text"])
        style.configure("Primary.TButton", font=("Helvetica Neue", 12, "bold"), foreground=COLORS["text"])
        style.configure("TProgressbar", thickness=6)
        # Entry con texto oscuro
        style.configure("TEntry", foreground=COLORS["text"], fieldbackground=COLORS["card"])
        style.map("TEntry", foreground=[("focus", COLORS["text"]), ("!focus", COLORS["text"])])

        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

        # Header
        header = ttk.Frame(container)
        header.pack(fill=tk.X)
        ttk.Label(header, text="HardwareXtractor", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 6))

        # Beta banner
        beta_frame = tk.Frame(container, bg="#fef3c7", highlightbackground="#f59e0b", highlightthickness=1)
        beta_frame.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            beta_frame,
            textvariable=self.beta_banner_var,
            bg="#fef3c7",
            fg="#92400e",
            font=("Helvetica Neue", 11),
            pady=6,
            padx=10,
        ).pack(fill=tk.X)

        # Input card
        input_card = ttk.Frame(container)
        input_card.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(input_card, text="Componente", style="Sub.TLabel").pack(anchor=tk.W)
        input_row = ttk.Frame(input_card)
        input_row.pack(fill=tk.X, pady=(6, 0))

        self.entry = tk.Entry(
            input_row,
            textvariable=self.input_var,
            font=("Helvetica Neue", 13),
            bg=COLORS["card"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],  # Color del cursor
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=COLORS["accent"],
            highlightbackground="#d1d5db",
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self.entry.bind("<Return>", lambda e: self._process())
        self.entry.focus_set()  # Cursor parpadeante al iniciar

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

        # Header row with label and toggle
        ficha_header = ttk.Frame(left)
        ficha_header.pack(fill=tk.X)
        ttk.Label(ficha_header, text="Ficha actual", style="Sub.TLabel").pack(side=tk.LEFT)
        ttk.Checkbutton(
            ficha_header,
            text="Ampliada",
            variable=self.expanded_view_var,
            command=self._update_output,
        ).pack(side=tk.RIGHT, padx=(10, 0))
        self.output = tk.Text(left, height=12, wrap=tk.WORD, font=("Menlo", 11))
        self.output.configure(bg=COLORS["card"], fg=COLORS["text"], relief=tk.FLAT, state=tk.DISABLED)
        self.output.pack(fill=tk.BOTH, expand=True, pady=(6, 8))

        # Configure text tags for coloring
        self.output.tag_configure("section", font=("Menlo", 11, "bold"), foreground=COLORS["accent"])
        self.output.tag_configure("tier_official", foreground=COLORS["success"])
        self.output.tag_configure("tier_reference", foreground=COLORS["warning"])
        self.output.tag_configure("tier_calculated", foreground=COLORS["accent"])
        self.output.tag_configure("url", foreground=COLORS["accent"], font=("Menlo", 9), underline=True)
        self.output.tag_configure("extra_field", foreground=COLORS["text_muted"])

        # Make URLs clickeable
        self.output.tag_bind("url", "<Button-1>", self._on_url_click)
        self.output.tag_bind("url", "<Enter>", lambda e: self.output.configure(cursor="hand2"))
        self.output.tag_bind("url", "<Leave>", lambda e: self.output.configure(cursor=""))

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
        self.log_text.tag_configure("debug", foreground="#6b7280")  # Gray for debug logs

        # Right: Candidates and Sources Panel
        right = ttk.Frame(body)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        ttk.Label(right, text="Candidatos", style="Sub.TLabel").pack(anchor=tk.W)
        self.candidate_list = tk.Listbox(right, height=8, width=40, font=("Helvetica Neue", 11))
        self.candidate_list.configure(
            bg=COLORS["card"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#ffffff",
            relief=tk.FLAT
        )
        self.candidate_list.pack(fill=tk.BOTH, expand=False, pady=(6, 8))
        self.candidate_list.bind("<Double-1>", lambda e: self._select_candidate())

        ttk.Button(right, text="Seleccionar", command=self._select_candidate).pack(fill=tk.X)

        # Sources Panel - Reference Links
        sources_frame = ttk.Frame(right)
        sources_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        # Component type selector
        type_row = ttk.Frame(sources_frame)
        type_row.pack(fill=tk.X)
        ttk.Label(type_row, text="Fuentes de consulta", style="Sub.TLabel").pack(side=tk.LEFT)

        self.component_type_var = tk.StringVar(value="CPU")
        type_combo = ttk.Combobox(
            type_row,
            textvariable=self.component_type_var,
            values=["CPU", "GPU", "RAM", "MAINBOARD", "DISK"],
            state="readonly",
            width=12,
        )
        type_combo.pack(side=tk.RIGHT)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self._update_sources_panel())

        # Scrollable sources list
        self.sources_text = tk.Text(
            sources_frame,
            height=12,
            width=40,
            wrap=tk.WORD,
            font=("Helvetica Neue", 10),
            cursor="arrow",
        )
        self.sources_text.configure(
            bg=COLORS["card"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            state=tk.DISABLED,
        )
        self.sources_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        # Configure tags for sources panel
        self.sources_text.tag_configure("category", font=("Helvetica Neue", 10, "bold"), foreground=COLORS["accent"])
        self.sources_text.tag_configure("link", foreground=COLORS["accent"], underline=True)
        self.sources_text.tag_bind("link", "<Button-1>", self._on_source_link_click)
        self.sources_text.tag_bind("link", "<Enter>", lambda e: self.sources_text.configure(cursor="hand2"))
        self.sources_text.tag_bind("link", "<Leave>", lambda e: self.sources_text.configure(cursor="arrow"))

        # Initialize sources panel
        self._update_sources_panel()

        # Footer with export options
        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(footer, text="Reset", command=self._reset).pack(side=tk.LEFT)
        ttk.Button(footer, text="Feedback", command=self._show_manual_feedback_dialog).pack(side=tk.LEFT, padx=(8, 0))

        export_frame = ttk.Frame(footer)
        export_frame.pack(side=tk.RIGHT)

        for fmt in ["CSV", "XLSX", "MD"]:
            ttk.Button(
                export_frame,
                text=f"Exportar {fmt}",
                command=lambda f=fmt.lower(): self._export(f),
            ).pack(side=tk.LEFT, padx=(4, 0))

        # Version and copyright
        version_frame = ttk.Frame(container)
        version_frame.pack(fill=tk.X, pady=(12, 0))
        version_text = f"v{__version__} (build {__build__})  |  {__copyright__}"
        ttk.Label(
            version_frame,
            text=version_text,
            style="Log.TLabel",
            foreground=COLORS["text_muted"],
        ).pack(side=tk.RIGHT)

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
        elif event.type in (EventType.SOURCE_ANTIBOT, EventType.SOURCE_TIMEOUT, EventType.VALIDATION_WARNING, EventType.LOG_WARNING):
            tag = "warning"
        elif event.type in (EventType.ERROR_RECOVERABLE, EventType.ERROR_FATAL, EventType.FAILED, EventType.LOG_ERROR):
            tag = "error"
        elif event.type == EventType.LOG_DEBUG:
            tag = "debug"  # Gray for debug logs
        elif event.type == EventType.LOG_INFO:
            tag = "info"

        self.log_text.insert(tk.END, f"[{event.type.value}] {event.message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_url_click(self, event: tk.Event) -> None:
        """Open URL in browser when clicked."""
        # Get the index of the click position
        index = self.output.index(f"@{event.x},{event.y}")

        # Get the range of the url tag at this position
        tag_range = self.output.tag_prevrange("url", f"{index}+1c")
        if not tag_range:
            tag_range = self.output.tag_nextrange("url", index)

        if tag_range:
            url = self.output.get(tag_range[0], tag_range[1]).strip()
            if url.startswith("http"):
                webbrowser.open(url)

    def _update_sources_panel(self, component_type: str = None) -> None:
        """Update the sources panel based on selected component type."""
        self.sources_text.configure(state=tk.NORMAL)
        self.sources_text.delete("1.0", tk.END)

        # Use provided type or get from combobox
        if component_type:
            self.component_type_var.set(component_type)

        type_str = self.component_type_var.get()
        try:
            comp_type = ComponentType(type_str)
        except ValueError:
            comp_type = ComponentType.CPU

        links = REFERENCE_LINKS.get(comp_type, {})

        if not links:
            self.sources_text.insert(tk.END, "\nNo hay fuentes para este tipo.\n")
            self.sources_text.configure(state=tk.DISABLED)
            return

        # Store URLs for click handling
        self._source_urls = {}
        url_index = 0

        for category, items in links.items():
            self.sources_text.insert(tk.END, f"\n{category}\n", "category")
            for name, url in items:
                # Store URL with unique tag
                tag_name = f"link_{url_index}"
                self._source_urls[tag_name] = url
                self.sources_text.insert(tk.END, "  ")
                # Insert bullet with link color
                self.sources_text.insert(tk.END, "→ ", "link")
                self.sources_text.insert(tk.END, name, ("link", tag_name))
                self.sources_text.insert(tk.END, "\n")
                # Bind click to this specific tag
                self.sources_text.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
                self.sources_text.tag_bind(tag_name, "<Enter>", lambda e: self.sources_text.configure(cursor="hand2"))
                self.sources_text.tag_bind(tag_name, "<Leave>", lambda e: self.sources_text.configure(cursor="arrow"))
                url_index += 1

        self.sources_text.configure(state=tk.DISABLED)
        self.update_idletasks()

    def _on_source_link_click(self, event: tk.Event) -> None:
        """Handle click on source link."""
        # This is handled by individual tag bindings now
        pass

    def _clear_log(self) -> None:
        """Clear the log area."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _log_legacy_event(self, status: str, message: str) -> None:
        """Log an OrchestratorEvent to the log area."""
        self.log_text.configure(state=tk.NORMAL)

        # Determine tag based on status
        tag = "info"
        if status in ("READY_TO_ADD", "RESULTADO", "SCRAPE"):
            tag = "success"
        elif status in ("NEEDS_USER_SELECTION", "RESOLVE_ENTITY"):
            tag = "warning"
        elif status.startswith("ERROR"):
            tag = "error"

        self.log_text.insert(tk.END, f"[{status}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.update_idletasks()

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

        # Determinar secciones relevantes según los tipos de componentes presentes
        relevant_sections = set()
        for component in self.ficha_manager.components:
            comp_type = component.component_type.value
            sections = COMPONENT_SECTIONS.get(comp_type, [])
            relevant_sections.update(sections)

        # Collect unique source URLs for fiscalización
        source_urls = set()

        # Collect template field keys for expanded view comparison
        template_keys = set()

        for field in ficha.fields_by_template:
            if field.value is None:
                continue

            # Filtrar: solo mostrar secciones relevantes al tipo de componente
            if field.section not in relevant_sections:
                continue

            template_keys.add(field.field)

            if field.section != current_section:
                current_section = field.section
                self.output.insert(tk.END, f"\n{current_section}\n", "section")
                self.output.insert(tk.END, "-" * 40 + "\n")

            # Determine origin indicator
            status = _to_spec_status(field.status)
            tier = _to_source_tier(field.source_tier)
            origin = get_data_origin(status, tier)
            tier_tag, tier_label = ORIGIN_INDICATORS.get(origin, ("", ""))

            value_str = str(field.value)
            if field.unit:
                value_str += f" {field.unit}"

            # Insert field into widget - indicador a la izquierda
            if tier_label:
                self.output.insert(tk.END, f"  {tier_label} ", tier_tag)
            else:
                self.output.insert(tk.END, "    ")  # Espaciado si no hay indicador
            self.output.insert(tk.END, f"{field.field}: {value_str}\n")

            # Track source URLs for fiscalización
            if field.source_url and field.source_url not in ("CALCULATED", "catalog", None):
                source_urls.add(field.source_url)

        # Show extra fields in expanded view
        if self.expanded_view_var.get():
            extra_fields = []
            for component in self.ficha_manager.components:
                comp_type = component.component_type.value
                for spec in component.specs:
                    # Check if this spec is NOT in the template
                    if spec.key not in template_keys and spec.value is not None:
                        extra_fields.append((comp_type, spec))
                        # Track URL from extra fields too
                        if spec.source_url and spec.source_url not in ("CALCULATED", "catalog", None):
                            source_urls.add(spec.source_url)

            if extra_fields:
                self.output.insert(tk.END, "\nDatos adicionales (no en template)\n", "section")
                self.output.insert(tk.END, "-" * 40 + "\n")

                current_comp_type = None
                for comp_type, spec in extra_fields:
                    if comp_type != current_comp_type:
                        current_comp_type = comp_type
                        comp_type_es = {"GPU": "Gráfica", "CPU": "Procesador", "RAM": "Memoria RAM", "MAINBOARD": "Placa base", "DISK": "Disco"}.get(comp_type, comp_type)
                        self.output.insert(tk.END, f"  [{comp_type_es}]\n", "extra_field")

                    value_str = str(spec.value)
                    if spec.unit:
                        value_str += f" {spec.unit}"

                    # Determine tier indicator using same logic as template fields
                    status = _to_spec_status(spec.status)
                    tier = _to_source_tier(spec.source_tier)
                    origin = get_data_origin(status, tier)
                    tier_tag, tier_label = ORIGIN_INDICATORS.get(origin, ("", ""))

                    field_name = SPEC_TRANSLATIONS.get(spec.key) or spec.label or spec.key

                    if tier_label:
                        self.output.insert(tk.END, f"    {tier_label} ", tier_tag)
                    else:
                        self.output.insert(tk.END, "      ")
                    self.output.insert(tk.END, f"{field_name}: {value_str}\n", "extra_field")

        # Show source URLs section for fiscalización (clickeable)
        if source_urls:
            self.output.insert(tk.END, "\nFuentes (click para abrir)\n", "section")
            self.output.insert(tk.END, "-" * 40 + "\n")
            for url in sorted(source_urls):
                self.output.insert(tk.END, f"  {url}\n", "url")

        # Show legend for origin indicators
        self.output.insert(tk.END, "\nLeyenda\n", "section")
        self.output.insert(tk.END, "-" * 40 + "\n")
        self.output.insert(tk.END, "  ● ", "tier_official")
        self.output.insert(tk.END, "Oficial (sitio del fabricante)\n")
        self.output.insert(tk.END, "  ◆ ", "tier_official")
        self.output.insert(tk.END, "Catálogo (datos internos + JEDEC)\n")
        self.output.insert(tk.END, "  ◐ ", "tier_reference")
        self.output.insert(tk.END, "Referencia (passmark, pcpartpicker)\n")
        self.output.insert(tk.END, "  ◇ ", "tier_calculated")
        self.output.insert(tk.END, "Calculado (derivado de otros datos)\n")

        # Update banner
        if ficha.has_reference:
            self.banner_var.set("⚠️ Ficha contiene datos REFERENCE (no oficiales)")
        else:
            self.banner_var.set("")

        self.output.configure(state=tk.DISABLED)
        self.output.see("1.0")  # Scroll to top
        self.update_idletasks()  # Force UI refresh

    def _process(self) -> None:
        """Process the current input."""
        input_value = self.input_var.get().strip()
        if not input_value:
            return

        # Store for feedback
        self._last_input = input_value

        # Clear previous state
        self._clear_log()
        self.progress_var.set(0)
        self.candidate_list.delete(0, tk.END)

        # Log inicio
        self._log_legacy_event("INICIO", f"Procesando: {input_value}")

        # Process
        events = self.orchestrator.process_input(input_value)

        for event in events:
            self.status_var.set(event.status)
            self.progress_var.set(event.progress)

            # Log cada evento
            self._log_legacy_event(event.status, event.log)

            if event.status == "NEEDS_USER_SELECTION" and event.candidates:
                self.candidate_list.delete(0, tk.END)
                for idx, candidate in enumerate(event.candidates):
                    brand = candidate.canonical.get("brand", "")
                    model = candidate.canonical.get("model", "")
                    score = candidate.score
                    tier = candidate.source_tier.value if hasattr(candidate, 'source_tier') else "?"
                    self.candidate_list.insert(tk.END, f"{idx + 1}. {brand} {model} ({tier}, {score:.0%})")

            if event.status == "READY_TO_ADD" and event.component_result:
                self.ficha_manager.add_component(event.component_result)
                self._update_output()
                # Update sources panel with detected component type
                r = event.component_result
                if hasattr(r, 'component_type'):
                    self._update_sources_panel(r.component_type.value)
                    self._last_component_type = r.component_type.value
                # Log resultado
                self._log_legacy_event(
                    "RESULTADO",
                    f"Match: {r.exact_match}, Tier: {r.source_tier.value}, Confianza: {r.source_confidence:.0%}"
                )
                # Ask for feedback after successful search
                self.after(500, lambda: self._ask_feedback_gui("success"))

            if event.status.startswith("ERROR"):
                self._log_event(Event.error_recoverable(event.log))
                # Ask for feedback on error
                self.after(500, lambda: self._ask_feedback_gui("error", event.log))

    def _select_candidate(self) -> None:
        """Select a candidate from the list."""
        if not self.orchestrator.last_candidates:
            return

        selection = self.candidate_list.curselection()
        if not selection:
            messagebox.showinfo("Selección", "Selecciona un candidato de la lista")
            return

        index = selection[0]
        candidate = self.orchestrator.last_candidates[index]
        self._log_legacy_event("SELECCIÓN", f"Candidato {index + 1}: {candidate.canonical.get('model', '')}")

        events = self.orchestrator.select_candidate(index)

        for event in events:
            self.status_var.set(event.status)
            self.progress_var.set(event.progress)
            self._log_legacy_event(event.status, event.log)

            if event.status == "READY_TO_ADD" and event.component_result:
                self.ficha_manager.add_component(event.component_result)
                self._update_output()
                r = event.component_result
                # Update sources panel with detected component type
                if hasattr(r, 'component_type'):
                    self._update_sources_panel(r.component_type.value)
                self._log_legacy_event(
                    "RESULTADO",
                    f"Match: {r.exact_match}, Tier: {r.source_tier.value}, Confianza: {r.source_confidence:.0%}"
                )

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

    def _ask_feedback_gui(self, result: str, error_msg: str = "") -> None:
        """Show feedback dialog after a search.

        Args:
            result: Search result ("success", "no_results", "error")
            error_msg: Error message if applicable
        """
        # Capture search context
        self.feedback.capture_search(
            input_text=self._last_input,
            component_type=self._last_component_type,
            result=result,
            error_message=error_msg,
        )

        # Show reminder every N searches
        if self.feedback.should_show_reminder():
            self.beta_banner_var.set(
                f"📊 Llevas {self.feedback.search_count} búsquedas - ¿Todo bien? Tu feedback es valioso"
            )

        # Ask if it worked
        response = messagebox.askyesno(
            "Feedback Beta",
            "¿La búsqueda funcionó correctamente?\n\n"
            "Tu feedback nos ayuda a mejorar HardwareXtractor.",
            icon="question",
        )

        if not response:
            # Show dialog to ask what went wrong
            self._show_feedback_dialog()

    def _show_feedback_dialog(self) -> None:
        """Show dialog to collect feedback details."""
        dialog = tk.Toplevel(self)
        dialog.title("Reportar problema")
        dialog.geometry("450x250")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 450) // 2
        y = self.winfo_y() + (self.winfo_height() - 250) // 2
        dialog.geometry(f"+{x}+{y}")

        # Content
        tk.Label(
            dialog,
            text="¿Qué salió mal?",
            font=("Helvetica Neue", 14, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(pady=(20, 10))

        tk.Label(
            dialog,
            text="(opcional - puedes dejarlo vacío)",
            font=("Helvetica Neue", 10),
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
        ).pack()

        # Text input
        text_frame = tk.Frame(dialog, bg=COLORS["bg"])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        problem_text = tk.Text(
            text_frame,
            height=4,
            font=("Helvetica Neue", 11),
            bg=COLORS["card"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=COLORS["accent"],
            highlightbackground="#d1d5db",
        )
        problem_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = tk.Frame(dialog, bg=COLORS["bg"])
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        def send_report():
            comment = problem_text.get("1.0", tk.END).strip()
            dialog.destroy()

            # Generate and send report
            report = self.feedback.generate_report(user_comment=comment)
            if report:
                self.status_var.set("Enviando reporte...")
                self.update_idletasks()

                result = send_feedback_report(
                    title=report["title"],
                    body=report["body"],
                    labels=report["labels"],
                )

                if result.get("status") == "success":
                    messagebox.showinfo(
                        "¡Gracias!",
                        f"¡Gracias por tu feedback!\n"
                        f"Tu reporte nos ayuda a mejorar.\n\n"
                        f"Issue #{result.get('issue_number', '')} creado.",
                    )
                else:
                    messagebox.showwarning(
                        "Error",
                        f"No se pudo enviar el reporte:\n{result.get('message', 'Error desconocido')}",
                    )

                self.status_var.set("Listo")

        def cancel():
            dialog.destroy()

        ttk.Button(btn_frame, text="Cancelar", command=cancel).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Enviar reporte", style="Primary.TButton", command=send_report).pack(side=tk.RIGHT)

        # Focus on text
        problem_text.focus_set()

    def _show_manual_feedback_dialog(self) -> None:
        """Show dialog to send manual feedback (not tied to a search)."""
        dialog = tk.Toplevel(self)
        dialog.title("Enviar Feedback")
        dialog.geometry("500x350")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 350) // 2
        dialog.geometry(f"+{x}+{y}")

        # Title
        tk.Label(
            dialog,
            text="Enviar Feedback",
            font=("Helvetica Neue", 16, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(pady=(20, 5))

        tk.Label(
            dialog,
            text="Tu feedback nos ayuda a mejorar HardwareXtractor",
            font=("Helvetica Neue", 10),
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
        ).pack()

        # Feedback type selector
        type_frame = tk.Frame(dialog, bg=COLORS["bg"])
        type_frame.pack(fill=tk.X, padx=20, pady=(15, 5))

        tk.Label(
            type_frame,
            text="Tipo:",
            font=("Helvetica Neue", 11),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT)

        feedback_type_var = tk.StringVar(value="Bug o error")
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=feedback_type_var,
            values=["Bug o error", "Sugerencia de mejora", "Componente no soportado", "Otro"],
            state="readonly",
            width=25,
        )
        type_combo.pack(side=tk.LEFT, padx=(10, 0))

        # Comment area
        tk.Label(
            dialog,
            text="Comentario:",
            font=("Helvetica Neue", 11),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor=tk.W,
        ).pack(fill=tk.X, padx=20, pady=(10, 5))

        comment_frame = tk.Frame(dialog, bg=COLORS["bg"])
        comment_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        comment_text = tk.Text(
            comment_frame,
            height=6,
            font=("Helvetica Neue", 11),
            bg=COLORS["card"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=COLORS["accent"],
            highlightbackground="#d1d5db",
        )
        comment_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = tk.Frame(dialog, bg=COLORS["bg"])
        btn_frame.pack(fill=tk.X, padx=20, pady=(10, 20))

        def send_feedback():
            comment = comment_text.get("1.0", tk.END).strip()
            if not comment:
                messagebox.showwarning("Feedback", "Por favor escribe un comentario")
                return

            type_label = feedback_type_var.get()
            dialog.destroy()

            # Create manual feedback report
            import platform
            import sys
            from datetime import datetime

            title = f"[Feedback Beta] {type_label}"
            body = f"""## Tipo de feedback
{type_label}

## Comentario del usuario
> {comment}

## Información del sistema
- **Versión:** {__version__}
- **OS:** {platform.system()} {platform.release()}
- **Python:** {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}
- **Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
*Feedback manual de HardwareXtractor Beta v{__version__}*
"""

            self.status_var.set("Enviando feedback...")
            self.update_idletasks()

            result = send_feedback_report(
                title=title,
                body=body,
                labels=["beta-feedback", "manual-feedback"],
            )

            if result.get("status") == "success":
                messagebox.showinfo(
                    "¡Gracias!",
                    f"¡Gracias por tu feedback!\n"
                    f"Tu comentario nos ayuda a mejorar.\n\n"
                    f"Issue #{result.get('issue_number', '')} creado.",
                )
            else:
                messagebox.showwarning(
                    "Error",
                    f"No se pudo enviar el feedback:\n{result.get('message', 'Error desconocido')}",
                )

            self.status_var.set("Listo")

        def cancel():
            dialog.destroy()

        ttk.Button(btn_frame, text="Cancelar", command=cancel).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Enviar", style="Primary.TButton", command=send_feedback).pack(side=tk.RIGHT)

        # Focus on text
        comment_text.focus_set()


if __name__ == "__main__":
    app = HardwareXtractorApp()
    app.mainloop()
