"""Reference URLs for fallback scraping when official sources are blocked.

These are direct product URLs (not search pages) that can be scraped immediately.
TechPowerUp has the most comprehensive GPU/CPU specs in a scrapable format.
"""

from __future__ import annotations

import re
from typing import Dict

# GPU reference URLs from TechPowerUp
# Format: model_normalized -> techpowerup_url
GPU_TECHPOWERUP_URLS: Dict[str, str] = {
    # NVIDIA RTX 40 Series
    "geforce rtx 4090": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4090.c3889",
    "geforce rtx 4080 super": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4080-super.c4174",
    "geforce rtx 4080": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4080.c3888",
    "geforce rtx 4070 ti super": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4070-ti-super.c4175",
    "geforce rtx 4070 ti": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4070-ti.c3950",
    "geforce rtx 4070 super": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4070-super.c4173",
    "geforce rtx 4070": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4070.c4004",
    "geforce rtx 4060 ti": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4060-ti.c4042",
    "geforce rtx 4060": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4060.c4043",
    # NVIDIA RTX 30 Series
    "geforce rtx 3090 ti": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3090-ti.c3829",
    "geforce rtx 3090": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3090.c3622",
    "geforce rtx 3080 ti": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3080-ti.c3735",
    "geforce rtx 3080": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3080.c3621",
    "geforce rtx 3070 ti": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3070-ti.c3675",
    "geforce rtx 3070": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3070.c3674",
    "geforce rtx 3060 ti": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3060-ti.c3681",
    "geforce rtx 3060": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3060-12-gb.c3682",
    "geforce rtx 3050": "https://www.techpowerup.com/gpu-specs/geforce-rtx-3050.c3858",
    # AMD RX 7000 Series
    "radeon rx 7900 xtx": "https://www.techpowerup.com/gpu-specs/radeon-rx-7900-xtx.c3941",
    "radeon rx 7900 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-7900-xt.c3912",
    "radeon rx 7900 gre": "https://www.techpowerup.com/gpu-specs/radeon-rx-7900-gre.c4038",
    "radeon rx 7800 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-7800-xt.c4055",
    "radeon rx 7700 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-7700-xt.c4056",
    "radeon rx 7600 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-7600-xt.c4177",
    "radeon rx 7600": "https://www.techpowerup.com/gpu-specs/radeon-rx-7600.c4037",
    # AMD RX 6000 Series
    "radeon rx 6950 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-6950-xt.c3899",
    "radeon rx 6900 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-6900-xt.c3481",
    "radeon rx 6800 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-6800-xt.c3694",
    "radeon rx 6800": "https://www.techpowerup.com/gpu-specs/radeon-rx-6800.c3693",
    "radeon rx 6750 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-6750-xt.c3898",
    "radeon rx 6700 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-6700-xt.c3695",
    "radeon rx 6650 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-6650-xt.c3897",
    "radeon rx 6600 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-6600-xt.c3774",
    "radeon rx 6600": "https://www.techpowerup.com/gpu-specs/radeon-rx-6600.c3696",
    "radeon rx 6500 xt": "https://www.techpowerup.com/gpu-specs/radeon-rx-6500-xt.c3850",
    "radeon rx 6400": "https://www.techpowerup.com/gpu-specs/radeon-rx-6400.c3765",
    # Intel Arc
    "arc a770": "https://www.techpowerup.com/gpu-specs/arc-a770.c3914",
    "arc a750": "https://www.techpowerup.com/gpu-specs/arc-a750.c3913",
    "arc a580": "https://www.techpowerup.com/gpu-specs/arc-a580.c4057",
    "arc a380": "https://www.techpowerup.com/gpu-specs/arc-a380.c3900",
    "arc a310": "https://www.techpowerup.com/gpu-specs/arc-a310.c3946",
}

# CPU reference URLs from TechPowerUp
# NOTE: TechPowerUp has changed their site structure and IDs are now incorrect.
# This dictionary is empty until we can verify and update the URLs.
# For now, CPU fallback will use the internal catalog.
CPU_TECHPOWERUP_URLS: Dict[str, str] = {}


def _normalize_model_for_lookup(model: str, component_type: str) -> str:
    """Normalize a model name for dictionary lookup.

    Handles variations like:
    - "Intel Core i9-14900K" -> "core i9-14900k"
    - "i9-14900K" -> "core i9-14900k"
    - "NVIDIA GeForce RTX 4090" -> "geforce rtx 4090"
    - "RTX 4090" -> "geforce rtx 4090"
    """
    normalized = model.lower().strip()

    if component_type == "CPU":
        # Remove brand prefixes
        normalized = re.sub(r'^(intel\s+|amd\s+)', '', normalized)

        # For Intel, ensure "core" prefix exists
        if re.search(r'^i[3579]-?\d{4,5}', normalized):
            normalized = "core " + normalized

        # Normalize i9-14900k to i9-14900k (with hyphen)
        normalized = re.sub(r'(i[3579])\s+(\d)', r'\1-\2', normalized)

    elif component_type == "GPU":
        # Remove brand prefixes
        normalized = re.sub(r'^(nvidia\s+|amd\s+|intel\s+)', '', normalized)

        # For NVIDIA, ensure "geforce" prefix exists for RTX/GTX
        if re.match(r'^(rtx|gtx)\s+\d', normalized):
            normalized = "geforce " + normalized

        # For AMD, ensure "radeon" prefix exists for RX
        if re.match(r'^rx\s+\d', normalized):
            normalized = "radeon " + normalized

    return normalized


def get_reference_url(component_type: str, model: str) -> str | None:
    """Get a reference URL for a component.

    Args:
        component_type: "GPU" or "CPU"
        model: The model name (e.g., "GeForce RTX 4090", "Intel Core i9-14900K")

    Returns:
        TechPowerUp URL if available, None otherwise
    """
    if not model or not model.strip():
        return None

    normalized = _normalize_model_for_lookup(model, component_type)
    if not normalized:
        return None

    if component_type == "GPU":
        # Try exact match first
        if url := GPU_TECHPOWERUP_URLS.get(normalized):
            return url

        # Try without "geforce"/"radeon" prefix
        for key, url in GPU_TECHPOWERUP_URLS.items():
            if normalized in key or key in normalized:
                return url

    elif component_type == "CPU":
        # Try exact match first
        if url := CPU_TECHPOWERUP_URLS.get(normalized):
            return url

        # Try partial matching for CPUs
        for key, url in CPU_TECHPOWERUP_URLS.items():
            # Check if key model number matches (e.g., "14900k" in both)
            model_match = re.search(r'(i[3579][-\s]?\d{4,5}[a-z]*|ryzen\s+\d\s+\d{4}[a-z0-9]*)', normalized)
            key_match = re.search(r'(i[3579][-\s]?\d{4,5}[a-z]*|ryzen\s+\d\s+\d{4}[a-z0-9]*)', key)
            if model_match and key_match:
                # Normalize both matches for comparison
                model_num = model_match.group(1).replace(' ', '-').replace('--', '-')
                key_num = key_match.group(1).replace(' ', '-').replace('--', '-')
                if model_num == key_num:
                    return url

    return None
