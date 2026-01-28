from __future__ import annotations

from typing import List

from hardwarextractor.models.schemas import SpecField, SpecStatus


class ValidationError(Exception):
    pass


def validate_specs(specs: List[SpecField]) -> None:
    normalize_specs(specs)
    for spec in specs:
        if spec.status in {SpecStatus.UNKNOWN, SpecStatus.NA}:
            continue
        if not spec.source_url or not spec.source_tier:
            raise ValidationError(f"Spec {spec.key} missing source provenance")


def normalize_specs(specs: List[SpecField]) -> None:
    for spec in specs:
        if spec.value is None:
            continue
        if isinstance(spec.value, (int, float)) and spec.unit:
            unit = spec.unit.lower()
            if spec.key.endswith("_mhz") and unit in {"ghz"}:
                spec.value = round(float(spec.value) * 1000, 2)
                spec.unit = "MHz"
            if spec.key.endswith("_mt_s") and unit in {"mt/s", "mts"}:
                spec.unit = "MT/s"
            if spec.key.endswith("_gb") and unit in {"tb"}:
                spec.value = round(float(spec.value) * 1024, 2)
                spec.unit = "GB"
