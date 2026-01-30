#!/usr/bin/env python3
"""Test which sources work with Playwright for scraping."""

from __future__ import annotations

import json
import sys
from datetime import datetime

sys.path.insert(0, ".")

from hardwarextractor.scrape.service import _fetch_with_fallback


# Test URLs por categoria
TEST_URLS = {
    "CPU": [
        # Intel ARK (oficial, deberia funcionar)
        "https://www.intel.com/content/www/us/en/products/details/processors/core/i9-14900k.html",
        # AMD (oficial)
        "https://www.amd.com/en/product/11796",
        # TechPowerUp (referencia, bloquea requests simples)
        "https://www.techpowerup.com/cpu-specs/amd-ryzen-9-7950x.c18887",
        "https://www.techpowerup.com/cpu-specs/intel-core-i9-14900k.c4071",
    ],
    "GPU": [
        # NVIDIA (oficial)
        "https://www.nvidia.com/en-us/geforce/graphics-cards/4090/",
        "https://www.nvidia.com/en-us/data-center/h100/",
        # AMD (oficial)
        "https://www.amd.com/en/graphics-cards/rx-7900-xtx",
        # TechPowerUp (referencia)
        "https://www.techpowerup.com/gpu-specs/nvidia-geforce-rtx-4090.c3889",
    ],
    "RAM": [
        # Corsair (oficial)
        "https://www.corsair.com/us/en/vengeance-ddr5-memory",
        # G.Skill (oficial)
        "https://www.gskill.com/memory/1/Trident-Z5",
    ],
    "DISK": [
        # Samsung (oficial)
        "https://www.samsung.com/ssd/990-pro/",
        # WD (oficial)
        "https://www.westerndigital.com/products/internal-drives/wd-black-sn850x-ssd",
    ],
}


def test_url(url: str, timeout: int = 30000) -> dict:
    """Test a single URL with Playwright fallback."""
    print(f"\nProbando: {url[:60]}...")

    result = _fetch_with_fallback(url, timeout=timeout, retries=1)

    html_len = len(result.html) if result.html else 0
    status = result.status_code

    if html_len > 1000 and status == 200:
        html_lower = result.html.lower() if result.html else ""
        if "captcha" in html_lower or "verify you are human" in html_lower:
            return {
                "url": url,
                "status": status,
                "html_len": html_len,
                "engine": result.engine_used,
                "blocked": True,
                "reason": "CAPTCHA detected",
            }
        return {
            "url": url,
            "status": status,
            "html_len": html_len,
            "engine": result.engine_used,
            "blocked": False,
            "success": True,
        }
    elif status == 403 or status == 429:
        return {
            "url": url,
            "status": status,
            "html_len": html_len,
            "engine": result.engine_used,
            "blocked": True,
            "reason": f"HTTP {status} - Rate limited",
        }
    else:
        return {
            "url": url,
            "status": status,
            "html_len": html_len,
            "engine": result.engine_used,
            "blocked": True,
            "reason": f"HTTP {status}, only {html_len} bytes",
        }


def run_tests(max_per_category: int = 2) -> dict:
    """Run tests on sample URLs from each category."""
    print("=" * 70)
    print("TEST DE FUENTES CON PLAYWRIGHT")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    results = {"summary": {}, "details": []}

    for category, urls in TEST_URLS.items():
        test_urls = urls[:max_per_category]
        print(f"\n[{category}] {len(test_urls)} URLs de prueba")
        print("-" * 50)

        working = 0
        blocked = 0

        for url in test_urls:
            result = test_url(url)
            results["details"].append({**result, "category": category})

            if result.get("success"):
                working += 1
                print(f"  [OK] {result['engine']} - {result['html_len'] // 1024}KB")
            else:
                blocked += 1
                print(f"  [FAIL] {result.get('reason', 'Unknown')}")

        results["summary"][category] = {
            "tested": len(test_urls),
            "working": working,
            "blocked": blocked,
        }

    return results


def print_final_report(results: dict) -> None:
    """Print final summary report."""
    print("\n" + "=" * 70)
    print("REPORTE FINAL")
    print("=" * 70)

    total_tested = sum(r["tested"] for r in results["summary"].values())
    total_working = sum(r["working"] for r in results["summary"].values())
    total_blocked = sum(r["blocked"] for r in results["summary"].values())

    print(f"\nTotal probado: {total_tested} URLs")
    print(f"Funcionando: {total_working} ({total_working / total_tested * 100:.0f}%)")
    print(f"Bloqueadas: {total_blocked} ({total_blocked / total_tested * 100:.0f}%)")

    print("\nPor categoria:")
    for category, stats in results["summary"].items():
        print(f"  {category}: {stats['working']}/{stats['tested']} funcionando")

    # Save results
    output_file = "playwright_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResultados guardados en: {output_file}")


if __name__ == "__main__":
    results = run_tests(max_per_category=3)
    print_final_report(results)
