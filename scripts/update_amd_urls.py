#!/usr/bin/env python3
"""Update AMD URLs in enrichment_index to use TechPowerUp."""

from __future__ import annotations

import json
from pathlib import Path

# Manual mapping of AMD CPU models to TechPowerUp URLs
# Format: "Model Name": "TechPowerUp URL suffix"
AMD_MODEL_TO_TPU = {
    # Zen 4 (Ryzen 7000)
    "Ryzen 9 7950X": "ryzen-9-7950x.c28798",
    "Ryzen 9 7950X3D": "ryzen-9-7950x3d.c3022",
    "Ryzen 9 7900X": "ryzen-9-7900x.c28799",
    "Ryzen 9 7900X3D": "ryzen-9-7900x3d.c3021",
    "Ryzen 9 7900": "ryzen-9-7900.c3055",
    "Ryzen 7 7800X3D": "ryzen-7-7800x3d.c3022",
    "Ryzen 7 7700X": "ryzen-7-7700x.c28800",
    "Ryzen 7 7700": "ryzen-7-7700.c3056",
    "Ryzen 5 7600X": "ryzen-5-7600x.c28801",
    "Ryzen 5 7600": "ryzen-5-7600.c3057",
    "Ryzen 5 7500F": "ryzen-5-7500f.c3259",
    # Zen 3 (Ryzen 5000)
    "Ryzen 9 5950X": "ryzen-9-5950x.c2364",
    "Ryzen 9 5900X": "ryzen-9-5900x.c2363",
    "Ryzen 9 5900": "ryzen-9-5900.c2774",
    "Ryzen 9 3900X": "ryzen-9-3900x.c2128",
    "Ryzen 9 3900": "ryzen-9-3900.c2419",
    "Ryzen 7 5800X3D": "ryzen-7-5800x3d.c2532",
    "Ryzen 7 5800X": "ryzen-7-5800x.c2362",
    "Ryzen 7 5800": "ryzen-7-5800.c2418",
    "Ryzen 7 5700X": "ryzen-7-5700x.c2755",
    "Ryzen 7 5700G": "ryzen-7-5700g.c2472",
    "Ryzen 7 5700": "ryzen-7-5700.c3305",
    "Ryzen 7 3700X": "ryzen-7-3700x.c2130",
    "Ryzen 7 2700X": "ryzen-7-2700x.c2011",
    "Ryzen 5 5600X": "ryzen-5-5600x.c2365",
    "Ryzen 5 5600G": "ryzen-5-5600g.c2471",
    "Ryzen 5 5600": "ryzen-5-5600.c2743",
    "Ryzen 5 5600GT": "ryzen-5-5600gt.c3438",
    "Ryzen 5 5500": "ryzen-5-5500.c2756",
    "Ryzen 5 3600X": "ryzen-5-3600x.c2131",
    "Ryzen 5 3600": "ryzen-5-3600.c2132",
    "Ryzen 5 3500X": "ryzen-5-3500x.c2264",
    "Ryzen 5 3400G": "ryzen-5-3400g.c2204",
    "Ryzen 5 2600": "ryzen-5-2600.c2015",
    "Ryzen 5 2400G": "ryzen-5-2400g.c1976",
    "Ryzen 3 3200G": "ryzen-3-3200g.c2205",
    "Ryzen 3 2200G": "ryzen-3-2200g.c1978",
    # Zen 2 (Ryzen 3000)
    "Ryzen 9 3950X": "ryzen-9-3950x.c2103",
    "Ryzen 9 3900X": "ryzen-9-3900x.c2128",
    "Ryzen 7 3800X": "ryzen-7-3800x.c2129",
    "Ryzen 7 3700X": "ryzen-7-3700x.c2130",
    "Ryzen 5 3600X": "ryzen-5-3600x.c2131",
    "Ryzen 5 3600": "ryzen-5-3600.c2132",
    "Ryzen 5 3400G": "ryzen-5-3400g.c2204",
    "Ryzen 3 3200G": "ryzen-3-3200g.c2205",
    # Threadripper
    "Ryzen Threadripper PRO 5995WX": "ryzen-threadripper-pro-5995wx.c2480",
    "Ryzen Threadripper PRO 5975WX": "ryzen-threadripper-pro-5975wx.c2481",
    "Ryzen Threadripper PRO 5965WX": "ryzen-threadripper-pro-5965wx.c2482",
    "Ryzen Threadripper 3990X": "ryzen-threadripper-3990x.c2056",
    "Ryzen Threadripper 3970X": "ryzen-threadripper-3970x.c2057",
    "Ryzen Threadripper 3960X": "ryzen-threadripper-3960x.c2058",
    # Zen 4c/APU
    "Ryzen 7 8700G": "ryzen-7-8700g.c3042",
    "Ryzen 5 8600G": "ryzen-5-8600g.c3043",
    "Ryzen 5 8500G": "ryzen-5-8500g.c3044",
    "Ryzen 3 8300G": "ryzen-3-8300g.c3045",
    # Zen 5 (Ryzen 9000)
    "Ryzen 9 9950X": "ryzen-9-9950x.c3892",
    "Ryzen 9 9950X3D": "ryzen-9-9950x3d.c3993",
    "Ryzen 7 9700X": "ryzen-7-9700x.c3651",
    "Ryzen 5 9600X": "ryzen-5-9600x.c3652",
    "Ryzen 7 9800X3D": "ryzen-7-9800x3d.c3891",
    "Ryzen 5 9600": "ryzen-5-9600.c3653",
    "Ryzen 5 9500": "ryzen-5-9500.c3654",
    "Ryzen 7 9800X": "ryzen-7-9800x.c3891",
    # Zen 5 3D V-Cache
    "Ryzen 9 9900X3D": "ryzen-9-9900x3d.c4300",
    "Ryzen 7 9850X3D": "ryzen-7-9850x3d.c4301",
    # EPYC Server (milan, genoa, bergamo)
    "EPYC 7443": "epyc-7443.c2795",
    "EPYC 7543": "epyc-7543.c2796",
    "EPYC 7713": "epyc-7713.c2358",
    "EPYC 7763": "epyc-7763.c2359",
    "EPYC 7773X": "epyc-7773x.c2486",
    "EPYC 9254": "epyc-9254.c3208",
    "EPYC 9354": "epyc-9354.c3209",
    "EPYC 9454": "epyc-9454.c3210",
    "EPYC 9554": "epyc-9554.c3211",
    "EPYC 9654": "epyc-9654.c3212",
    # Radeon GPUs (usar techpowerup gpu specs)
    "Radeon RX 6600": "radeon-rx-6600.c3535",
    "Radeon RX 6600 XT": "radeon-rx-6600-xt.c3536",
    "Radeon RX 6650 XT": "radeon-rx-6650-xt.c3537",
    "Radeon RX 6700 XT": "radeon-rx-6700-xt.c3538",
    "Radeon RX 6750 XT": "radeon-rx-6750-xt.c3539",
    "Radeon RX 6800": "radeon-rx-6800.c3540",
    "Radeon RX 6800 XT": "radeon-rx-6800-xt.c3541",
    "Radeon RX 6900 XT": "radeon-rx-6900-xt.c3542",
    "Radeon RX 6950 XT": "radeon-rx-6950-xt.c3543",
    "Radeon RX 7600": "radeon-rx-7600.c3879",
    "Radeon RX 7700 XT": "radeon-rx-7700-xt.c3880",
    "Radeon RX 7800 XT": "radeon-rx-7800-xt.c3881",
    "Radeon RX 7900 XT": "radeon-rx-7900-xt.c3882",
    "Radeon RX 7900 XTX": "radeon-rx-7900-xtx.c3883",
    # Radeon Pro / FirePro
    "Radeon Pro W6600": "radeon-pro-w6600.c3558",
    "Radeon Pro W6800": "radeon-pro-w6800.c3559",
    "Radeon Pro W6900": "radeon-pro-w6900.c3560",
    "FirePro W7100": "firepro-w7100.c1860",
    "FirePro W7200": "firepro-w7200.c1861",
    "FirePro W7300": "firepro-w7300.c1862",
    # RX 6000 series
    "Radeon RX 6500 XT": "radeon-rx-6500-xt.c3544",
    "Radeon RX 6400": "radeon-rx-6400.c3545",
    # RX 7000 series
    "Radeon RX 7500": "radeon-rx-7500.c4087",
    "Radeon RX 9070 XT": "radeon-rx-9070-xt.c4322",
    "Radeon RX 9070": "radeon-rx-9070.c4321",
    "Radeon RX 7900 GRE": "radeon-rx-7900-gre.c4088",
    # Ryzen 3000/5000 non-X
    "Ryzen 3 3100": "ryzen-3-3100.c2053",
    "Ryzen 3 3300X": "ryzen-3-3300x.c2054",
    "Ryzen 3 5300G": "ryzen-3-5300g.c2470",
    # Threadripper PRO 5000
    "Ryzen Threadripper PRO 5945WX": "ryzen-threadripper-pro-5945wx.c2858",
    "Ryzen Threadripper PRO 5955WX": "ryzen-threadripper-pro-5955wx.c2859",
    "Ryzen Threadripper PRO 7960X": "ryzen-threadripper-pro-7960x.c2860",
    "Ryzen Threadripper PRO 7970X": "ryzen-threadripper-pro-7970x.c2861",
    "Ryzen Threadripper PRO 7980X": "ryzen-threadripper-pro-7980x.c2862",
}

TPU_BASE_URL = "https://www.techpowerup.com/cpu-specs/"


def update_amd_urls():
    """Update AMD URLs in enrichment_index to use TechPowerUp."""
    path = Path("hardwarextractor/data/enrichment_index.json")

    with open(path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    updated = 0
    skipped = 0
    not_found = []

    for component in catalog:
        if component.get("brand") != "AMD":
            continue

        model = component.get("model", "")

        # Check if already using TechPowerUp
        if "techpowerup.com" in component.get("source_url", ""):
            skipped += 1
            continue

        # Look for matching URL
        tpu_suffix = None

        # Try exact match first
        if model in AMD_MODEL_TO_TPU:
            tpu_suffix = AMD_MODEL_TO_TPU[model]
        else:
            # Try fuzzy matching
            for known_model, suffix in AMD_MODEL_TO_TPU.items():
                if (
                    known_model.lower() in model.lower()
                    or model.lower() in known_model.lower()
                ):
                    tpu_suffix = suffix
                    break

        if tpu_suffix:
            component["source_url"] = TPU_BASE_URL + tpu_suffix
            component["source_name"] = "TechPowerUp"
            component["spider_name"] = "techpowerup_cpu_spider"
            updated += 1
        else:
            not_found.append(model)

    # Save updated catalog
    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Updated {updated} AMD entries to use TechPowerUp")
    print(f"Skipped {skipped} entries (already TechPowerUp)")
    print(f"Modelos AMD sin mapeo: {len(not_found)}")

    if not_found:
        print("\nModelos no encontrados:")
        for m in sorted(set(not_found))[:20]:
            print(f"  - {m}")
        if len(not_found) > 20:
            print(f"  ... y {len(not_found) - 20} más")


if __name__ == "__main__":
    update_amd_urls()
