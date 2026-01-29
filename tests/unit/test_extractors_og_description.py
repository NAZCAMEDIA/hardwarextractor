"""Tests for parse_og_description_specs extractor (TechPowerUp new format)."""

import pytest
from parsel import Selector

from hardwarextractor.models.schemas import SourceTier, SpecStatus
from hardwarextractor.scrape.extractors import parse_og_description_specs


class TestParseOgDescriptionSpecs:
    """Test og:description spec extraction for TechPowerUp's new format."""

    def test_rtx_4090_full_specs(self):
        """Test extraction from RTX 4090 og:description."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA AD102, 2520 MHz, 16384 Cores, 512 TMUs, 176 ROPs, 24576 MB GDDR6X, 1313 MHz, 384 bit" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com/gpu-specs/rtx-4090", SourceTier.REFERENCE
        )

        assert len(specs) >= 8, f"Expected at least 8 specs, got {len(specs)}"

        keys = {s.key for s in specs}
        assert "gpu_chip" in keys
        assert "cuda_cores" in keys
        assert "tmus" in keys
        assert "rops" in keys
        assert "vram_gb" in keys
        assert "memory_type" in keys
        assert "memory_bus_bits" in keys
        assert "gpu_clock_mhz" in keys

    def test_rtx_4090_values(self):
        """Test specific values extracted from RTX 4090."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA AD102, 2520 MHz, 16384 Cores, 512 TMUs, 176 ROPs, 24576 MB GDDR6X, 1313 MHz, 384 bit" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}

        # Values can be int or str after coercion
        assert str(spec_dict["cuda_cores"].value) == "16384"
        assert str(spec_dict["tmus"].value) == "512"
        assert str(spec_dict["rops"].value) == "176"
        assert str(spec_dict["vram_gb"].value) == "24"  # 24576 MB -> 24 GB
        assert spec_dict["memory_type"].value == "GDDR6X"
        assert str(spec_dict["memory_bus_bits"].value) == "384"
        assert spec_dict["memory_bus_bits"].unit == "bit"

    def test_amd_gpu_navi_chip(self):
        """Test AMD Navi chip detection."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="AMD Navi 31, 2499 MHz, 12288 Cores, 384 TMUs, 192 ROPs, 24576 MB GDDR6, 1250 MHz, 384 bit" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}

        # AMD chip should be detected
        assert "gpu_chip" in spec_dict
        assert "Navi 31" in spec_dict["gpu_chip"].value

        # AMD uses GDDR6 (not GDDR6X)
        assert spec_dict["memory_type"].value == "GDDR6"

    def test_intel_arc_chip(self):
        """Test Intel Arc chip detection."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="Intel ACM-G10, 2100 MHz, 4096 Cores, 128 TMUs, 64 ROPs, 16384 MB GDDR6, 1093 MHz, 256 bit" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}

        assert "gpu_chip" in spec_dict
        assert "Intel" in spec_dict["gpu_chip"].value

    def test_no_og_description(self):
        """Test handling of missing og:description."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Some Page" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        assert specs == []

    def test_empty_og_description(self):
        """Test handling of empty og:description."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        assert specs == []

    def test_non_gpu_og_description(self):
        """Test handling of non-GPU og:description content."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="TechPowerUp is a website about computer hardware." />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        # Should return empty or minimal specs since no GPU-related content
        assert len(specs) == 0 or all(s.key == "gpu_chip" for s in specs)

    def test_memory_gb_conversion(self):
        """Test MB to GB conversion for VRAM."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA AD102, 2520 MHz, 16384 Cores, 512 TMUs, 176 ROPs, 8192 MB GDDR6X, 1313 MHz, 256 bit" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}
        assert str(spec_dict["vram_gb"].value) == "8"  # 8192 MB = 8 GB
        assert spec_dict["vram_gb"].unit == "GB"

    def test_dual_clock_speeds(self):
        """Test detection of GPU and memory clock speeds."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA AD102, 2520 MHz, 16384 Cores, 512 TMUs, 176 ROPs, 24576 MB GDDR6X, 1313 MHz, 384 bit" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}

        # First MHz should be GPU clock
        assert "gpu_clock_mhz" in spec_dict
        assert str(spec_dict["gpu_clock_mhz"].value) == "2520"

        # Second MHz should be memory clock
        assert "memory_clock_mhz" in spec_dict
        assert str(spec_dict["memory_clock_mhz"].value) == "1313"

    def test_source_metadata(self):
        """Test that source metadata is properly set."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA AD102, 2520 MHz, 16384 Cores" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com/gpu-specs/rtx-4090", SourceTier.REFERENCE
        )

        for spec in specs:
            assert spec.source_name == "TechPowerUp"
            assert spec.source_url == "https://techpowerup.com/gpu-specs/rtx-4090"
            assert spec.source_tier == SourceTier.REFERENCE
            assert spec.status == SpecStatus.EXTRACTED_REFERENCE

    def test_rtx_30_series(self):
        """Test RTX 30 series GPU extraction."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA GA102, 1710 MHz, 8704 Cores, 272 TMUs, 96 ROPs, 10240 MB GDDR6X, 1188 MHz, 320 bit" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}

        assert str(spec_dict["cuda_cores"].value) == "8704"
        assert str(spec_dict["vram_gb"].value) == "10"  # 10240 MB = 10 GB
        assert str(spec_dict["memory_bus_bits"].value) == "320"

    def test_low_end_gpu(self):
        """Test low-end GPU with smaller values."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA AD107, 2475 MHz, 2048 Cores, 64 TMUs, 32 ROPs, 8192 MB GDDR6, 2000 MHz, 128 bit" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}

        assert str(spec_dict["cuda_cores"].value) == "2048"
        assert str(spec_dict["tmus"].value) == "64"
        assert str(spec_dict["rops"].value) == "32"
        assert str(spec_dict["memory_bus_bits"].value) == "128"


class TestParseOgDescriptionEdgeCases:
    """Edge cases and error handling for og:description parsing."""

    def test_case_insensitive_matching(self):
        """Test case-insensitive matching for keywords."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="nvidia AD102, 2520 mhz, 16384 CORES, 512 tmus, 176 ROPS, 24576 mb gddr6x, 1313 mhz, 384 BIT" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        keys = {s.key for s in specs}
        assert "cuda_cores" in keys
        assert "tmus" in keys
        assert "rops" in keys

    def test_extra_whitespace(self):
        """Test handling of extra whitespace in values."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA AD102,   2520 MHz,  16384  Cores ,  512  TMUs" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        assert len(specs) >= 3

    def test_gb_memory_format(self):
        """Test GB memory format instead of MB."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="NVIDIA AD102, 2520 MHz, 16384 Cores, 24 GB GDDR6X" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}
        assert str(spec_dict["vram_gb"].value) == "24"

    def test_rdna_chip_detection(self):
        """Test RDNA chip architecture detection."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="AMD RDNA 3, 2500 MHz, 6144 Cores" />
        </head>
        </html>
        """
        selector = Selector(text=html)
        specs = parse_og_description_specs(
            selector, "TechPowerUp", "https://techpowerup.com", SourceTier.REFERENCE
        )

        spec_dict = {s.key: s for s in specs}
        assert "gpu_chip" in spec_dict
        assert "RDNA" in spec_dict["gpu_chip"].value
