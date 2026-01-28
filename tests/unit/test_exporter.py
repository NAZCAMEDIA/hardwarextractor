from __future__ import annotations

from pathlib import Path

from hardwarextractor.export.csv_exporter import export_ficha_csv
from hardwarextractor.models.schemas import FichaAggregated, TemplateField, SpecStatus, SourceTier


def test_export_csv(tmp_path: Path):
    ficha = FichaAggregated(
        ficha_id="f1",
        fields_by_template=[
            TemplateField(
                section="Procesador",
                field="Núcleos físicos",
                value=8,
                unit=None,
                status=SpecStatus.EXTRACTED_OFFICIAL,
                source_tier=SourceTier.OFFICIAL,
                source_name="Intel",
                source_url="https://intel.com",
                confidence=0.9,
                component_id="cpu-1",
            )
        ],
    )
    out = export_ficha_csv(ficha, tmp_path / "ficha.csv")
    content = out.read_text(encoding="utf-8")
    assert "section,field,value" in content
