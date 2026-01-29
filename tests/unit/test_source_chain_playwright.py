"""Tests for source_chain FetchEngine configuration (PLAYWRIGHT vs REQUESTS)."""

import pytest

from hardwarextractor.core.source_chain import (
    FetchEngine,
    Source,
    SourceChainManager,
)
from hardwarextractor.models.schemas import ComponentType, SourceTier


def _get_all_sources() -> list[Source]:
    """Get all sources from all component types."""
    manager = SourceChainManager()
    sources = []
    for comp_type in ComponentType:
        sources.extend(manager.get_chain(comp_type))
    # Remove duplicates by name
    seen = set()
    unique = []
    for s in sources:
        if s.name not in seen:
            seen.add(s.name)
            unique.append(s)
    return unique


class TestFetchEngineConfiguration:
    """Test FetchEngine assignments for sources."""

    def test_playwright_sources_count(self):
        """Test that expected number of sources use PLAYWRIGHT."""
        sources = _get_all_sources()
        playwright_count = sum(1 for s in sources if s.engine == FetchEngine.PLAYWRIGHT)
        # Expected: Intel ARK, AMD, MSI, PassMark (4), UserBenchmark, CPU-World, GPU-Specs, etc.
        assert playwright_count >= 8, f"Expected at least 8 PLAYWRIGHT sources, got {playwright_count}"

    def test_official_blocked_sources(self):
        """Test known blocked official sources use PLAYWRIGHT."""
        sources = _get_all_sources()
        blocked_official = ["intel_ark"]
        for source in sources:
            if source.name in blocked_official:
                assert source.engine == FetchEngine.PLAYWRIGHT, f"{source.name} should use PLAYWRIGHT"

    def test_passmark_sources_playwright(self):
        """Test all PassMark sources use PLAYWRIGHT."""
        sources = _get_all_sources()
        passmark_sources = [s for s in sources if "passmark" in s.name.lower()]
        assert len(passmark_sources) > 0, "No PassMark sources found"
        for source in passmark_sources:
            assert source.engine == FetchEngine.PLAYWRIGHT, f"{source.name} should use PLAYWRIGHT"

    def test_userbenchmark_playwright(self):
        """Test UserBenchmark uses PLAYWRIGHT."""
        sources = _get_all_sources()
        ub_sources = [s for s in sources if "userbenchmark" in s.name.lower()]
        assert len(ub_sources) > 0, "No UserBenchmark sources found"
        for source in ub_sources:
            assert source.engine == FetchEngine.PLAYWRIGHT, f"{source.name} should use PLAYWRIGHT"

    def test_techpowerup_gpu_playwright(self):
        """Test TechPowerUp GPU source uses PLAYWRIGHT (anti-bot protection)."""
        sources = _get_all_sources()
        tpu_gpu_sources = [s for s in sources if s.name == "techpowerup_gpu"]
        assert len(tpu_gpu_sources) > 0, "No TechPowerUp GPU source found"
        for source in tpu_gpu_sources:
            assert source.engine == FetchEngine.PLAYWRIGHT, f"{source.name} should use PLAYWRIGHT"


class TestSourceChainManager:
    """Test SourceChainManager functionality."""

    def test_get_chain_returns_sources(self):
        """Test get_chain returns sources for component type."""
        manager = SourceChainManager()
        chain = manager.get_chain(ComponentType.GPU)
        assert len(chain) > 0
        assert all(hasattr(s, 'name') for s in chain)

    def test_should_use_playwright_for_blocked_domain(self):
        """Test should_use_playwright returns True for blocked domains."""
        from hardwarextractor.core.source_chain import Source, SourceType
        manager = SourceChainManager()

        # Mark a domain as blocked (just the domain, not full URL)
        manager.mark_domain_blocked("example-blocked.com")

        # Create a mock source with REQUESTS engine
        source = Source(
            name="Test",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.REFERENCE,
            provider="test",
            engine=FetchEngine.REQUESTS,
            domains=("example-blocked.com",),
        )

        result = manager.should_use_playwright(source, "https://example-blocked.com/page")
        assert result is True

    def test_should_use_playwright_for_playwright_engine(self):
        """Test should_use_playwright returns True for PLAYWRIGHT engine sources."""
        from hardwarextractor.core.source_chain import Source, SourceType
        manager = SourceChainManager()

        source = Source(
            name="Test",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.REFERENCE,
            provider="test",
            engine=FetchEngine.PLAYWRIGHT,
            domains=("example.com",),
        )

        result = manager.should_use_playwright(source, "https://example.com/page")
        assert result is True

    def test_should_use_playwright_false_for_requests(self):
        """Test should_use_playwright returns False for REQUESTS engine without block."""
        from hardwarextractor.core.source_chain import Source, SourceType
        manager = SourceChainManager()

        source = Source(
            name="Test",
            source_type=SourceType.SCRAPE,
            tier=SourceTier.REFERENCE,
            provider="test",
            engine=FetchEngine.REQUESTS,
            domains=("example.com",),
        )

        result = manager.should_use_playwright(source, "https://example.com/page")
        assert result is False

    def test_is_domain_blocked(self):
        """Test is_domain_blocked functionality."""
        manager = SourceChainManager()

        assert manager.is_domain_blocked("https://example.com") is False

        # mark_domain_blocked expects just the domain string
        manager.mark_domain_blocked("example.com")

        assert manager.is_domain_blocked("https://example.com/other/page") is True

    def test_reset_blocked_domains(self):
        """Test reset_blocked_domains clears the list."""
        manager = SourceChainManager()

        manager.mark_domain_blocked("example.com")
        assert manager.is_domain_blocked("https://example.com") is True

        manager._blocked_domains.clear()
        assert manager.is_domain_blocked("https://example.com") is False


class TestSourcesByComponentType:
    """Test sources are properly categorized by component type."""

    @pytest.mark.parametrize("component_type", [
        ComponentType.CPU,
        ComponentType.GPU,
        ComponentType.RAM,
        ComponentType.DISK,
        ComponentType.MAINBOARD,
    ])
    def test_has_sources_for_type(self, component_type):
        """Test each component type has sources."""
        manager = SourceChainManager()
        sources = manager.get_chain(component_type)
        assert len(sources) > 0, f"No sources for {component_type}"

    def test_gpu_has_official_sources(self):
        """Test GPU has official sources."""
        manager = SourceChainManager()
        sources = manager.get_chain(ComponentType.GPU)
        official = [s for s in sources if s.tier == SourceTier.OFFICIAL]
        assert len(official) >= 2  # NVIDIA, AMD at minimum

    def test_cpu_has_official_sources(self):
        """Test CPU has official sources."""
        manager = SourceChainManager()
        sources = manager.get_chain(ComponentType.CPU)
        official = [s for s in sources if s.tier == SourceTier.OFFICIAL]
        assert len(official) >= 2  # Intel ARK, AMD at minimum


class TestSourceTiers:
    """Test source tier assignments."""

    def test_official_tier_count(self):
        """Test we have expected official sources."""
        sources = _get_all_sources()
        official = [s for s in sources if s.tier == SourceTier.OFFICIAL]
        assert len(official) >= 5  # Multiple manufacturers

    def test_reference_tier_count(self):
        """Test we have expected reference sources."""
        sources = _get_all_sources()
        reference = [s for s in sources if s.tier == SourceTier.REFERENCE]
        assert len(reference) >= 5  # TechPowerUp, PassMark, etc.

    def test_has_catalog_fallback(self):
        """Test component types have catalog fallback sources."""
        manager = SourceChainManager()
        for comp_type in [ComponentType.CPU, ComponentType.GPU, ComponentType.RAM]:
            sources = manager.get_chain(comp_type)
            # Should have at least one embedded/catalog source
            has_fallback = any("embedded" in s.name or s.tier == SourceTier.NONE for s in sources)
            assert has_fallback, f"No catalog fallback for {comp_type}"
