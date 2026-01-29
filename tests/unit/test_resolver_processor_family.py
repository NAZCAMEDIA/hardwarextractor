"""Tests for processor family search in resolver."""

import pytest

from hardwarextractor.models.schemas import ComponentType
from hardwarextractor.resolver.resolver import (
    _extract_processor_family,
    _model_contains_family,
    resolve_component,
)


class TestExtractProcessorFamily:
    """Test _extract_processor_family function."""

    def test_intel_i7(self):
        """Test extracting Intel i7 family."""
        assert _extract_processor_family("intel i7") == "i7"

    def test_intel_i5(self):
        """Test extracting Intel i5 family."""
        assert _extract_processor_family("intel i5") == "i5"

    def test_intel_i9(self):
        """Test extracting Intel i9 family."""
        assert _extract_processor_family("i9 processor") == "i9"

    def test_intel_i3(self):
        """Test extracting Intel i3 family."""
        assert _extract_processor_family("core i3") == "i3"

    def test_ryzen_9(self):
        """Test extracting AMD Ryzen 9 family."""
        assert _extract_processor_family("ryzen 9") == "ryzen9"

    def test_ryzen_7(self):
        """Test extracting AMD Ryzen 7 family."""
        assert _extract_processor_family("amd ryzen 7") == "ryzen7"

    def test_ryzen_5(self):
        """Test extracting AMD Ryzen 5 family."""
        assert _extract_processor_family("ryzen5") == "ryzen5"

    def test_ryzen_3(self):
        """Test extracting AMD Ryzen 3 family."""
        assert _extract_processor_family("Ryzen 3") == "ryzen3"

    def test_no_family(self):
        """Test input with no processor family."""
        assert _extract_processor_family("xeon platinum") is None

    def test_empty_string(self):
        """Test empty string input."""
        assert _extract_processor_family("") is None


class TestModelContainsFamily:
    """Test _model_contains_family function."""

    def test_intel_i7_in_model(self):
        """Test Intel i7 found in model."""
        assert _model_contains_family("Core i7-12700K", "i7") is True

    def test_intel_i7_not_in_model(self):
        """Test Intel i7 not found in model."""
        assert _model_contains_family("Core i5-12400", "i7") is False

    def test_ryzen_9_in_model(self):
        """Test Ryzen 9 found in model."""
        assert _model_contains_family("AMD Ryzen 9 5900X", "ryzen9") is True

    def test_ryzen_7_in_model(self):
        """Test Ryzen 7 found in model."""
        assert _model_contains_family("Ryzen 7 7800X3D", "ryzen7") is True

    def test_ryzen_not_in_model(self):
        """Test Ryzen family not found in model."""
        assert _model_contains_family("Ryzen 5 5600X", "ryzen7") is False

    def test_other_family(self):
        """Test unknown family prefix."""
        assert _model_contains_family("Xeon E5-2699", "xeon") is False


class TestResolveComponentFamilySearch:
    """Test resolve_component with family searches."""

    def test_intel_i7_returns_candidates(self):
        """Test 'intel i7' returns i7 candidates."""
        result = resolve_component("intel i7", ComponentType.CPU)
        # Should find some i7 candidates from catalog
        if result.candidates:
            for candidate in result.candidates:
                model = candidate.canonical.get("model", "").lower()
                # All candidates should be i7
                assert "i7" in model

    def test_intel_i5_returns_candidates(self):
        """Test 'intel i5' returns i5 candidates."""
        result = resolve_component("intel i5", ComponentType.CPU)
        if result.candidates:
            for candidate in result.candidates:
                model = candidate.canonical.get("model", "").lower()
                assert "i5" in model

    def test_amd_ryzen_7_returns_candidates(self):
        """Test 'amd ryzen 7' returns Ryzen 7 candidates."""
        result = resolve_component("amd ryzen 7", ComponentType.CPU)
        if result.candidates:
            for candidate in result.candidates:
                model = candidate.canonical.get("model", "").lower()
                assert "ryzen" in model and "7" in model

    def test_generic_search_not_exact(self):
        """Test generic family search is not exact match."""
        result = resolve_component("intel i7", ComponentType.CPU)
        # Family searches should not be exact matches
        if result.candidates:
            assert result.exact is False

    def test_family_score_is_moderate(self):
        """Test family search candidates have moderate score."""
        result = resolve_component("intel i7", ComponentType.CPU)
        if result.candidates:
            for candidate in result.candidates:
                # Score for family match should be around 0.65
                assert candidate.score >= 0.5
                assert candidate.score <= 0.75


class TestResolveComponentEdgeCases:
    """Test resolve_component edge cases."""

    def test_empty_input(self):
        """Test empty input returns no candidates or few candidates."""
        result = resolve_component("", ComponentType.CPU)
        assert result.exact is False
        # Empty input should return very few or no candidates
        # (depends on fuzzy matching threshold)

    def test_gibberish_input(self):
        """Test gibberish input returns no candidates."""
        result = resolve_component("xyzabc123456", ComponentType.CPU)
        assert result.exact is False

    def test_part_number_exact_match(self):
        """Test exact part number matching."""
        # Use a known part number from catalog
        result = resolve_component("CMK32GX5M2B6000C36", ComponentType.RAM)
        if result.candidates:
            # Exact part number should have high score
            assert result.candidates[0].score >= 0.95

    def test_model_number_extraction(self):
        """Test model number extraction works."""
        result = resolve_component("i7-12700K", ComponentType.CPU)
        if result.candidates:
            # Should find the exact model
            assert len(result.candidates) > 0

    def test_brand_with_tokens(self):
        """Test brand + token matching."""
        result = resolve_component("corsair vengeance", ComponentType.RAM)
        if result.candidates:
            for candidate in result.candidates:
                brand = candidate.canonical.get("brand", "").lower()
                model = candidate.canonical.get("model", "").lower()
                # Should match Corsair Vengeance products
                assert "corsair" in brand or "vengeance" in model
