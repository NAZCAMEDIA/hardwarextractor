from __future__ import annotations

from hardwarextractor.models.schemas import SpecField, SpecStatus, SourceTier
from hardwarextractor.validate.validator import normalize_specs


def test_normalize_units():
    specs = [
        SpecField(
            key="cpu.base_clock_mhz",
            label="",
            value=3.6,
            unit="GHz",
            status=SpecStatus.EXTRACTED_OFFICIAL,
            source_tier=SourceTier.OFFICIAL,
            source_name="Intel",
            source_url="https://intel.com",
            confidence=0.9,
        ),
        SpecField(
            key="ram.capacity_gb",
            label="",
            value=1,
            unit="TB",
            status=SpecStatus.EXTRACTED_OFFICIAL,
            source_tier=SourceTier.OFFICIAL,
            source_name="Kingston",
            source_url="https://kingston.com",
            confidence=0.9,
        ),
    ]
    normalize_specs(specs)
    assert specs[0].value == 3600
    assert specs[0].unit == "MHz"
    assert specs[1].value == 1024
    assert specs[1].unit == "GB"
