"""Ficha manager for aggregating and managing component data."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from hardwarextractor.models.schemas import (
    ComponentRecord,
    DataOrigin,
    FichaAggregated,
    get_data_origin,
    SourceTier,
    SpecField,
    SpecStatus,
    TemplateField,
    new_ficha_id,
)
from hardwarextractor.aggregate.aggregator import aggregate_components


class FichaManager:
    """Manages the aggregated ficha state.

    The ficha is a collection of components with their specs,
    aggregated into a unified view following the FIELD_CATALOG template.
    """

    def __init__(self):
        """Initialize an empty ficha."""
        self._components: list[ComponentRecord] = []
        self._ficha_id: str = new_ficha_id()
        self._created_at: datetime = datetime.now()
        self._last_updated: datetime = self._created_at

    @property
    def ficha_id(self) -> str:
        return self._ficha_id

    @property
    def component_count(self) -> int:
        return len(self._components)

    @property
    def components(self) -> list[ComponentRecord]:
        return self._components.copy()

    def add_component(self, component: ComponentRecord) -> None:
        """Add a component to the ficha.

        For non-stacking types (CPU, MAINBOARD), replaces existing.
        For stacking types (RAM, DISK), appends.

        Args:
            component: The component to add
        """
        comp_type = component.component_type.value

        # Non-stacking types replace existing
        if comp_type not in ("RAM", "DISK"):
            self._components = [
                c for c in self._components
                if c.component_type != component.component_type
            ]

        self._components.append(component)
        self._last_updated = datetime.now()

    def remove_component(self, component_id: str) -> bool:
        """Remove a component by ID.

        Args:
            component_id: The component ID to remove

        Returns:
            True if removed, False if not found
        """
        original_count = len(self._components)
        self._components = [
            c for c in self._components
            if c.component_id != component_id
        ]

        if len(self._components) < original_count:
            self._last_updated = datetime.now()
            return True
        return False

    def get_aggregated(self) -> FichaAggregated:
        """Get the aggregated ficha view.

        Returns:
            FichaAggregated with all components and template fields
        """
        return aggregate_components(self._components)

    def has_reference_data(self) -> bool:
        """Check if any component has REFERENCE tier data.

        Returns:
            True if any field has REFERENCE tier
        """
        for component in self._components:
            for spec in component.specs:
                if spec.source_tier == SourceTier.REFERENCE:
                    return True
        return False

    def get_spec(self, key: str) -> Optional[SpecField]:
        """Get a specific spec field by key.

        Args:
            key: The spec key to look up

        Returns:
            SpecField if found, None otherwise
        """
        ficha = self.get_aggregated()
        for tf in ficha.fields_by_template:
            if tf.field == key and tf.value is not None:
                return SpecField(
                    key=tf.field,
                    label=tf.field,
                    value=tf.value,
                    unit=tf.unit,
                    status=tf.status,
                    source_tier=tf.source_tier,
                    source_name=tf.source_name,
                    source_url=tf.source_url,
                    confidence=tf.confidence,
                )
        return None

    def reset(self) -> None:
        """Reset the ficha to empty state."""
        self._components = []
        self._ficha_id = new_ficha_id()
        self._created_at = datetime.now()
        self._last_updated = self._created_at

    def to_dict(self) -> dict[str, Any]:
        """Convert ficha to dictionary for serialization.

        Returns:
            Dictionary representation of the ficha
        """
        ficha = self.get_aggregated()
        return {
            "ficha_id": self._ficha_id,
            "created_at": self._created_at.isoformat(),
            "last_updated": self._last_updated.isoformat(),
            "component_count": len(self._components),
            "has_reference": self.has_reference_data(),
            "components": [
                {
                    "component_id": c.component_id,
                    "type": c.component_type.value,
                    "brand": c.canonical.get("brand", ""),
                    "model": c.canonical.get("model", ""),
                    "part_number": c.canonical.get("part_number", ""),
                    "specs_count": len(c.specs),
                }
                for c in self._components
            ],
            "fields_by_template": [
                {
                    "section": tf.section,
                    "field": tf.field,
                    "value": tf.value,
                    "unit": tf.unit,
                    "status": tf.status.value if tf.status else None,
                    "tier": tf.source_tier.value if tf.source_tier else None,
                    "source_name": tf.source_name,
                    "source_url": tf.source_url,
                }
                for tf in ficha.fields_by_template
            ],
        }

    def get_export_rows(self) -> list[dict[str, Any]]:
        """Get rows for CSV/XLSX export.

        Only exports sections relevant to the component types present.

        Returns:
            List of dictionaries with export data
        """
        # Mapeo de tipo de componente a secciones relevantes
        COMPONENT_SECTIONS = {
            "CPU": ["Identificación", "Procesador"],
            "MAINBOARD": ["Identificación", "Placa base"],
            "RAM": ["Identificación", "RAM"],
            "GPU": ["Identificación", "Gráfica"],
            "DISK": ["Identificación", "Disco duro"],
            "GENERAL": ["Identificación", "Datos generales"],
        }

        # Determinar secciones relevantes
        relevant_sections = set()
        for component in self._components:
            comp_type = component.component_type.value
            sections = COMPONENT_SECTIONS.get(comp_type, [])
            relevant_sections.update(sections)

        ficha = self.get_aggregated()
        rows = []

        for tf in ficha.fields_by_template:
            # Solo exportar secciones relevantes
            if tf.section not in relevant_sections:
                continue

            # Obtener origen simplificado
            status = tf.status if tf.status else SpecStatus.UNKNOWN
            tier = tf.source_tier if tf.source_tier else SourceTier.NONE
            origin = get_data_origin(status, tier)

            rows.append({
                "section": tf.section,
                "field": tf.field,
                "value": tf.value if tf.value is not None else "",
                "unit": tf.unit or "",
                "origen": origin.value,  # Origen simplificado
                "source_name": tf.source_name or "",
                "source_url": tf.source_url or "",
            })

        return rows

    def export(self, format: str, path: Optional[str] = None) -> str:
        """Export the ficha to a file.

        Args:
            format: Export format (csv, xlsx, md)
            path: Output path (auto-generated if None)

        Returns:
            The path to the exported file
        """
        from hardwarextractor.export import ExporterFactory

        if path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"./hxtractor_export_{timestamp}.{format.lower()}"

        exporter = ExporterFactory.get(format)
        result = exporter.export(self, Path(path))

        return str(result.path)
