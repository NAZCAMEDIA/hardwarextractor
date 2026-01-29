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
    # Databases técnicas
    "techpowerup.com",      # GPU/CPU specs database
    "wikichip.org",         # CPU/semiconductor wiki
    "cpu-world.com",        # CPU specifications database
    "gpu-specs.com",        # GPU specifications database
    # Benchmarks con specs
    "cpubenchmark.net",     # PassMark CPU database
    "videocardbenchmark.net",  # PassMark GPU database
    "memorybenchmark.net",  # PassMark RAM database
    "harddrivebenchmark.net",  # PassMark storage database
    "userbenchmark.com",    # Community benchmarks
    # Reviews técnicos
    "tomshardware.com",     # Hardware reviews/specs
    "anandtech.com",        # Technical reviews
    "notebookcheck.net",    # Mobile GPU/CPU specs
    # Tiendas con specs detallados
    "pcpartpicker.com",     # Component database
    "newegg.com",           # Retailer with detailed specs
    # Agregadores
    "pangoly.com",          # Component aggregator
    "nanoreviews.net",      # Spec comparisons
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
