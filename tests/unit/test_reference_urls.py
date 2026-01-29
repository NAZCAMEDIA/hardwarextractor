"""Tests for data/reference_urls.py - Reference URL catalog."""

import pytest

from hardwarextractor.data.reference_urls import (
    GPU_TECHPOWERUP_URLS,
    CPU_TECHPOWERUP_URLS,
    get_reference_url,
)


class TestGPUUrls:
    """Test GPU reference URLs."""

    def test_gpu_urls_dict_exists(self):
        """Test that GPU_TECHPOWERUP_URLS is defined."""
        assert GPU_TECHPOWERUP_URLS is not None
        assert isinstance(GPU_TECHPOWERUP_URLS, dict)

    def test_gpu_urls_has_rtx_4090(self):
        """Test RTX 4090 is in catalog."""
        assert "geforce rtx 4090" in GPU_TECHPOWERUP_URLS
        assert "techpowerup.com" in GPU_TECHPOWERUP_URLS["geforce rtx 4090"]

    def test_gpu_urls_has_amd_cards(self):
        """Test AMD cards are in catalog."""
        assert "radeon rx 7900 xtx" in GPU_TECHPOWERUP_URLS
        assert "radeon rx 6800 xt" in GPU_TECHPOWERUP_URLS

    def test_gpu_urls_has_intel_arc(self):
        """Test Intel Arc cards are in catalog."""
        assert "arc a770" in GPU_TECHPOWERUP_URLS
        assert "arc a750" in GPU_TECHPOWERUP_URLS


class TestCPUUrls:
    """Test CPU reference URLs.

    NOTE: CPU_TECHPOWERUP_URLS is currently empty because the TechPowerUp
    URL IDs were incorrect (e.g., c3287 pointed to Ryzen Z1 instead of i9-14900K).
    Tests are updated to reflect this until correct URLs are discovered.
    """

    def test_cpu_urls_dict_exists(self):
        """Test that CPU_TECHPOWERUP_URLS is defined."""
        assert CPU_TECHPOWERUP_URLS is not None
        assert isinstance(CPU_TECHPOWERUP_URLS, dict)

    def test_cpu_urls_is_empty(self):
        """Test CPU URLs is currently empty (IDs were incorrect)."""
        # CPU URLs are disabled until we verify correct TechPowerUp IDs
        assert len(CPU_TECHPOWERUP_URLS) == 0


class TestGetReferenceUrl:
    """Test get_reference_url function."""

    def test_get_gpu_url_exact_match(self):
        """Test getting GPU URL with exact match."""
        url = get_reference_url("GPU", "geforce rtx 4090")
        assert url is not None
        assert "techpowerup.com" in url
        assert "4090" in url

    def test_get_gpu_url_case_insensitive(self):
        """Test GPU URL lookup is case insensitive."""
        url = get_reference_url("GPU", "GeForce RTX 4090")
        assert url is not None

    def test_get_gpu_url_with_spaces(self):
        """Test GPU URL lookup trims spaces."""
        url = get_reference_url("GPU", "  geforce rtx 4090  ")
        assert url is not None

    def test_get_cpu_url_returns_none(self):
        """Test CPU URL returns None (URLs disabled due to incorrect IDs)."""
        # CPU TechPowerUp URLs are currently disabled
        url = get_reference_url("CPU", "core i9-14900k")
        assert url is None

    def test_get_url_not_found(self):
        """Test getting URL for unknown model."""
        url = get_reference_url("GPU", "unknown gpu model xyz")
        assert url is None

    def test_get_url_invalid_type(self):
        """Test getting URL with invalid component type."""
        url = get_reference_url("RAM", "ddr5 6000")
        assert url is None

    def test_get_url_empty_model(self):
        """Test getting URL with empty model returns None."""
        # Empty model should return None, not match anything
        url = get_reference_url("GPU", "")
        assert url is None

    def test_get_url_rtx_30_series(self):
        """Test RTX 30 series URLs."""
        assert get_reference_url("GPU", "geforce rtx 3090") is not None
        assert get_reference_url("GPU", "geforce rtx 3080") is not None
        assert get_reference_url("GPU", "geforce rtx 3070") is not None

    def test_get_url_radeon_rx_6000(self):
        """Test RX 6000 series URLs."""
        assert get_reference_url("GPU", "radeon rx 6900 xt") is not None
        assert get_reference_url("GPU", "radeon rx 6800") is not None
        assert get_reference_url("GPU", "radeon rx 6700 xt") is not None


class TestUrlFormat:
    """Test URL format validity."""

    def test_gpu_urls_are_valid_format(self):
        """Test all GPU URLs have valid format."""
        for model, url in GPU_TECHPOWERUP_URLS.items():
            assert url.startswith("https://"), f"URL for {model} should use https"
            assert "techpowerup.com" in url, f"URL for {model} should be techpowerup"

    def test_cpu_urls_are_valid_format(self):
        """Test all CPU URLs have valid format."""
        for model, url in CPU_TECHPOWERUP_URLS.items():
            assert url.startswith("https://"), f"URL for {model} should use https"
            assert "techpowerup.com" in url, f"URL for {model} should be techpowerup"
