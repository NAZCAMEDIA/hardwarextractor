from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

from parsel import Selector

from hardwarextractor.models.schemas import SpecField, SpecStatus, SourceTier
from hardwarextractor.scrape.jsonld import extract_jsonld_pairs


def parse_data_spec_fields(selector: Selector, source_name: str, source_url: str, source_tier: SourceTier) -> List[SpecField]:
    fields: List[SpecField] = []
    for node in selector.css("[data-spec-key]"):
        key = node.attrib.get("data-spec-key")
        value = node.attrib.get("data-spec-value") or node.xpath("string()").get(default="").strip()
        unit = node.attrib.get("data-spec-unit")
        label = node.attrib.get("data-spec-label", key)
        if not key:
            continue
        fields.append(
            _field_from_value(
                key=key,
                label=label,
                value=value,
                unit=unit,
                source_name=source_name,
                source_url=source_url,
                source_tier=source_tier,
            )
        )
    return fields


def parse_labeled_fields(
    selector: Selector,
    label_map: Dict[str, str],
    source_name: str,
    source_url: str,
    source_tier: SourceTier,
) -> List[SpecField]:
    fields: List[SpecField] = []
    for label, value in _extract_label_value_pairs(selector):
        key = label_map.get(_normalize_label(label))
        if not key:
            continue
        fields.append(
            _field_from_value(
                key=key,
                label=label,
                value=value,
                unit=None,
                source_name=source_name,
                source_url=source_url,
                source_tier=source_tier,
            )
        )
    return fields


def _extract_label_value_pairs(selector: Selector) -> Iterable[Tuple[str, str]]:
    # Table rows
    for row in selector.css("table tr"):
        label = row.css("th::text").get() or row.css("td:nth-child(1)::text").get()
        value = row.css("td:nth-child(2)::text").get()
        if not value:
            value = row.css("td:nth-child(2) ::text").get()
        if label and value:
            yield label.strip(), value.strip()

    # Definition lists
    for node in selector.css("dl"):
        labels = [t.get().strip() for t in node.css("dt::text")]
        values = [t.get().strip() for t in node.css("dd::text")]
        for label, value in zip(labels, values):
            if label and value:
                yield label, value

    # Definition list variant with nested spans
    for node in selector.css("dl"):
        labels = [t.get().strip() for t in node.css("dt span::text")]
        values = [t.get().strip() for t in node.css("dd span::text")]
        for label, value in zip(labels, values):
            if label and value:
                yield label, value

    # Label: value lists
    for item in selector.css("li"):
        text = item.xpath("string()").get(default="").strip()
        if ":" in text:
            label, value = text.split(":", 1)
            if label.strip() and value.strip():
                yield label.strip(), value.strip()

    # data-label + data-value attributes
    for node in selector.css("[data-label][data-value]"):
        label = node.attrib.get("data-label")
        value = node.attrib.get("data-value")
        if label and value:
            yield label.strip(), value.strip()

    # data-spec-name + data-spec-value attributes (common in product pages)
    for node in selector.css("[data-spec-name][data-spec-value]"):
        label = node.attrib.get("data-spec-name")
        value = node.attrib.get("data-spec-value")
        if label and value:
            yield label.strip(), value.strip()

    # data-spec-label + data-spec-value attributes
    for node in selector.css("[data-spec-label][data-spec-value]"):
        label = node.attrib.get("data-spec-label")
        value = node.attrib.get("data-spec-value")
        if label and value:
            yield label.strip(), value.strip()

    # class-based label/value pairs
    for node in selector.css(".specs__row, .spec-row, .specs-row, .spec-row"):
        label = node.css(".specs__label::text, .spec-label::text, .label::text").get()
        value = node.css(".specs__value::text, .spec-value::text, .value::text").get()
        if label and value:
            yield label.strip(), value.strip()

    # dt/dd with data-title/data-value
    for node in selector.css("[data-title][data-value]"):
        label = node.attrib.get("data-title")
        value = node.attrib.get("data-value")
        if label and value:
            yield label.strip(), value.strip()

    # colon-separated blocks in spec containers
    for node in selector.css(".specs, .specifications, .product-specs, .techspecs"):
        text = node.xpath("string()").get(default="").strip()
        for line in text.splitlines():
            if ":" in line:
                label, value = line.split(":", 1)
                if label.strip() and value.strip():
                    yield label.strip(), value.strip()

    # JSON-LD additionalProperty pairs
    for label, value in extract_jsonld_pairs(selector):
        yield label.strip(), value.strip()


def _normalize_label(label: str) -> str:
    label = label.strip().lower()
    label = re.sub(r"\s+", " ", label)
    label = re.sub(r"[^a-z0-9 /-]", "", label)
    return label


def _coerce_value(value: str):
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return value
    value_clean = value.replace(",", "")
    try:
        if "." in value_clean:
            return float(value_clean)
        return int(value_clean)
    except ValueError:
        return value


def _field_from_value(
    key: str,
    label: str,
    value: str,
    unit: str | None,
    source_name: str,
    source_url: str,
    source_tier: SourceTier,
) -> SpecField:
    value_coerced = _coerce_value(value)
    if isinstance(value_coerced, str) and value_coerced.upper() in {"UNKNOWN", "NA"}:
        status = SpecStatus.UNKNOWN if value_coerced.upper() == "UNKNOWN" else SpecStatus.NA
        return SpecField(
            key=key,
            label=label,
            value=value_coerced.upper(),
            unit=unit,
            status=status,
            source_tier=SourceTier.NONE,
            source_name=None,
            source_url=None,
            confidence=0.0,
        )

    unit_normalized = unit
    value_normalized = value_coerced
    if isinstance(value_coerced, str):
        pcie_parsed = _parse_pcie_value(key, value_coerced)
        if pcie_parsed is not None:
            value_normalized, unit_normalized = pcie_parsed
        lanes_parsed = _parse_lanes_value(key, value_coerced)
        if lanes_parsed is not None:
            value_normalized, unit_normalized = lanes_parsed
        ddr_parsed = _parse_ddr_speed(key, value_coerced)
        if ddr_parsed is not None:
            value_normalized, unit_normalized = ddr_parsed
    if unit_normalized is None and isinstance(value_coerced, str) and _should_parse_numeric(key):
        parsed = _extract_numeric_with_unit(value_coerced)
        if parsed:
            value_normalized, unit_normalized = parsed

    return SpecField(
        key=key,
        label=label,
        value=value_normalized,
        unit=unit_normalized,
        status=SpecStatus.EXTRACTED_OFFICIAL if source_tier == SourceTier.OFFICIAL else SpecStatus.EXTRACTED_REFERENCE,
        source_tier=source_tier,
        source_name=source_name,
        source_url=source_url,
        confidence=0.9 if source_tier == SourceTier.OFFICIAL else 0.75,
    )


_NUMERIC_SUFFIXES = (
    "_mhz",
    "_mt_s",
    "_gb",
    "_mb",
    "_bits",
    "_gbps",
    "_mbps",
    "_v",
)


def _should_parse_numeric(key: str) -> bool:
    return key.endswith(_NUMERIC_SUFFIXES)


def _extract_numeric_with_unit(raw: str):
    normalized = raw.replace("-", " ")
    normalized = normalized.replace(",", "")
    normalized = normalized.replace("up to", "").replace("upto", "")
    normalized = normalized.replace("about", "")
    pattern = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/]+|bit|bits)?", re.IGNORECASE)
    matches = list(pattern.finditer(normalized))
    if not matches:
        return None
    last = matches[-1]
    value = float(last.group(1)) if "." in last.group(1) else int(last.group(1))
    unit = last.group(2) or None
    if unit is None and "ddr" in normalized.lower():
        unit = "MT/s"
    if unit:
        unit = unit.lower()
        unit = unit.replace("per", "/").replace("sec", "s")
        unit = unit.replace("bits", "bit")
        unit = unit.replace("gbs", "gb/s").replace("gb/s", "gb/s")
        unit = unit.replace("mb/s", "mb/s")
        unit = unit.replace("mbps", "mb/s")
        unit = unit.replace("gbps", "gb/s")
        unit = unit.replace("mt/s", "mt/s")
        unit = unit.replace("ghz", "ghz")
        unit = unit.replace("mhz", "mhz")
        unit = unit.replace("gb", "gb")
        unit = unit.replace("mb", "mb")
        unit = unit.replace("bit", "bit")
        unit = _normalize_unit_case(unit)
    return value, unit


def _parse_pcie_value(key: str, raw: str):
    if "pcie" not in key and "pci" not in key:
        return None
    text = raw.lower()
    version_match = re.search(r"(?:pcie|pci express)\s*([0-9]+(?:\.[0-9]+)?)", text)
    lanes_match = re.search(r"x\s*([0-9]+)", text)
    if "version" in key and version_match:
        return (float(version_match.group(1)) if "." in version_match.group(1) else version_match.group(1), None)
    if "lanes" in key and lanes_match:
        return (int(lanes_match.group(1)), None)
    return None


def _parse_lanes_value(key: str, raw: str):
    if "lanes" not in key:
        return None
    text = raw.lower()
    lanes_match = re.search(r"x\s*([0-9]+)", text)
    if lanes_match:
        return (int(lanes_match.group(1)), None)
    lanes_match = re.search(r"([0-9]+)\s*lanes", text)
    if lanes_match:
        return (int(lanes_match.group(1)), None)
    return None


def _parse_ddr_speed(key: str, raw: str):
    if not key.endswith("_mt_s"):
        return None
    text = raw.lower().replace(" ", "")
    match = re.search(r"ddr[3-6][-]?([0-9]{3,5})", text)
    if match:
        return (int(match.group(1)), "MT/s")
    match = re.search(r"([0-9]{3,5})\\s*mt/s", raw.lower())
    if match:
        return (int(match.group(1)), "MT/s")
    return None


def _normalize_unit_case(unit: str) -> str:
    mapping = {
        "gb/s": "GB/s",
        "mb/s": "MB/s",
        "mt/s": "MT/s",
        "ghz": "GHz",
        "mhz": "MHz",
        "gb": "GB",
        "mb": "MB",
        "bit": "bit",
        "v": "V",
    }
    return mapping.get(unit, unit)
