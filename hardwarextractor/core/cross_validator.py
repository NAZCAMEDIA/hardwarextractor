"""Cross-validation for web search data.

Consulta múltiples fuentes y solo valida datos que coinciden entre 2+ fuentes.
Los datos validados se agregan al catálogo automáticamente.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict

from hardwarextractor.models.schemas import (
    ComponentType,
    SourceTier,
    SpecField,
    SpecStatus,
)
from hardwarextractor.core.events import Event


@dataclass
class SourceResult:
    """Result from a single source."""
    source_name: str
    source_url: str
    specs: List[SpecField]
    success: bool
    error: Optional[str] = None


@dataclass
class ValidatedSpec:
    """A spec that has been cross-validated from multiple sources."""
    key: str
    value: Any
    sources: List[str]  # Names of sources that agree
    confidence: float   # n_agreeing / n_total
    unit: Optional[str] = None


@dataclass
class CrossValidationResult:
    """Result of cross-validation from multiple sources."""
    component_input: str
    component_type: ComponentType
    validated_specs: List[ValidatedSpec]
    all_source_results: List[SourceResult]
    consensus_reached: bool  # True if 2+ sources agree on core specs
    should_persist: bool     # True if quality is high enough to save

    def to_spec_fields(self) -> List[SpecField]:
        """Convert validated specs to SpecField objects."""
        return [
            SpecField(
                key=vs.key,
                label=vs.key.replace(".", " ").replace("_", " ").title(),
                value=vs.value,
                unit=vs.unit,
                status=SpecStatus.EXTRACTED_REFERENCE,
                source_tier=SourceTier.REFERENCE,
                source_name=", ".join(vs.sources),
                confidence=vs.confidence,
                notes=f"Validated from {len(vs.sources)} sources",
            )
            for vs in self.validated_specs
        ]


# Comparison rules for different spec types
COMPARISON_RULES = {
    # Exact match required
    "exact": lambda a, b: str(a).lower().strip() == str(b).lower().strip(),

    # Numeric with 5% tolerance
    "numeric_5pct": lambda a, b: _numeric_compare(a, b, 0.05),

    # Numeric with 10% tolerance
    "numeric_10pct": lambda a, b: _numeric_compare(a, b, 0.10),
}

# Map spec keys to comparison rules
SPEC_COMPARISON_MAP = {
    # RAM specs
    "ram.latency_cl": "exact",
    "ram.voltage_v": "numeric_5pct",
    "ram.capacity_gb": "exact",
    "ram.type": "exact",
    "ram.speed_mhz": "numeric_5pct",

    # CPU specs
    "cpu.cores_physical": "exact",
    "cpu.threads_logical": "exact",
    "cpu.base_clock_mhz": "numeric_5pct",
    "cpu.boost_clock_mhz": "numeric_5pct",
    "cpu.tdp_w": "numeric_10pct",
    "cpu.cache_l3_mb": "exact",

    # GPU specs
    "gpu.vram_gb": "exact",
    "gpu.vram_type": "exact",
    "gpu.cuda_cores": "exact",
    "gpu.boost_clock_mhz": "numeric_5pct",
    "gpu.tdp_w": "numeric_10pct",
    "gpu.memory_bus_bits": "exact",

    # Disk specs
    "disk.capacity_gb": "exact",
    "disk.interface": "exact",
    "disk.read_speed_mb": "numeric_10pct",
    "disk.write_speed_mb": "numeric_10pct",

    # Default
    "default": "exact",
}


def _numeric_compare(a: Any, b: Any, tolerance: float) -> bool:
    """Compare two values numerically with tolerance."""
    try:
        # Extract numeric part from strings like "1.1V" or "16 GB"
        a_num = float(''.join(c for c in str(a) if c.isdigit() or c == '.'))
        b_num = float(''.join(c for c in str(b) if c.isdigit() or c == '.'))

        if a_num == 0 and b_num == 0:
            return True
        if a_num == 0 or b_num == 0:
            return False

        diff = abs(a_num - b_num) / max(a_num, b_num)
        return diff <= tolerance
    except (ValueError, ZeroDivisionError):
        return str(a).lower().strip() == str(b).lower().strip()


def _values_match(key: str, val1: Any, val2: Any) -> bool:
    """Check if two values match according to the rules for this key."""
    rule_name = SPEC_COMPARISON_MAP.get(key, SPEC_COMPARISON_MAP["default"])
    rule = COMPARISON_RULES[rule_name]
    return rule(val1, val2)


class CrossValidator:
    """Cross-validates data from multiple web sources."""

    def __init__(
        self,
        scrape_fn: Callable,
        event_callback: Optional[Callable[[Event], None]] = None,
        min_sources_for_validation: int = 2,
        min_confidence_for_persist: float = 0.6,
    ):
        """Initialize cross-validator.

        Args:
            scrape_fn: Function to scrape a URL (spider_name, url, **kwargs) -> List[SpecField]
            event_callback: Optional callback for events
            min_sources_for_validation: Minimum sources needed to validate a spec
            min_confidence_for_persist: Minimum confidence to persist to catalog
        """
        self.scrape_fn = scrape_fn
        self._emit = event_callback or (lambda e: None)
        self.min_sources = min_sources_for_validation
        self.min_confidence = min_confidence_for_persist

    def validate_from_sources(
        self,
        component_input: str,
        component_type: ComponentType,
        sources: List[Tuple[str, str, str]],  # [(source_name, spider_name, url), ...]
        cache=None,
    ) -> CrossValidationResult:
        """Validate component data from multiple sources.

        Args:
            component_input: The raw component input string
            component_type: The classified component type
            sources: List of (source_name, spider_name, url) tuples to try
            cache: Optional cache for scraping

        Returns:
            CrossValidationResult with validated specs
        """
        self._emit(Event.log("info", f"Cross-validating {component_input} from {len(sources)} sources"))

        # Collect results from each source
        source_results: List[SourceResult] = []

        for source_name, spider_name, url in sources:
            self._emit(Event.source_trying(source_name, url))

            try:
                specs = self.scrape_fn(
                    spider_name,
                    url,
                    cache=cache,
                    enable_tier2=True,
                )

                if specs:
                    self._emit(Event.source_success(source_name, len(specs)))
                    source_results.append(SourceResult(
                        source_name=source_name,
                        source_url=url,
                        specs=specs,
                        success=True,
                    ))
                else:
                    self._emit(Event.source_empty(source_name))
                    source_results.append(SourceResult(
                        source_name=source_name,
                        source_url=url,
                        specs=[],
                        success=False,
                        error="No specs extracted",
                    ))

            except Exception as e:
                self._emit(Event.source_failed(source_name, str(e)))
                source_results.append(SourceResult(
                    source_name=source_name,
                    source_url=url,
                    specs=[],
                    success=False,
                    error=str(e),
                ))

        # Find consensus across sources
        validated_specs = self._find_consensus(source_results)

        # Determine if we should persist
        successful_sources = [r for r in source_results if r.success]
        consensus_reached = len(validated_specs) >= 2 and len(successful_sources) >= 2

        avg_confidence = (
            sum(vs.confidence for vs in validated_specs) / len(validated_specs)
            if validated_specs else 0
        )
        should_persist = consensus_reached and avg_confidence >= self.min_confidence

        self._emit(Event.log(
            "info" if consensus_reached else "warning",
            f"Cross-validation: {len(validated_specs)} validated specs, "
            f"consensus={consensus_reached}, persist={should_persist}"
        ))

        return CrossValidationResult(
            component_input=component_input,
            component_type=component_type,
            validated_specs=validated_specs,
            all_source_results=source_results,
            consensus_reached=consensus_reached,
            should_persist=should_persist,
        )

    def _find_consensus(self, source_results: List[SourceResult]) -> List[ValidatedSpec]:
        """Find specs that agree across multiple sources."""
        # Group specs by key across all sources
        specs_by_key: Dict[str, List[Tuple[str, SpecField]]] = defaultdict(list)

        for result in source_results:
            if not result.success:
                continue
            for spec in result.specs:
                specs_by_key[spec.key].append((result.source_name, spec))

        validated: List[ValidatedSpec] = []

        for key, source_specs in specs_by_key.items():
            if len(source_specs) < self.min_sources:
                continue

            # Find groups of matching values
            value_groups: List[List[Tuple[str, SpecField]]] = []

            for source_name, spec in source_specs:
                # Try to find a group this value belongs to
                found_group = False
                for group in value_groups:
                    if _values_match(key, spec.value, group[0][1].value):
                        group.append((source_name, spec))
                        found_group = True
                        break

                if not found_group:
                    value_groups.append([(source_name, spec)])

            # Find the largest group that meets minimum sources
            for group in sorted(value_groups, key=len, reverse=True):
                if len(group) >= self.min_sources:
                    sources = [s for s, _ in group]
                    representative = group[0][1]

                    validated.append(ValidatedSpec(
                        key=key,
                        value=representative.value,
                        sources=sources,
                        confidence=len(sources) / len(source_specs),
                        unit=representative.unit,
                    ))
                    break

        return validated
