from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class ComponentType(str, Enum):
    CPU = "CPU"
    MAINBOARD = "MAINBOARD"
    RAM = "RAM"
    GPU = "GPU"
    DISK = "DISK"
    GENERAL = "GENERAL"


class SpecStatus(str, Enum):
    EXTRACTED_OFFICIAL = "EXTRACTED_OFFICIAL"
    EXTRACTED_REFERENCE = "EXTRACTED_REFERENCE"
    CALCULATED = "CALCULATED"
    NA = "NA"
    UNKNOWN = "UNKNOWN"


class SourceTier(str, Enum):
    OFFICIAL = "OFFICIAL"      # Fabricante oficial (intel.com, amd.com) → 100%
    REFERENCE = "REFERENCE"    # Comunidad validada (techpowerup, pcpartpicker) → 80%
    CATALOG = "CATALOG"        # Catálogo embebido (puede estar desactualizado) → 60%
    NONE = "NONE"              # Fuente desconocida → 0%


class DataOrigin(str, Enum):
    """Origen simplificado del dato - unifica Status y Tier para display."""
    OFICIAL = "OFICIAL"        # Scraping del sitio del fabricante
    CATALOGO = "CATÁLOGO"      # Catálogo interno + estándares JEDEC
    REFERENCIA = "REFERENCIA"  # Sitios de referencia (passmark, etc.)
    CALCULADO = "CALCULADO"    # Calculado por la app
    DESCONOCIDO = "DESCONOCIDO"  # Sin datos


# Mapeo de SourceTier a DataOrigin
_TIER_TO_ORIGIN = {
    SourceTier.OFFICIAL: DataOrigin.OFICIAL,
    SourceTier.CATALOG: DataOrigin.CATALOGO,
    SourceTier.REFERENCE: DataOrigin.REFERENCIA,
}

# Mapeo de SpecStatus a DataOrigin (fallback cuando tier no determina origen)
_STATUS_TO_ORIGIN = {
    SpecStatus.EXTRACTED_OFFICIAL: DataOrigin.OFICIAL,
    SpecStatus.EXTRACTED_REFERENCE: DataOrigin.REFERENCIA,
}


def get_data_origin(status: SpecStatus, tier: SourceTier) -> DataOrigin:
    """Deriva el origen simplificado a partir de status y tier.

    Args:
        status: El SpecStatus del campo
        tier: El SourceTier del campo

    Returns:
        DataOrigin simplificado para display
    """
    if status == SpecStatus.CALCULATED:
        return DataOrigin.CALCULADO

    if status in (SpecStatus.UNKNOWN, SpecStatus.NA):
        return DataOrigin.DESCONOCIDO

    if tier in _TIER_TO_ORIGIN:
        return _TIER_TO_ORIGIN[tier]

    return _STATUS_TO_ORIGIN.get(status, DataOrigin.DESCONOCIDO)


# Mapeo de SourceTier a porcentaje de confianza
SOURCE_TIER_CONFIDENCE = {
    SourceTier.OFFICIAL: 1.0,    # 100%
    SourceTier.REFERENCE: 0.8,   # 80%
    SourceTier.CATALOG: 0.6,     # 60%
    SourceTier.NONE: 0.0,        # 0%
}

# Fecha de ultima actualizacion del catalogo embebido
CATALOG_LAST_UPDATED = "2026-01-29"

# Mapeo de tipo de componente a secciones relevantes de la ficha
COMPONENT_SECTIONS = {
    "CPU": ["Identificación", "Procesador"],
    "MAINBOARD": ["Identificación", "Placa base"],
    "RAM": ["Identificación", "RAM"],
    "GPU": ["Identificación", "Gráfica"],
    "DISK": ["Identificación", "Disco duro"],
    "GENERAL": ["Identificación", "Datos generales"],
}


@dataclass
class SpecField:
    key: str
    label: str
    value: Any
    unit: Optional[str] = None
    status: SpecStatus = SpecStatus.UNKNOWN
    source_tier: SourceTier = SourceTier.NONE
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    confidence: float = 0.0
    notes: Optional[str] = None
    inputs_used: Optional[Dict[str, Any]] = None


@dataclass
class ComponentRecord:
    component_id: str
    input_raw: str
    input_normalized: str
    component_type: ComponentType
    canonical: Dict[str, Any]
    exact_match: bool = False                          # Si encontramos el componente buscado
    source_tier: SourceTier = SourceTier.NONE          # Tier de la fuente
    source_confidence: float = 0.0                     # Confianza basada en el tier
    data_date: Optional[str] = None                    # Fecha de los datos (catálogo o scraping)
    specs: List[SpecField] = field(default_factory=list)
    source_url: Optional[str] = None
    source_name: Optional[str] = None


@dataclass
class TemplateField:
    section: str
    field: str
    value: Any
    unit: Optional[str]
    status: SpecStatus
    source_tier: SourceTier
    source_name: Optional[str]
    source_url: Optional[str]
    confidence: float
    component_id: Optional[str]


@dataclass
class FichaAggregated:
    ficha_id: str
    general: Dict[str, Any] = field(default_factory=dict)
    components: List[ComponentRecord] = field(default_factory=list)
    fields_by_template: List[TemplateField] = field(default_factory=list)
    has_reference: bool = False


@dataclass
class RawExtract:
    source_url: str
    source_name: str
    source_tier: SourceTier
    fields: Dict[str, Any]
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class ResolveCandidate:
    canonical: Dict[str, Any]
    score: float
    source_url: str
    source_name: str
    spider_name: str
    source_tier: SourceTier = SourceTier.NONE


@dataclass
class ResolveResult:
    exact: bool
    candidates: List[ResolveCandidate]


@dataclass
class OrchestratorEvent:
    status: str
    progress: int
    log: str
    candidates: Optional[List[ResolveCandidate]] = None
    component_result: Optional[ComponentRecord] = None
    ficha_update: Optional[FichaAggregated] = None


def new_component_id() -> str:
    return str(uuid4())


def new_ficha_id() -> str:
    return str(uuid4())
