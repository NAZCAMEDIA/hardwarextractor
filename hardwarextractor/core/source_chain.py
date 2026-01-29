"""SourceChain manager for fallback-based data fetching."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Generator, Optional
from urllib.parse import urlparse

from hardwarextractor.core.events import Event
from hardwarextractor.models.schemas import (
    ComponentType,
    ResolveCandidate,
    SourceTier,
    SpecField,
)


class SourceType(str, Enum):
    """Type of data source."""
    API = "api"
    SCRAPE = "scrape"
    CATALOG = "catalog"


class FetchEngine(str, Enum):
    """Engine used to fetch data."""
    REQUESTS = "requests"
    PLAYWRIGHT = "playwright"


@dataclass
class Source:
    """Definition of a data source in the chain.

    Attributes:
        name: Unique identifier for this source
        source_type: Type of source (API, SCRAPE, CATALOG)
        tier: Data tier (OFFICIAL, REFERENCE)
        provider: Provider name (e.g., "intel", "techpowerup")
        engine: Fetch engine to use
        spider_name: Spider name for scraping (optional)
        domains: List of domains this source handles
        priority: Lower = higher priority
        url_template: URL template for search (optional)
    """
    name: str
    source_type: SourceType
    tier: SourceTier
    provider: str
    engine: FetchEngine
    spider_name: Optional[str] = None
    domains: tuple[str, ...] = ()
    priority: int = 50
    url_template: Optional[str] = None

    def matches_domain(self, url: str) -> bool:
        """Check if this source handles the given URL."""
        if not self.domains:
            return False
        try:
            domain = urlparse(url).netloc.lower().replace("www.", "")
            return any(d in domain for d in self.domains)
        except Exception:
            return False

    def matches_provider(self, source_name: str) -> bool:
        """Check if this source matches a provider name."""
        return self.provider.lower() in source_name.lower()


@dataclass
class SpecResult:
    """Result of fetching specs from a source."""
    specs: list[SpecField]
    source: Optional[Source]
    engine_used: Optional[str] = None
    errors: list[tuple[Source, str]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success(self) -> bool:
        return len(self.specs) > 0


# Source definitions for each component type
_CPU_SOURCES = [
    Source(
        name="intel_ark",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="intel",
        engine=FetchEngine.REQUESTS,
        spider_name="intel_ark_spider",
        domains=("intel.com", "ark.intel.com"),
        priority=1,
    ),
    Source(
        name="amd_specs",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="amd",
        engine=FetchEngine.REQUESTS,
        spider_name="amd_cpu_specs_spider",
        domains=("amd.com",),
        priority=2,
    ),
    Source(
        name="wikichip",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="wikichip",
        engine=FetchEngine.REQUESTS,
        spider_name="wikichip_reference_spider",
        domains=("wikichip.org",),
        priority=3,
    ),
    Source(
        name="techpowerup_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="techpowerup",
        engine=FetchEngine.REQUESTS,
        spider_name="techpowerup_reference_spider",
        domains=("techpowerup.com",),
        priority=4,
    ),
    Source(
        name="embedded_cpu",
        source_type=SourceType.CATALOG,
        tier=SourceTier.NONE,
        provider="local",
        engine=FetchEngine.REQUESTS,
        priority=99,
    ),
]

_RAM_SOURCES = [
    Source(
        name="crucial",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="crucial",
        engine=FetchEngine.REQUESTS,
        spider_name="crucial_ram_spider",
        domains=("crucial.com", "micron.com"),
        priority=1,
    ),
    Source(
        name="kingston",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="kingston",
        engine=FetchEngine.REQUESTS,
        spider_name="kingston_ram_spider",
        domains=("kingston.com",),
        priority=2,
    ),
    Source(
        name="corsair",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="corsair",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="corsair_ram_spider",
        domains=("corsair.com",),
        priority=3,
    ),
    Source(
        name="gskill",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="gskill",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="gskill_ram_spider",
        domains=("gskill.com",),
        priority=4,
    ),
    Source(
        name="techpowerup_ram",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="techpowerup",
        engine=FetchEngine.REQUESTS,
        spider_name="techpowerup_reference_spider",
        domains=("techpowerup.com",),
        priority=5,
    ),
    Source(
        name="embedded_ram",
        source_type=SourceType.CATALOG,
        tier=SourceTier.NONE,
        provider="local",
        engine=FetchEngine.REQUESTS,
        priority=99,
    ),
]

_GPU_SOURCES = [
    Source(
        name="techpowerup_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="techpowerup",
        engine=FetchEngine.REQUESTS,
        spider_name="techpowerup_reference_spider",
        domains=("techpowerup.com",),
        priority=1,  # Best source for GPUs
    ),
    Source(
        name="nvidia_official",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="nvidia",
        engine=FetchEngine.REQUESTS,
        spider_name="nvidia_gpu_chip_spider",
        domains=("nvidia.com",),
        priority=2,
    ),
    Source(
        name="amd_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="amd",
        engine=FetchEngine.REQUESTS,
        spider_name="amd_gpu_chip_spider",
        domains=("amd.com",),
        priority=3,
    ),
    Source(
        name="intel_arc",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="intel",
        engine=FetchEngine.REQUESTS,
        spider_name="intel_arc_gpu_chip_spider",
        domains=("intel.com",),
        priority=4,
    ),
    Source(
        name="asus_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="asus",
        engine=FetchEngine.REQUESTS,
        spider_name="asus_gpu_aib_spider",
        domains=("asus.com",),
        priority=5,
    ),
    Source(
        name="embedded_gpu",
        source_type=SourceType.CATALOG,
        tier=SourceTier.NONE,
        provider="local",
        engine=FetchEngine.REQUESTS,
        priority=99,
    ),
]

_MAINBOARD_SOURCES = [
    Source(
        name="asus_mb",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="asus",
        engine=FetchEngine.REQUESTS,
        spider_name="asus_mainboard_spider",
        domains=("asus.com",),
        priority=1,
    ),
    Source(
        name="msi_mb",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="msi",
        engine=FetchEngine.REQUESTS,
        spider_name="msi_mainboard_spider",
        domains=("msi.com",),
        priority=2,
    ),
    Source(
        name="gigabyte_mb",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="gigabyte",
        engine=FetchEngine.REQUESTS,
        spider_name="gigabyte_mainboard_spider",
        domains=("gigabyte.com",),
        priority=3,
    ),
    Source(
        name="asrock_mb",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="asrock",
        engine=FetchEngine.REQUESTS,
        spider_name="asrock_mainboard_spider",
        domains=("asrock.com",),
        priority=4,
    ),
    Source(
        name="embedded_mb",
        source_type=SourceType.CATALOG,
        tier=SourceTier.NONE,
        provider="local",
        engine=FetchEngine.REQUESTS,
        priority=99,
    ),
]

_DISK_SOURCES = [
    Source(
        name="samsung_storage",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="samsung",
        engine=FetchEngine.REQUESTS,
        spider_name="samsung_storage_spider",
        domains=("samsung.com", "semiconductor.samsung.com"),
        priority=1,
    ),
    Source(
        name="wdc_storage",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="wdc",
        engine=FetchEngine.REQUESTS,
        spider_name="wdc_storage_spider",
        domains=("wdc.com", "westerndigital.com", "sandisk.com"),
        priority=2,
    ),
    Source(
        name="seagate_storage",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="seagate",
        engine=FetchEngine.REQUESTS,
        spider_name="seagate_storage_spider",
        domains=("seagate.com",),
        priority=3,
    ),
    Source(
        name="techpowerup_ssd",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="techpowerup",
        engine=FetchEngine.REQUESTS,
        spider_name="techpowerup_reference_spider",
        domains=("techpowerup.com",),
        priority=4,
    ),
    Source(
        name="embedded_disk",
        source_type=SourceType.CATALOG,
        tier=SourceTier.NONE,
        provider="local",
        engine=FetchEngine.REQUESTS,
        priority=99,
    ),
]

# Main source chain registry
SOURCE_CHAINS: dict[ComponentType, list[Source]] = {
    ComponentType.CPU: _CPU_SOURCES,
    ComponentType.RAM: _RAM_SOURCES,
    ComponentType.GPU: _GPU_SOURCES,
    ComponentType.MAINBOARD: _MAINBOARD_SOURCES,
    ComponentType.DISK: _DISK_SOURCES,
    ComponentType.GENERAL: [],  # No specific sources for general
}


class SourceChainManager:
    """Manages the source chain and fallback logic."""

    def __init__(self):
        self._blocked_domains: set[str] = set()

    def get_chain(self, component_type: ComponentType) -> list[Source]:
        """Get the source chain for a component type."""
        return SOURCE_CHAINS.get(component_type, [])

    def find_matching_sources(
        self,
        component_type: ComponentType,
        candidates: list[ResolveCandidate]
    ) -> list[tuple[Source, list[ResolveCandidate]]]:
        """Find sources that match the candidates.

        Returns list of (source, matching_candidates) tuples.
        """
        chain = self.get_chain(component_type)
        results = []

        for source in chain:
            if source.source_type == SourceType.CATALOG:
                # Catalog always matches as last resort
                results.append((source, candidates))
                continue

            matching = []
            for candidate in candidates:
                if source.matches_domain(candidate.source_url):
                    matching.append(candidate)
                elif source.matches_provider(candidate.source_name):
                    matching.append(candidate)

            if matching:
                results.append((source, matching))

        return results

    def get_source_for_candidate(
        self,
        component_type: ComponentType,
        candidate: ResolveCandidate
    ) -> Optional[Source]:
        """Get the best source for a specific candidate."""
        chain = self.get_chain(component_type)

        for source in chain:
            if source.source_type == SourceType.CATALOG:
                continue
            if source.matches_domain(candidate.source_url):
                return source
            if source.matches_provider(candidate.source_name):
                return source

        return None

    def get_reference_sources(self, component_type: ComponentType) -> list[Source]:
        """Get reference sources for fallback."""
        chain = self.get_chain(component_type)
        return [s for s in chain if s.tier == SourceTier.REFERENCE]

    def get_catalog_source(self, component_type: ComponentType) -> Optional[Source]:
        """Get the catalog (embedded) source."""
        chain = self.get_chain(component_type)
        for source in chain:
            if source.source_type == SourceType.CATALOG:
                return source
        return None

    def mark_domain_blocked(self, domain: str) -> None:
        """Mark a domain as blocked (anti-bot detected)."""
        self._blocked_domains.add(domain.lower().replace("www.", ""))

    def is_domain_blocked(self, url: str) -> bool:
        """Check if a domain is known to be blocked."""
        try:
            domain = urlparse(url).netloc.lower().replace("www.", "")
            return domain in self._blocked_domains
        except Exception:
            return False

    def should_use_playwright(self, source: Source, url: str) -> bool:
        """Determine if Playwright should be used for this request."""
        if source.engine == FetchEngine.PLAYWRIGHT:
            return True
        if self.is_domain_blocked(url):
            return True
        return False

    def iterate_chain(
        self,
        component_type: ComponentType,
        candidates: list[ResolveCandidate],
        skip_catalog: bool = False
    ) -> Generator[tuple[int, Source, list[ResolveCandidate]], None, None]:
        """Iterate through the source chain with matching candidates.

        Yields: (index, source, matching_candidates) tuples
        """
        chain = self.get_chain(component_type)
        total = len(chain) - (1 if skip_catalog else 0)

        for i, source in enumerate(chain):
            if skip_catalog and source.source_type == SourceType.CATALOG:
                continue

            # Find matching candidates for this source
            if source.source_type == SourceType.CATALOG:
                matching = candidates
            else:
                matching = [
                    c for c in candidates
                    if source.matches_domain(c.source_url)
                    or source.matches_provider(c.source_name)
                ]

            yield (i + 1, source, matching)


# Singleton instance
_manager: Optional[SourceChainManager] = None


def get_source_chain_manager() -> SourceChainManager:
    """Get the singleton SourceChainManager instance."""
    global _manager
    if _manager is None:
        _manager = SourceChainManager()
    return _manager
