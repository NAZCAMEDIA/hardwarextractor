from __future__ import annotations

from typing import Dict, List, Tuple

from hardwarextractor.data.catalog import load_field_catalog
from hardwarextractor.mapper.mapper import map_component_to_template
from hardwarextractor.models.schemas import ComponentRecord, FichaAggregated, SpecStatus, SourceTier, TemplateField, new_ficha_id


_PRECEDENCE = {
    SpecStatus.EXTRACTED_OFFICIAL: 3,
    SpecStatus.EXTRACTED_REFERENCE: 2,
    SpecStatus.CALCULATED: 1,
    SpecStatus.NA: 0,
    SpecStatus.UNKNOWN: 0,
}


def aggregate_components(components: List[ComponentRecord], system_name: str | None = None) -> FichaAggregated:
    ficha = FichaAggregated(ficha_id=new_ficha_id())
    ficha.general["system_name"] = system_name or "UNKNOWN"

    mapped_fields: Dict[Tuple[str, str], TemplateField] = {}
    for component in components:
        for field in map_component_to_template(component):
            key = (field.section, field.field)
            existing = mapped_fields.get(key)
            if not existing:
                mapped_fields[key] = field
                continue
            if _PRECEDENCE[field.status] > _PRECEDENCE[existing.status]:
                mapped_fields[key] = field
                continue
            if _PRECEDENCE[field.status] == _PRECEDENCE[existing.status] and field.confidence > existing.confidence:
                mapped_fields[key] = field

    catalog = load_field_catalog()
    fields_by_template: List[TemplateField] = []
    for item in catalog:
        section, field_name = item["section"], item["field"]
        if section == "Datos generales" and field_name == "Nombre del equipo montado":
            fields_by_template.append(TemplateField(
                section=section,
                field=field_name,
                value=ficha.general["system_name"],
                unit=None,
                status=SpecStatus.UNKNOWN if ficha.general["system_name"] == "UNKNOWN" else SpecStatus.EXTRACTED_OFFICIAL,
                source_tier=SourceTier.NONE,
                source_name=None,
                source_url=None,
                confidence=1.0 if ficha.general["system_name"] != "UNKNOWN" else 0.0,
                component_id=None,
            ))
            continue

        field_obj = mapped_fields.get((section, field_name))
        if field_obj:
            fields_by_template.append(field_obj)
        else:
            fields_by_template.append(TemplateField(
                section=section,
                field=field_name,
                value="UNKNOWN",
                unit=None,
                status=SpecStatus.UNKNOWN,
                source_tier=SourceTier.NONE,
                source_name=None,
                source_url=None,
                confidence=0.0,
                component_id=None,
            ))

    ficha.components = components
    ficha.fields_by_template = fields_by_template
    ficha.has_reference = any(field.source_tier == SourceTier.REFERENCE for field in fields_by_template)

    return ficha
