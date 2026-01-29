"""Tests for TechPowerUpSpider specialized spider."""

from pathlib import Path

import pytest

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.spiders import SPIDERS, TechPowerUpSpider


FIXTURE_BASE = Path(__file__).resolve().parent.parent / "spiders" / "fixtures"


class TestTechPowerUpSpiderClass:
    """Test TechPowerUpSpider class structure."""

    def test_spider_exists(self):
        """Test that TechPowerUp spiders exist in registry."""
        assert "techpowerup_gpu_spider" in SPIDERS
        assert "techpowerup_cpu_spider" in SPIDERS
        assert "techpowerup_reference_spider" in SPIDERS

    def test_spider_is_techpowerup_class(self):
        """Test that TechPowerUp spiders use specialized class."""
        assert isinstance(SPIDERS["techpowerup_gpu_spider"], TechPowerUpSpider)
        assert isinstance(SPIDERS["techpowerup_cpu_spider"], TechPowerUpSpider)
        assert isinstance(SPIDERS["techpowerup_reference_spider"], TechPowerUpSpider)

    def test_spider_source_tier(self):
        """Test that TechPowerUp spiders are REFERENCE tier."""
        assert SPIDERS["techpowerup_gpu_spider"].source_tier == SourceTier.REFERENCE
        assert SPIDERS["techpowerup_cpu_spider"].source_tier == SourceTier.REFERENCE

    def test_spider_allowed_domains(self):
        """Test allowed domains configuration."""
        spider = SPIDERS["techpowerup_gpu_spider"]
        assert "techpowerup.com" in spider.allowed_domains


class TestTechPowerUpSpiderParsing:
    """Test TechPowerUpSpider HTML parsing."""

    def test_parse_rtx_4090(self):
        """Test parsing RTX 4090 fixture."""
        spider = SPIDERS["techpowerup_gpu_spider"]
        html = (FIXTURE_BASE / "techpowerup_gpu_spider" / "sample.html").read_text()

        specs = spider.parse_html(html, "https://www.techpowerup.com/gpu-specs/geforce-rtx-4090.c3889")

        assert len(specs) >= 8
        keys = {s.key for s in specs}
        assert "gpu_chip" in keys
        assert "cuda_cores" in keys
        assert "vram_gb" in keys

    def test_parse_rtx_3080(self):
        """Test parsing RTX 3080 fixture."""
        spider = SPIDERS["techpowerup_gpu_spider"]
        html = (FIXTURE_BASE / "techpowerup_gpu_spider" / "rtx_3080.html").read_text()

        specs = spider.parse_html(html, "https://www.techpowerup.com/gpu-specs/geforce-rtx-3080.c3621")

        spec_dict = {s.key: s for s in specs}
        assert str(spec_dict["cuda_cores"].value) == "8704"
        assert str(spec_dict["vram_gb"].value) == "10"
        assert str(spec_dict["memory_bus_bits"].value) == "320"

    def test_parse_rx_7900_xtx(self):
        """Test parsing AMD RX 7900 XTX fixture."""
        spider = SPIDERS["techpowerup_gpu_spider"]
        html = (FIXTURE_BASE / "techpowerup_gpu_spider" / "rx_7900_xtx.html").read_text()

        specs = spider.parse_html(html, "https://www.techpowerup.com/gpu-specs/radeon-rx-7900-xtx.c3941")

        spec_dict = {s.key: s for s in specs}
        assert "Navi 31" in spec_dict["gpu_chip"].value
        assert str(spec_dict["cuda_cores"].value) == "12288"
        assert spec_dict["memory_type"].value == "GDDR6"

    def test_parse_empty_html(self):
        """Test parsing empty HTML returns empty list."""
        spider = SPIDERS["techpowerup_gpu_spider"]
        specs = spider.parse_html("<html></html>", "https://example.com")

        assert specs == []

    def test_parse_no_og_description(self):
        """Test parsing HTML without og:description."""
        spider = SPIDERS["techpowerup_gpu_spider"]
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body><p>No specs here</p></body>
        </html>
        """
        specs = spider.parse_html(html, "https://example.com")

        assert specs == []


class TestTechPowerUpSpiderValues:
    """Test specific extracted values."""

    def test_rtx_4090_all_values(self):
        """Test all expected values for RTX 4090."""
        spider = SPIDERS["techpowerup_gpu_spider"]
        html = (FIXTURE_BASE / "techpowerup_gpu_spider" / "sample.html").read_text()

        specs = spider.parse_html(html, "https://techpowerup.com")
        spec_dict = {s.key: s for s in specs}

        expected = {
            "gpu_chip": "NVIDIA AD102",
            "cuda_cores": "16384",
            "tmus": "512",
            "rops": "176",
            "vram_gb": "24",
            "memory_type": "GDDR6X",
            "memory_bus_bits": "384",
            "gpu_clock_mhz": "2520",
            "memory_clock_mhz": "1313",
        }

        for key, expected_value in expected.items():
            assert key in spec_dict, f"Missing spec: {key}"
            # Compare as strings to handle int/str coercion
            assert str(spec_dict[key].value) == expected_value, f"Wrong value for {key}: {spec_dict[key].value} != {expected_value}"

    def test_source_metadata(self):
        """Test source metadata is properly set."""
        spider = SPIDERS["techpowerup_gpu_spider"]
        html = (FIXTURE_BASE / "techpowerup_gpu_spider" / "sample.html").read_text()
        url = "https://www.techpowerup.com/gpu-specs/geforce-rtx-4090.c3889"

        specs = spider.parse_html(html, url)

        for spec in specs:
            assert spec.source_name == "TechPowerUp"
            assert spec.source_url == url
            assert spec.source_tier == SourceTier.REFERENCE


class TestTechPowerUpSpiderCPU:
    """Test TechPowerUp CPU spider (placeholder for future)."""

    def test_cpu_spider_exists(self):
        """Test CPU spider is registered."""
        assert "techpowerup_cpu_spider" in SPIDERS

    def test_cpu_spider_is_techpowerup_class(self):
        """Test CPU spider uses TechPowerUpSpider class."""
        spider = SPIDERS["techpowerup_cpu_spider"]
        assert isinstance(spider, TechPowerUpSpider)

    def test_cpu_spider_source_name(self):
        """Test CPU spider source name."""
        spider = SPIDERS["techpowerup_cpu_spider"]
        assert spider.source_name == "TechPowerUp"
