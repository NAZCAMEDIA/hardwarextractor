from __future__ import annotations

import pytest

from hardwarextractor.models.schemas import SpecField, SpecStatus, SourceTier
from hardwarextractor.validate.validator import ValidationError, validate_specs


def test_validator_requires_provenance():
    spec = SpecField(
        key="cpu.cores_physical",
        label="cores",
        value=8,
        status=SpecStatus.EXTRACTED_OFFICIAL,
        source_tier=SourceTier.OFFICIAL,
        source_name="Intel",
        source_url=None,
        confidence=0.9,
    )
    with pytest.raises(ValidationError):
        validate_specs([spec])
