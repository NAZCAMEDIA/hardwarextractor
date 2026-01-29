"""CSV exporter for HardwareXtractor."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

from hardwarextractor.export.base import BaseExporter, ExportResult
from hardwarextractor.models.schemas import FichaAggregated

if TYPE_CHECKING:
    from hardwarextractor.engine.ficha_manager import FichaManager


CSV_HEADERS = [
    "Seccion",
    "Campo",
    "Valor",
    "Unidad",
    "Origen",
    "Fuente",
    "URL",
]


class CSVExporter(BaseExporter):
    """Export ficha to CSV format with full traceability."""

    @property
    def format(self) -> str:
        return "csv"

    def export(self, ficha_manager: "FichaManager", path: Path) -> ExportResult:
        """Export the ficha to CSV.

        Args:
            ficha_manager: The ficha manager with data
            path: Output file path

        Returns:
            ExportResult with export information
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        rows = ficha_manager.get_export_rows()

        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
            writer.writeheader()

            for row in rows:
                writer.writerow({
                    "Seccion": row["section"],
                    "Campo": row["field"],
                    "Valor": row["value"],
                    "Unidad": row["unit"],
                    "Origen": row["origen"],
                    "Fuente": row["source_name"],
                    "URL": self._truncate_url(row["source_url"], 80),
                })

        return ExportResult(
            path=path,
            format="csv",
            rows=len(rows),
            success=True,
        )


# Legacy headers for backwards compatibility
LEGACY_CSV_HEADERS = [
    "section",
    "field",
    "value",
    "unit",
    "status",
    "source_tier",
    "source_name",
    "source_url",
    "confidence",
    "component_id",
]


def export_ficha_csv(ficha: FichaAggregated, path: str | Path) -> Path:
    """Legacy export function for backwards compatibility.

    Args:
        ficha: The aggregated ficha
        path: Output path

    Returns:
        Path to exported file
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEGACY_CSV_HEADERS)
        writer.writeheader()

        for field in ficha.fields_by_template:
            writer.writerow({
                "section": field.section,
                "field": field.field,
                "value": field.value,
                "unit": field.unit or "",
                "status": field.status.value,
                "source_tier": field.source_tier.value,
                "source_name": field.source_name or "",
                "source_url": field.source_url or "",
                "confidence": field.confidence,
                "component_id": field.component_id or "",
            })

    return output
