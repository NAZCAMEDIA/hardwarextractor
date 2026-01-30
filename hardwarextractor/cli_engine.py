from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from hardwarextractor.aggregate.aggregator import aggregate_components
from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.app.paths import cache_db_path
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.export.csv_exporter import export_ficha_csv
from hardwarextractor.models.schemas import ComponentRecord
from hardwarextractor.data.spec_templates import apply_template_to_specs


class EngineSession:
    def __init__(self, orchestrator: Orchestrator | None = None, cache: SQLiteCache | None = None) -> None:
        self.cache = cache or SQLiteCache(cache_db_path())
        self.orchestrator = orchestrator or Orchestrator(cache=self.cache)
        self.last_component: ComponentRecord | None = None
        self.ficha = None

    def analyze_component(self, input_text: str) -> None:
        events = self.orchestrator.process_input(input_text)
        for event in events:
            if event.status:
                emit({"type": "status", "value": event.status})
            if event.log:
                emit({"type": "log", "value": event.log})
            if event.candidates:
                candidates = []
                for c in event.candidates:
                    candidates.append(
                        {
                            "brand": c.canonical.get("brand"),
                            "model": c.canonical.get("model"),
                            "part_number": c.canonical.get("part_number"),
                            "score": c.score,
                            "source_domain": c.source_url.split("/")[2] if c.source_url else "",
                        }
                    )
                emit({"type": "candidates", "value": candidates})
            if event.component_result:
                self.last_component = event.component_result
                emit({"type": "result", "value": _component_to_dict(event.component_result)})
            if event.ficha_update:
                self.ficha = event.ficha_update
                emit({"type": "ficha_update", "value": _ficha_to_dict(event.ficha_update)})

    def select_candidate(self, index: int) -> None:
        events = self.orchestrator.select_candidate(index)
        for event in events:
            if event.status:
                emit({"type": "status", "value": event.status})
            if event.log:
                emit({"type": "log", "value": event.log})
            if event.component_result:
                self.last_component = event.component_result
                emit({"type": "result", "value": _component_to_dict(event.component_result)})
            if event.ficha_update:
                self.ficha = event.ficha_update
                emit({"type": "ficha_update", "value": _ficha_to_dict(event.ficha_update)})

    def add_to_ficha(self) -> None:
        if not self.last_component:
            return
        components = self.orchestrator.components
        if self.last_component not in components:
            components.append(self.last_component)
        self.ficha = aggregate_components(components)
        emit({"type": "ficha_update", "value": _ficha_to_dict(self.ficha)})

    def show_ficha(self) -> None:
        if self.ficha:
            emit({"type": "ficha_update", "value": _ficha_to_dict(self.ficha)})

    def reset_ficha(self) -> None:
        self.orchestrator.components = []
        self.ficha = aggregate_components([])
        emit({"type": "ficha_update", "value": _ficha_to_dict(self.ficha)})

    def export_ficha(self, format: str, path: str | None = None) -> None:
        if not self.ficha:
            return
        fmt = format.lower()
        if not path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"./hxtractor_export_{timestamp}.{fmt}"
        if fmt == "csv":
            export_ficha_csv(self.ficha, path)
        elif fmt == "md":
            export_ficha_md(self.ficha, path)
        elif fmt == "xlsx":
            raise RuntimeError("XLSX no disponible en MVP")
        emit({"type": "log", "value": f"Exportado: {path}"})

    def get_complete_specs(self) -> None:
        """Get specs for last component with ALL template fields (unknown for missing)."""
        if self.last_component:
            emit({"type": "complete_specs", "value": _component_to_dict(self.last_component, include_all_specs=True)})


def export_ficha_md(ficha, path: str) -> None:
    lines: List[str] = []
    lines.append(f"# Export HXTRACTOR — {datetime.now().isoformat()}")
    lines.append("")
    if ficha.has_reference:
        lines.append("WARNING: La ficha contiene datos no oficiales (REFERENCE).")
        lines.append("")
    lines.append("## Componentes añadidos")
    for component in ficha.components:
        canonical = component.canonical
        lines.append(f"- {component.component_type.value}: {canonical.get('brand','')} {canonical.get('model','')} {canonical.get('part_number','')}")
    lines.append("")
    current_section = None
    for field in ficha.fields_by_template:
        if field.section != current_section:
            current_section = field.section
            lines.append(f"## {current_section}")
            lines.append("| Campo | Valor | Status | Tier | Fuente |")
            lines.append("| --- | --- | --- | --- | --- |")
        source = field.source_url or ""
        lines.append(f"| {field.field} | {field.value} | {field.status.value} | {field.source_tier.value} | {source} |")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _component_to_dict(component: ComponentRecord, include_all_specs: bool = False) -> Dict[str, Any]:
    """Convert component to dictionary format.

    Args:
        component: The component record
        include_all_specs: If True, includes all template fields with 'unknown' for missing
    """
    specs = component.specs

    # Apply template if requested (shows all possible fields)
    if include_all_specs:
        specs = apply_template_to_specs(
            component.component_type,
            component.specs,
            component.canonical,
        )

    return {
        "component_type": component.component_type.value,
        "canonical": component.canonical,
        "specs": [
            {
                "key": spec.key,
                "label": spec.label,
                "value": spec.value,
                "unit": spec.unit,
                "status": spec.status.value,
                "source_tier": spec.source_tier.value,
                "source_url": spec.source_url,
            }
            for spec in specs
        ],
    }


def _ficha_to_dict(ficha) -> Dict[str, Any]:
    return {
        "has_reference": ficha.has_reference,
        "fields_by_template": [
            {
                "section": field.section,
                "field": field.field,
                "value": field.value,
                "status": field.status.value,
                "source_tier": field.source_tier.value,
                "source_url": field.source_url,
            }
            for field in ficha.fields_by_template
        ],
    }


def emit(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main() -> None:
    session = EngineSession()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            cmd = json.loads(line)
        except json.JSONDecodeError:
            continue
        command = cmd.get("command")
        payload = cmd.get("payload", {})
        try:
            if command == "analyze_component":
                session.analyze_component(payload.get("input", ""))
            elif command == "select_candidate":
                session.select_candidate(int(payload.get("index", 0)))
            elif command == "add_to_ficha":
                session.add_to_ficha()
            elif command == "show_ficha":
                session.show_ficha()
            elif command == "export_ficha":
                session.export_ficha(payload.get("format", "csv"), payload.get("path"))
            elif command == "reset_ficha":
                session.reset_ficha()
            elif command == "get_complete_specs":
                session.get_complete_specs()
            else:
                emit({"type": "error", "value": {"message": "Comando desconocido", "recoverable": True}})
        except Exception as exc:  # noqa: BLE001
            emit({"type": "error", "value": {"message": str(exc), "recoverable": True}})


if __name__ == "__main__":
    main()
