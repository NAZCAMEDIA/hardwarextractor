"""Tests for core/source_chain.py - SourceChain system."""

import pytest
from hardwarextractor.core.source_chain import (
    Source,
    SourceType,
    FetchEngine,
    SpecResult,
    SourceChainManager,
    get_source_chain_manager,
    SOURCE_CHAINS,
)
from hardwarextractor.models.schemas import (
    ComponentType,
    ResolveCandidate,
    SourceTier,
    SpecField,
    SpecStatus,
)


class TestSourceType:
    """Test SourceType enum."""

    def test_api_type(self):
        """Test API source type."""
        assert SourceType.API.value == "api"

    def test_scrape_type(self):
        """Test SCRAPE source type."""
        assert SourceType.SCRAPE.value == "scrape"

    def test_catalog_type(self):
        """Test CATALOG source type."""
        assert SourceType.CATALOG.value == "catalog"


class TestFetchEngine:
    """Test FetchEngine enum."""

    def test_requests_engine(self):
        """Test REQUESTS engine."""
        assert FetchEngine.REQUESTS.value == "requests"

    def test_playwright_engine(self):
        """Test PLAYWRIGHT engine."""
        assert FetchEngine.PLAYWRIGHT.value == "playwright"


class TestSource:
    """Test Source dataclass."""

    def test_source_creation(self):
        """Test creating a Source."""
        source = Source(
            name="intel_ark",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="intel",
            engine=FetchEngine.REQUESTS,
            spider_name="intel_ark_spider",
            domains=("intel.com", "ark.intel.com"),
            priority=1,
        )
        assert source.name == "intel_ark"
        assert source.source_type == SourceType.SCRAPE
        assert source.tier == SourceTier.OFFICIAL
        assert source.provider == "intel"
        assert source.engine == FetchEngine.REQUESTS
        assert source.spider_name == "intel_ark_spider"
        assert "intel.com" in source.domains
        assert source.priority == 1

    def test_source_matches_domain(self):
        """Test domain matching."""
        source = Source(
            name="intel",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="intel",
            engine=FetchEngine.REQUESTS,
            domains=("intel.com", "ark.intel.com"),
        )
        assert source.matches_domain("https://ark.intel.com/content/www/us/en/ark.html")
        assert source.matches_domain("https://www.intel.com/products")
        assert not source.matches_domain("https://amd.com/products")

    def test_source_matches_domain_no_domains(self):
        """Test domain matching with no domains defined."""
        source = Source(
            name="generic",
            source_type=SourceType.CATALOG,
            tier=SourceTier.REFERENCE,
            provider="generic",
            engine=FetchEngine.REQUESTS,
            domains=(),
        )
        assert not source.matches_domain("https://example.com")

    def test_source_matches_domain_invalid_url(self):
        """Test domain matching with invalid URL."""
        source = Source(
            name="intel",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="intel",
            engine=FetchEngine.REQUESTS,
            domains=("intel.com",),
        )
        assert not source.matches_domain("not-a-url")

    def test_source_matches_provider(self):
        """Test provider matching."""
        source = Source(
            name="intel_ark",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="intel",
            engine=FetchEngine.REQUESTS,
        )
        assert source.matches_provider("intel_ark_spider")
        assert source.matches_provider("INTEL")
        assert not source.matches_provider("amd")


class TestSpecResult:
    """Test SpecResult dataclass."""

    def test_spec_result_creation(self):
        """Test creating a SpecResult."""
        specs = [
            SpecField(
                key="capacity",
                label="Capacity",
                value="32GB",
                status=SpecStatus.EXTRACTED_OFFICIAL,
            )
        ]
        source = Source(
            name="corsair",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="corsair",
            engine=FetchEngine.REQUESTS,
        )
        result = SpecResult(specs=specs, source=source, engine_used="requests")
        assert result.specs == specs
        assert result.source == source
        assert result.engine_used == "requests"
        assert result.errors == []  # Initialized by __post_init__
        assert result.success is True

    def test_spec_result_empty_specs(self):
        """Test SpecResult with empty specs."""
        result = SpecResult(specs=[], source=None)
        assert result.success is False

    def test_spec_result_errors(self):
        """Test SpecResult with errors."""
        source = Source(
            name="test",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="test",
            engine=FetchEngine.REQUESTS,
        )
        errors = [(source, "Connection timeout")]
        result = SpecResult(specs=[], source=None, errors=errors)
        assert result.errors == errors
        assert result.success is False


class TestSourceChains:
    """Test SOURCE_CHAINS registry."""

    def test_cpu_chain_exists(self):
        """Test CPU chain exists."""
        assert ComponentType.CPU in SOURCE_CHAINS
        assert len(SOURCE_CHAINS[ComponentType.CPU]) > 0

    def test_ram_chain_exists(self):
        """Test RAM chain exists."""
        assert ComponentType.RAM in SOURCE_CHAINS
        assert len(SOURCE_CHAINS[ComponentType.RAM]) > 0

    def test_gpu_chain_exists(self):
        """Test GPU chain exists."""
        assert ComponentType.GPU in SOURCE_CHAINS
        assert len(SOURCE_CHAINS[ComponentType.GPU]) > 0

    def test_mainboard_chain_exists(self):
        """Test MAINBOARD chain exists."""
        assert ComponentType.MAINBOARD in SOURCE_CHAINS
        assert len(SOURCE_CHAINS[ComponentType.MAINBOARD]) > 0

    def test_disk_chain_exists(self):
        """Test DISK chain exists."""
        assert ComponentType.DISK in SOURCE_CHAINS
        assert len(SOURCE_CHAINS[ComponentType.DISK]) > 0

    def test_general_chain_empty(self):
        """Test GENERAL chain is empty."""
        assert ComponentType.GENERAL in SOURCE_CHAINS
        assert len(SOURCE_CHAINS[ComponentType.GENERAL]) == 0


class TestSourceChainManager:
    """Test SourceChainManager class."""

    @pytest.fixture
    def manager(self):
        return SourceChainManager()

    def test_manager_creation(self):
        """Test creating a SourceChainManager."""
        manager = SourceChainManager()
        assert manager is not None

    def test_get_chain_cpu(self, manager):
        """Test getting CPU chain."""
        chain = manager.get_chain(ComponentType.CPU)
        assert len(chain) > 0
        # Intel should be in the list for CPU
        assert any("intel" in s.name.lower() for s in chain)

    def test_get_chain_ram(self, manager):
        """Test getting RAM chain."""
        chain = manager.get_chain(ComponentType.RAM)
        assert len(chain) > 0

    def test_get_chain_gpu(self, manager):
        """Test getting GPU chain."""
        chain = manager.get_chain(ComponentType.GPU)
        assert len(chain) > 0

    def test_get_chain_mainboard(self, manager):
        """Test getting MAINBOARD chain."""
        chain = manager.get_chain(ComponentType.MAINBOARD)
        assert len(chain) > 0

    def test_get_chain_disk(self, manager):
        """Test getting DISK chain."""
        chain = manager.get_chain(ComponentType.DISK)
        assert len(chain) > 0

    def test_get_chain_unknown(self, manager):
        """Test getting chain for GENERAL type."""
        chain = manager.get_chain(ComponentType.GENERAL)
        assert chain == []

    def test_get_reference_sources(self, manager):
        """Test getting reference sources."""
        sources = manager.get_reference_sources(ComponentType.CPU)
        assert all(s.tier == SourceTier.REFERENCE for s in sources)

    def test_get_catalog_source(self, manager):
        """Test getting catalog source."""
        source = manager.get_catalog_source(ComponentType.CPU)
        assert source is not None
        assert source.source_type == SourceType.CATALOG

    def test_mark_domain_blocked(self, manager):
        """Test marking domain as blocked."""
        manager.mark_domain_blocked("example.com")
        assert manager.is_domain_blocked("https://example.com/page") is True

    def test_is_domain_blocked_www(self, manager):
        """Test domain blocking ignores www."""
        manager.mark_domain_blocked("www.example.com")
        assert manager.is_domain_blocked("https://example.com/page") is True

    def test_is_domain_not_blocked(self, manager):
        """Test domain not blocked."""
        assert manager.is_domain_blocked("https://unknown.com") is False

    def test_should_use_playwright_engine(self, manager):
        """Test should_use_playwright based on engine."""
        source = Source(
            name="test",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="corsair",
            engine=FetchEngine.PLAYWRIGHT,
        )
        assert manager.should_use_playwright(source, "https://corsair.com") is True

    def test_should_use_playwright_blocked(self, manager):
        """Test should_use_playwright for blocked domain."""
        source = Source(
            name="test",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="test",
            engine=FetchEngine.REQUESTS,
        )
        manager.mark_domain_blocked("blocked.com")
        assert manager.should_use_playwright(source, "https://blocked.com/page") is True

    def test_should_use_playwright_requests(self, manager):
        """Test should_use_playwright for requests engine."""
        source = Source(
            name="test",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.OFFICIAL,
            provider="test",
            engine=FetchEngine.REQUESTS,
        )
        assert manager.should_use_playwright(source, "https://example.com") is False


class TestSourceChainManagerFindMatching:
    """Test SourceChainManager candidate matching."""

    @pytest.fixture
    def manager(self):
        return SourceChainManager()

    @pytest.fixture
    def intel_candidate(self):
        return ResolveCandidate(
            canonical={"brand": "Intel", "model": "i7-12700K"},
            source_name="Intel ARK",
            source_url="https://ark.intel.com/product/123",
            score=0.95,
            spider_name="intel_ark_spider",
        )

    @pytest.fixture
    def amd_candidate(self):
        return ResolveCandidate(
            canonical={"brand": "AMD", "model": "Ryzen 9"},
            source_name="AMD",
            source_url="https://amd.com/product/456",
            score=0.90,
            spider_name="amd_cpu_specs_spider",
        )

    def test_find_matching_sources(self, manager, intel_candidate):
        """Test finding matching sources."""
        matches = manager.find_matching_sources(
            ComponentType.CPU,
            [intel_candidate]
        )
        assert len(matches) > 0
        # Should find intel source
        source_names = [m[0].name for m in matches]
        assert any("intel" in name.lower() for name in source_names)

    def test_get_source_for_candidate(self, manager, intel_candidate):
        """Test getting source for specific candidate."""
        source = manager.get_source_for_candidate(
            ComponentType.CPU,
            intel_candidate
        )
        assert source is not None
        assert "intel" in source.provider.lower()

    def test_get_source_for_candidate_no_match(self, manager):
        """Test getting source for unknown candidate."""
        unknown = ResolveCandidate(
            canonical={"brand": "Unknown"},
            source_name="Unknown",
            source_url="https://unknown.com",
            score=0.5,
            spider_name="unknown_spider",
        )
        source = manager.get_source_for_candidate(
            ComponentType.CPU,
            unknown
        )
        assert source is None


class TestSourceChainManagerIterate:
    """Test SourceChainManager iterate_chain method."""

    @pytest.fixture
    def manager(self):
        return SourceChainManager()

    def test_iterate_chain(self, manager):
        """Test iterating through chain."""
        candidates = [
            ResolveCandidate(
                canonical={"brand": "Intel"},
                source_name="Intel",
                source_url="https://ark.intel.com/123",
                score=0.9,
                spider_name="intel_ark_spider",
            )
        ]
        results = list(manager.iterate_chain(ComponentType.CPU, candidates))
        assert len(results) > 0
        # Each result is (index, source, matching_candidates)
        for index, source, matching in results:
            assert isinstance(index, int)
            assert isinstance(source, Source)
            assert isinstance(matching, list)

    def test_iterate_chain_skip_catalog(self, manager):
        """Test iterating with skip_catalog."""
        candidates = []
        results_with = list(manager.iterate_chain(ComponentType.CPU, candidates, skip_catalog=False))
        results_without = list(manager.iterate_chain(ComponentType.CPU, candidates, skip_catalog=True))
        # Should have one less when skipping catalog
        assert len(results_without) < len(results_with)


class TestGetSourceChainManager:
    """Test singleton getter."""

    def test_get_manager(self):
        """Test getting singleton manager."""
        manager1 = get_source_chain_manager()
        manager2 = get_source_chain_manager()
        assert manager1 is manager2
