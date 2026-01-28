from __future__ import annotations

from urllib.parse import urlparse


OFFICIAL_DOMAINS = {
    "intel.com",
    "amd.com",
    "apple.com",
    "nvidia.com",
    "asus.com",
    "msi.com",
    "gigabyte.com",
    "asrock.com",
    "supermicro.com",
    "biostar.com",
    "kingston.com",
    "crucial.com",
    "micron.com",
    "corsair.com",
    "gskill.com",
    "teamgroupinc.com",
    "patriotmemory.com",
    "adata.com",
    "lexar.com",
    "samsung.com",
    "semiconductors.samsung.com",
    "wdc.com",
    "western-digital.com",
    "sandisk.com",
    "seagate.com",
    "toshiba-storage.com",
    "kioxia.com",
    "realtek.com",
    "broadcom.com",
    "marvell.com",
}

REFERENCE_DOMAINS = {
    "techpowerup.com",
    "wikichip.org",
}

DISCOVERY_DOMAINS = {
    "google.com",
    "duckduckgo.com",
}


def _domain_matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def is_allowlisted(url: str) -> bool:
    host = urlparse(url).hostname or ""
    for domain in OFFICIAL_DOMAINS | REFERENCE_DOMAINS:
        if _domain_matches(host, domain):
            return True
    return False


def classify_tier(url: str) -> str:
    host = urlparse(url).hostname or ""
    for domain in OFFICIAL_DOMAINS:
        if _domain_matches(host, domain):
            return "OFFICIAL"
    for domain in REFERENCE_DOMAINS:
        if _domain_matches(host, domain):
            return "REFERENCE"
    return "NONE"
