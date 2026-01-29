from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

from hardwarextractor.models.schemas import ComponentType, ResolveCandidate, ResolveResult, SourceTier
from hardwarextractor.scrape.spiders import SPIDERS
from hardwarextractor.utils.allowlist import classify_tier, is_allowlisted


def resolve_from_url(input_raw: str, component_type: ComponentType) -> Optional[ResolveResult]:
    if not input_raw.startswith("http"):
        return None
    if not is_allowlisted(input_raw):
        return None

    host = urlparse(input_raw).hostname or ""
    spider_name = _spider_for_domain(host, component_type)
    if not spider_name:
        return None

    spider = SPIDERS[spider_name]
    tier_str = classify_tier(input_raw)
    source_tier = SourceTier.OFFICIAL if tier_str == "OFFICIAL" else SourceTier.REFERENCE

    candidate = ResolveCandidate(
        canonical={"brand": spider.source_name, "model": "URL_INPUT", "part_number": None},
        score=0.99 if source_tier == SourceTier.OFFICIAL else 0.9,
        source_url=input_raw,
        source_name=spider.source_name,
        spider_name=spider_name,
        source_tier=source_tier,
    )
    return ResolveResult(exact=True, candidates=[candidate])


def _spider_for_domain(host: str, component_type: ComponentType) -> Optional[str]:
    domain_matches = []
    for spider_name, spider in SPIDERS.items():
        for domain in spider.allowed_domains:
            if host == domain or host.endswith("." + domain):
                domain_matches.append(spider_name)
    if not domain_matches:
        return None

    if component_type == ComponentType.CPU:
        for name in domain_matches:
            if "cpu" in name or "ark" in name:
                return name
    if component_type == ComponentType.MAINBOARD:
        for name in domain_matches:
            if "mainboard" in name:
                return name
    if component_type == ComponentType.RAM:
        for name in domain_matches:
            if "ram" in name:
                return name
    if component_type == ComponentType.GPU:
        for name in domain_matches:
            if "gpu" in name:
                return name
    if component_type == ComponentType.DISK:
        for name in domain_matches:
            if "storage" in name:
                return name

    return domain_matches[0]
