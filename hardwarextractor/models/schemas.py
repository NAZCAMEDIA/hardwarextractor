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
    OFFICIAL = "OFFICIAL"
    REFERENCE = "REFERENCE"
    NONE = "NONE"


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
    classification_confidence: float
    canonical: Dict[str, Any]
    specs: List[SpecField] = field(default_factory=list)


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
