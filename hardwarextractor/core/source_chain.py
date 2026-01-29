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
    errors: Optional[list[tuple[Source, str]]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success(self) -> bool:
        return len(self.specs) > 0


# Source definitions for each component type
_CPU_SOURCES = [
    # Official sources (Tier 1)
    Source(
        name="intel_ark",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="intel",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="intel_ark_spider",
        domains=("intel.com", "ark.intel.com"),
        priority=1,
    ),
    Source(
        name="amd_specs",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="amd",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="amd_cpu_specs_spider",
        domains=("amd.com",),
        priority=2,
    ),
    # Reference sources - Technical databases (Tier 2)
    Source(
        name="techpowerup_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="techpowerup",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection requires JS
        spider_name="techpowerup_cpu_spider",
        domains=("techpowerup.com",),
        priority=10,
        url_template="https://www.techpowerup.com/cpu-specs/?ajaxsrch={query}",
    ),
    Source(
        name="wikichip",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="wikichip",
        engine=FetchEngine.REQUESTS,
        spider_name="wikichip_reference_spider",
        domains=("wikichip.org",),
        priority=11,
        url_template="https://en.wikichip.org/w/index.php?search={query}",
    ),
    Source(
        name="cpu_world",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="cpu-world",
        engine=FetchEngine.PLAYWRIGHT,  # 403 Forbidden without JS
        spider_name="cpu_world_spider",
        domains=("cpu-world.com",),
        priority=12,
        url_template="https://www.cpu-world.com/cgi-bin/search.pl?search={query}",
    ),
    # Reference sources - Benchmarks (Tier 2)
    Source(
        name="passmark_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="passmark",
        engine=FetchEngine.PLAYWRIGHT,  # 403 Forbidden without JS
        spider_name="passmark_cpu_spider",
        domains=("cpubenchmark.net",),
        priority=20,
        url_template="https://www.cpubenchmark.net/cpu_list.php",
    ),
    Source(
        name="userbenchmark_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="userbenchmark",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="userbenchmark_spider",
        domains=("userbenchmark.com",),
        priority=21,
        url_template="https://cpu.userbenchmark.com/Search?searchTerm={query}",
    ),
    # Reference sources - Reviews (Tier 2)
    Source(
        name="tomshardware_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="tomshardware",
        engine=FetchEngine.REQUESTS,
        spider_name="tomshardware_spider",
        domains=("tomshardware.com",),
        priority=30,
        url_template="https://www.tomshardware.com/search?searchTerm={query}",
    ),
    Source(
        name="anandtech_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="anandtech",
        engine=FetchEngine.REQUESTS,
        spider_name="anandtech_spider",
        domains=("anandtech.com",),
        priority=31,
        url_template="https://www.anandtech.com/SearchResult?search={query}",
    ),
    Source(
        name="notebookcheck_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="notebookcheck",
        engine=FetchEngine.REQUESTS,
        spider_name="notebookcheck_spider",
        domains=("notebookcheck.net",),
        priority=32,
        url_template="https://www.notebookcheck.net/Mobile-Processors-Benchmark-List.2436.0.html?search={query}",
    ),
    # Reference sources - Retailers/Aggregators (Tier 2)
    Source(
        name="pcpartpicker_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="pcpartpicker",
        engine=FetchEngine.REQUESTS,
        spider_name="pcpartpicker_spider",
        domains=("pcpartpicker.com",),
        priority=40,
        url_template="https://pcpartpicker.com/search/?q={query}",
    ),
    Source(
        name="newegg_cpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="newegg",
        engine=FetchEngine.REQUESTS,
        spider_name="newegg_spider",
        domains=("newegg.com",),
        priority=41,
    ),
    # Embedded catalog (last resort)
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
    # Official sources (Tier 1)
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
    # Reference sources - Benchmarks (Tier 2)
    Source(
        name="passmark_ram",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="passmark",
        engine=FetchEngine.PLAYWRIGHT,  # 403 Forbidden without JS
        spider_name="passmark_ram_spider",
        domains=("memorybenchmark.net",),
        priority=10,
        url_template="https://www.memorybenchmark.net/ram_list.php",
    ),
    Source(
        name="userbenchmark_ram",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="userbenchmark",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="userbenchmark_spider",
        domains=("userbenchmark.com",),
        priority=11,
        url_template="https://ram.userbenchmark.com/Search?searchTerm={query}",
    ),
    # Reference sources - Retailers/Aggregators (Tier 2)
    Source(
        name="pcpartpicker_ram",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="pcpartpicker",
        engine=FetchEngine.REQUESTS,
        spider_name="pcpartpicker_spider",
        domains=("pcpartpicker.com",),
        priority=20,
        url_template="https://pcpartpicker.com/search/?q={query}",
    ),
    Source(
        name="newegg_ram",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="newegg",
        engine=FetchEngine.REQUESTS,
        spider_name="newegg_spider",
        domains=("newegg.com",),
        priority=21,
        url_template="https://www.newegg.com/p/pl?d={query}",
    ),
    Source(
        name="pangoly_ram",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="pangoly",
        engine=FetchEngine.REQUESTS,
        spider_name="pangoly_spider",
        domains=("pangoly.com",),
        priority=22,
        url_template="https://pangoly.com/en/review/search?q={query}",
    ),
    # Embedded catalog (last resort)
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
    # Official sources (Tier 1)
    Source(
        name="nvidia_official",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="nvidia",
        engine=FetchEngine.REQUESTS,
        spider_name="nvidia_gpu_chip_spider",
        domains=("nvidia.com",),
        priority=1,
    ),
    Source(
        name="amd_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="amd",
        engine=FetchEngine.REQUESTS,
        spider_name="amd_gpu_chip_spider",
        domains=("amd.com",),
        priority=2,
    ),
    Source(
        name="intel_arc",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="intel",
        engine=FetchEngine.REQUESTS,
        spider_name="intel_arc_gpu_chip_spider",
        domains=("intel.com",),
        priority=3,
    ),
    Source(
        name="asus_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.OFFICIAL,
        provider="asus",
        engine=FetchEngine.REQUESTS,
        spider_name="asus_gpu_aib_spider",
        domains=("asus.com",),
        priority=4,
    ),
    # Reference sources - Technical databases (Tier 2) - BEST for GPUs
    Source(
        name="techpowerup_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="techpowerup",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection requires JS
        spider_name="techpowerup_gpu_spider",
        domains=("techpowerup.com",),
        priority=10,  # Best detailed GPU database
        url_template="https://www.techpowerup.com/gpu-specs/?ajaxsrch={query}",
    ),
    Source(
        name="gpu_specs",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="gpu-specs",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="gpu_specs_spider",
        domains=("gpu-specs.com",),
        priority=11,
        url_template="https://www.gpu-specs.com/search.php?search={query}",
    ),
    # Reference sources - Benchmarks (Tier 2)
    Source(
        name="passmark_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="passmark",
        engine=FetchEngine.PLAYWRIGHT,  # 403 Forbidden without JS
        spider_name="passmark_gpu_spider",
        domains=("videocardbenchmark.net",),
        priority=20,
        url_template="https://www.videocardbenchmark.net/gpu_list.php",
    ),
    Source(
        name="userbenchmark_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="userbenchmark",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="userbenchmark_spider",
        domains=("userbenchmark.com",),
        priority=21,
        url_template="https://gpu.userbenchmark.com/Search?searchTerm={query}",
    ),
    # Reference sources - Reviews (Tier 2)
    Source(
        name="tomshardware_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="tomshardware",
        engine=FetchEngine.REQUESTS,
        spider_name="tomshardware_spider",
        domains=("tomshardware.com",),
        priority=30,
        url_template="https://www.tomshardware.com/search?searchTerm={query}",
    ),
    Source(
        name="notebookcheck_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="notebookcheck",
        engine=FetchEngine.REQUESTS,
        spider_name="notebookcheck_spider",
        domains=("notebookcheck.net",),
        priority=31,
        url_template="https://www.notebookcheck.net/Mobile-Graphics-Cards-Benchmark-List.2963.0.html?search={query}",
    ),
    # Reference sources - Retailers/Aggregators (Tier 2)
    Source(
        name="pcpartpicker_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="pcpartpicker",
        engine=FetchEngine.REQUESTS,
        spider_name="pcpartpicker_spider",
        domains=("pcpartpicker.com",),
        priority=40,
        url_template="https://pcpartpicker.com/search/?q={query}",
    ),
    Source(
        name="newegg_gpu",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="newegg",
        engine=FetchEngine.REQUESTS,
        spider_name="newegg_spider",
        domains=("newegg.com",),
        priority=41,
    ),
    # Embedded catalog (last resort)
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
    # Official sources (Tier 1)
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
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection (403)
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
    # Reference sources - Retailers/Aggregators (Tier 2)
    Source(
        name="pcpartpicker_mb",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="pcpartpicker",
        engine=FetchEngine.REQUESTS,
        spider_name="pcpartpicker_spider",
        domains=("pcpartpicker.com",),
        priority=10,
        url_template="https://pcpartpicker.com/search/?q={query}",
    ),
    Source(
        name="newegg_mb",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="newegg",
        engine=FetchEngine.REQUESTS,
        spider_name="newegg_spider",
        domains=("newegg.com",),
        priority=11,
        url_template="https://www.newegg.com/p/pl?d={query}",
    ),
    Source(
        name="pangoly_mb",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="pangoly",
        engine=FetchEngine.REQUESTS,
        spider_name="pangoly_spider",
        domains=("pangoly.com",),
        priority=12,
        url_template="https://pangoly.com/en/review/search?q={query}",
    ),
    # Reference sources - Reviews (Tier 2)
    Source(
        name="tomshardware_mb",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="tomshardware",
        engine=FetchEngine.REQUESTS,
        spider_name="tomshardware_spider",
        domains=("tomshardware.com",),
        priority=20,
        url_template="https://www.tomshardware.com/search?searchTerm={query}",
    ),
    # Embedded catalog (last resort)
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
    # Official sources (Tier 1)
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
    # Reference sources - Benchmarks (Tier 2)
    Source(
        name="passmark_disk",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="passmark",
        engine=FetchEngine.PLAYWRIGHT,  # 403 Forbidden without JS
        spider_name="passmark_disk_spider",
        domains=("harddrivebenchmark.net",),
        priority=10,
        url_template="https://www.harddrivebenchmark.net/hdd_list.php",
    ),
    Source(
        name="userbenchmark_disk",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="userbenchmark",
        engine=FetchEngine.PLAYWRIGHT,  # Anti-bot protection
        spider_name="userbenchmark_spider",
        domains=("userbenchmark.com",),
        priority=11,
        url_template="https://ssd.userbenchmark.com/Search?searchTerm={query}",
    ),
    # Reference sources - Technical (Tier 2)
    Source(
        name="techpowerup_ssd",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="techpowerup",
        engine=FetchEngine.REQUESTS,
        spider_name="techpowerup_reference_spider",
        domains=("techpowerup.com",),
        priority=12,
        url_template="https://www.techpowerup.com/ssd-specs/?ajaxsrch={query}",
    ),
    # Reference sources - Retailers/Aggregators (Tier 2)
    Source(
        name="pcpartpicker_disk",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="pcpartpicker",
        engine=FetchEngine.REQUESTS,
        spider_name="pcpartpicker_spider",
        domains=("pcpartpicker.com",),
        priority=20,
        url_template="https://pcpartpicker.com/search/?q={query}",
    ),
    Source(
        name="newegg_disk",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="newegg",
        engine=FetchEngine.REQUESTS,
        spider_name="newegg_spider",
        domains=("newegg.com",),
        priority=21,
        url_template="https://www.newegg.com/p/pl?d={query}",
    ),
    # Reference sources - Reviews (Tier 2)
    Source(
        name="tomshardware_disk",
        source_type=SourceType.SCRAPE,
        tier=SourceTier.REFERENCE,
        provider="tomshardware",
        engine=FetchEngine.REQUESTS,
        spider_name="tomshardware_spider",
        domains=("tomshardware.com",),
        priority=30,
        url_template="https://www.tomshardware.com/search?searchTerm={query}",
    ),
    # Embedded catalog (last resort)
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
