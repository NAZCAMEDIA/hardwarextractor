"""Reference URLs for fallback scraping when official sources are blocked.

These are direct product URLs (not search pages) that can be scraped immediately.
TechPowerUp has the most comprehensive GPU/CPU specs in a scrapable format.
"""

from __future__ import annotations

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
CPU_TECHPOWERUP_URLS: Dict[str, str] = {
    # Intel 14th Gen
    "core i9-14900k": "https://www.techpowerup.com/cpu-specs/core-i9-14900k.c3287",
    "core i9-14900kf": "https://www.techpowerup.com/cpu-specs/core-i9-14900kf.c3288",
    "core i7-14700k": "https://www.techpowerup.com/cpu-specs/core-i7-14700k.c3283",
    "core i7-14700kf": "https://www.techpowerup.com/cpu-specs/core-i7-14700kf.c3284",
    "core i5-14600k": "https://www.techpowerup.com/cpu-specs/core-i5-14600k.c3281",
    "core i5-14600kf": "https://www.techpowerup.com/cpu-specs/core-i5-14600kf.c3282",
    # Intel 13th Gen
    "core i9-13900k": "https://www.techpowerup.com/cpu-specs/core-i9-13900k.c3049",
    "core i9-13900kf": "https://www.techpowerup.com/cpu-specs/core-i9-13900kf.c3050",
    "core i9-13900ks": "https://www.techpowerup.com/cpu-specs/core-i9-13900ks.c3122",
    "core i7-13700k": "https://www.techpowerup.com/cpu-specs/core-i7-13700k.c3047",
    "core i7-13700kf": "https://www.techpowerup.com/cpu-specs/core-i7-13700kf.c3048",
    "core i5-13600k": "https://www.techpowerup.com/cpu-specs/core-i5-13600k.c3051",
    "core i5-13600kf": "https://www.techpowerup.com/cpu-specs/core-i5-13600kf.c3052",
    # Intel 12th Gen
    "core i9-12900k": "https://www.techpowerup.com/cpu-specs/core-i9-12900k.c2838",
    "core i9-12900kf": "https://www.techpowerup.com/cpu-specs/core-i9-12900kf.c2836",
    "core i9-12900ks": "https://www.techpowerup.com/cpu-specs/core-i9-12900ks.c2925",
    "core i7-12700k": "https://www.techpowerup.com/cpu-specs/core-i7-12700k.c2835",
    "core i7-12700kf": "https://www.techpowerup.com/cpu-specs/core-i7-12700kf.c2833",
    "core i5-12600k": "https://www.techpowerup.com/cpu-specs/core-i5-12600k.c2834",
    "core i5-12600kf": "https://www.techpowerup.com/cpu-specs/core-i5-12600kf.c2832",
    # AMD Ryzen 9000 Series
    "ryzen 9 9950x": "https://www.techpowerup.com/cpu-specs/ryzen-9-9950x.c3361",
    "ryzen 9 9900x": "https://www.techpowerup.com/cpu-specs/ryzen-9-9900x.c3360",
    "ryzen 7 9700x": "https://www.techpowerup.com/cpu-specs/ryzen-7-9700x.c3359",
    "ryzen 5 9600x": "https://www.techpowerup.com/cpu-specs/ryzen-5-9600x.c3358",
    # AMD Ryzen 7000 Series
    "ryzen 9 7950x": "https://www.techpowerup.com/cpu-specs/ryzen-9-7950x.c3018",
    "ryzen 9 7950x3d": "https://www.techpowerup.com/cpu-specs/ryzen-9-7950x3d.c3101",
    "ryzen 9 7900x": "https://www.techpowerup.com/cpu-specs/ryzen-9-7900x.c3015",
    "ryzen 9 7900x3d": "https://www.techpowerup.com/cpu-specs/ryzen-9-7900x3d.c3102",
    "ryzen 9 7900": "https://www.techpowerup.com/cpu-specs/ryzen-9-7900.c3121",
    "ryzen 7 7800x3d": "https://www.techpowerup.com/cpu-specs/ryzen-7-7800x3d.c3103",
    "ryzen 7 7700x": "https://www.techpowerup.com/cpu-specs/ryzen-7-7700x.c3016",
    "ryzen 7 7700": "https://www.techpowerup.com/cpu-specs/ryzen-7-7700.c3120",
    "ryzen 5 7600x": "https://www.techpowerup.com/cpu-specs/ryzen-5-7600x.c3017",
    "ryzen 5 7600": "https://www.techpowerup.com/cpu-specs/ryzen-5-7600.c3119",
    # AMD Ryzen 5000 Series
    "ryzen 9 5950x": "https://www.techpowerup.com/cpu-specs/ryzen-9-5950x.c2316",
    "ryzen 9 5900x": "https://www.techpowerup.com/cpu-specs/ryzen-9-5900x.c2315",
    "ryzen 9 5900": "https://www.techpowerup.com/cpu-specs/ryzen-9-5900.c2505",
    "ryzen 7 5800x": "https://www.techpowerup.com/cpu-specs/ryzen-7-5800x.c2313",
    "ryzen 7 5800x3d": "https://www.techpowerup.com/cpu-specs/ryzen-7-5800x3d.c2877",
    "ryzen 7 5800": "https://www.techpowerup.com/cpu-specs/ryzen-7-5800.c2506",
    "ryzen 7 5700x": "https://www.techpowerup.com/cpu-specs/ryzen-7-5700x.c2926",
    "ryzen 5 5600x": "https://www.techpowerup.com/cpu-specs/ryzen-5-5600x.c2314",
    "ryzen 5 5600": "https://www.techpowerup.com/cpu-specs/ryzen-5-5600.c2928",
    "ryzen 5 5500": "https://www.techpowerup.com/cpu-specs/ryzen-5-5500.c2944",
}


def get_reference_url(component_type: str, model: str) -> str | None:
    """Get a reference URL for a component.

    Args:
        component_type: "GPU" or "CPU"
        model: The model name (e.g., "GeForce RTX 4090")

    Returns:
        TechPowerUp URL if available, None otherwise
    """
    normalized = model.lower().strip()

    if component_type == "GPU":
        return GPU_TECHPOWERUP_URLS.get(normalized)
    elif component_type == "CPU":
        return CPU_TECHPOWERUP_URLS.get(normalized)

    return None
