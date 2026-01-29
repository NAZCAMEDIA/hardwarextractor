"""Markdown exporter for HardwareXtractor."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from hardwarextractor.export.base import BaseExporter, ExportResult

if TYPE_CHECKING:
    from hardwarextractor.engine.ficha_manager import FichaManager


class MarkdownExporter(BaseExporter):
    """Export ficha to Markdown format with tables by section."""

    @property
    def format(self) -> str:
        return "md"

    def export(self, ficha_manager: "FichaManager", path: Path) -> ExportResult:
        """Export the ficha to Markdown.

        Args:
            ficha_manager: The ficha manager with data
            path: Output file path

        Returns:
            ExportResult with export information
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        header_info = self._get_header_info(ficha_manager)
        rows = ficha_manager.get_export_rows()

        lines = []

        # Header
        lines.append("# Ficha Técnica de Hardware")
        lines.append("")
        lines.append(f"**Fecha:** {header_info['date']}")
        lines.append(f"**ID:** {header_info['ficha_id'][:8]}...")
        lines.append(f"**Componentes:** {header_info['component_count']}")
        lines.append("")

        # Warning banner if has reference data
        if header_info["has_reference"]:
            lines.append("> **ADVERTENCIA:** Esta ficha contiene datos de fuentes")
            lines.append("> no oficiales (REFERENCE). Verificar antes de usar.")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Components summary
        lines.append("## Componentes Analizados")
        lines.append("")
        for comp in ficha_manager.components:
            brand = comp.canonical.get("brand", "")
            model = comp.canonical.get("model", "")
            lines.append(f"- **{comp.component_type.value}:** {brand} {model}")
        lines.append("")

        # Group rows by section
        sections: dict[str, list] = {}
        for row in rows:
            section = row["section"]
            if section not in sections:
                sections[section] = []
            sections[section].append(row)

        # Render each section
        for section_name, section_rows in sections.items():
            # Filter rows with values
            rows_with_data = [r for r in section_rows if r["value"]]

            if not rows_with_data:
                continue

            lines.append(f"## {section_name}")
            lines.append("")
            lines.append("| Campo | Valor | Origen | Fuente |")
            lines.append("|-------|-------|--------|--------|")

            for row in rows_with_data:
                field = row["field"]
                value = str(row["value"])
                if row["unit"]:
                    value += f" {row['unit']}"

                origen = row["origen"]
                source = self._format_source(row["source_name"], row["source_url"])

                lines.append(f"| {field} | {value} | {origen} | {source} |")

            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generado por HXtractor*")

        # Write file
        content = "\n".join(lines)
        path.write_text(content, encoding="utf-8")

        return ExportResult(
            path=path,
            format="md",
            rows=len(rows),
            success=True,
        )

    def _format_source(self, name: str | None, url: str | None) -> str:
        """Format source as markdown link.

        Args:
            name: Source name
            url: Source URL

        Returns:
            Formatted source string
        """
        if not name and not url:
            return "-"

        if url:
            # Extract domain for display
            try:
                domain = urlparse(url).netloc.replace("www.", "")
                display = name or domain
                # Truncate long names
                if len(display) > 20:
                    display = display[:17] + "..."
                return f"[{display}]({url})"
            except Exception:
                return name or "-"

        return name or "-"
