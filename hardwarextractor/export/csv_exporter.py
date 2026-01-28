from __future__ import annotations

import csv
from pathlib import Path

from hardwarextractor.models.schemas import FichaAggregated


CSV_HEADERS = [
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
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
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
