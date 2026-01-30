#!/usr/bin/env python3
"""Expand catalog to target size."""
import json

def load_catalog():
    with open("hardwarextractor/data/resolver_index.json", "r") as f:
        return json.load(f)

def save_catalog(catalog):
    with open("hardwarextractor/data/resolver_index.json", "w") as f:
        json.dump(catalog, f, indent=2)

def exists(catalog, brand, model):
    brand, model = brand.lower(), model.lower()
    return any(c.get("brand", "").lower() == brand and c.get("model", "").lower() == model for c in catalog)

def add_component(catalog, comp):
    if not exists(catalog, comp["brand"], comp["model"]):
        catalog.append(comp)
        return True
    return False

# Components to add
NEW = [
    # CPUs - Intel
    {"component_type": "CPU", "brand": "Intel", "model": "Core i7-14700K", "part_number": "BX8071514700K", "score": 0.95, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/236719", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    {"component_type": "CPU", "brand": "Intel", "model": "Core i7-14700KF", "part_number": "BX8071514700KF", "score": 0.95, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/236720", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    {"component_type": "CPU", "brand": "Intel", "model": "Core i5-14600K", "part_number": "BX8071514600K", "score": 0.95, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/236718", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    {"component_type": "CPU", "brand": "Intel", "model": "Core i5-14600KF", "part_number": "BX8071514600KF", "score": 0.95, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/236717", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    {"component_type": "CPU", "brand": "Intel", "model": "Core i5-14400", "part_number": "BX8071514400", "score": 0.90, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/236715", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    {"component_type": "CPU", "brand": "Intel", "model": "Core i7-13700K", "part_number": "BX8071513700K", "score": 0.95, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/230495", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    {"component_type": "CPU", "brand": "Intel", "model": "Core i5-13600K", "part_number": "BX8071513600K", "score": 0.95, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/230493", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    {"component_type": "CPU", "brand": "Intel", "model": "Core i7-12700K", "part_number": "BX8071512700K", "score": 0.95, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/134594", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    {"component_type": "CPU", "brand": "Intel", "model": "Core i5-12600K", "part_number": "BX8071512600K", "score": 0.95, "source_url": "https://ark.intel.com/content/www/us/en/ark/products/134592", "source_name": "Intel ARK", "spider_name": "intel_ark_spider"},
    # AMD Ryzen 7000
    {"component_type": "CPU", "brand": "AMD", "model": "Ryzen 9 7950X3D", "part_number": "100-100000686WOF", "score": 0.98, "source_url": "https://www.amd.com/en/product/13251", "source_name": "AMD", "spider_name": "amd_cpu_specs_spider"},
    {"component_type": "CPU", "brand": "AMD", "model": "Ryzen 7 7800X3D", "part_number": "100-100000910WOF", "score": 0.98, "source_url": "https://www.amd.com/en/product/13256", "source_name": "AMD", "spider_name": "amd_cpu_specs_spider"},
    {"component_type": "CPU", "brand": "AMD", "model": "Ryzen 5 7600X", "part_number": "100-100000593WOF", "score": 0.95, "source_url": "https://www.amd.com/en/product/13244", "source_name": "AMD", "spider_name": "amd_cpu_specs_spider"},
    {"component_type": "CPU", "brand": "AMD", "model": "Ryzen 5 7600", "part_number": "100-100000837WOF", "score": 0.95, "source_url": "https://www.amd.com/en/product/13255", "source_name": "AMD", "spider_name": "amd_cpu_specs_spider"},
    {"component_type": "CPU", "brand": "AMD", "model": "Ryzen 7 7700X", "part_number": "100-100000592WOF", "score": 0.95, "source_url": "https://www.amd.com/en/product/13246", "source_name": "AMD", "spider_name": "amd_cpu_specs_spider"},
    # GPUs
    {"component_type": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4070 Ti SUPER", "score": 0.95, "source_url": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4070-ti-super.c3887", "source_name": "TechPowerUp", "spider_name": "techpowerup_gpu_spider"},
    {"component_type": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4080 SUPER", "score": 0.95, "source_url": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4080-super.c3888", "source_name": "TechPowerUp", "spider_name": "techpowerup_gpu_spider"},
    {"component_type": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4060", "score": 0.90, "source_url": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4060.c3886", "source_name": "TechPowerUp", "spider_name": "techpowerup_gpu_spider"},
    {"component_type": "GPU", "brand": "Intel", "model": "Arc A750", "score": 0.85, "source_url": "https://www.techpowerup.com/gpu-specs/intel-arc-a750.c3834", "source_name": "TechPowerUp", "spider_name": "techpowerup_gpu_spider"},
    {"component_type": "GPU", "brand": "Intel", "model": "Arc A770", "score": 0.85, "source_url": "https://www.techpowerup.com/gpu-specs/intel-arc-a770.c3835", "source_name": "TechPowerUp", "spider_name": "techpowerup_gpu_spider"},
    # RAM
    {"component_type": "RAM", "brand": "Corsair", "model": "Vengeance DDR5-6000 32GB", "part_number": "CMK32GX5M2B6000C36", "score": 0.90, "source_url": "https://www.corsair.com/us/en/Categories/Products/Memory/VENGEANCE-DDR5-Memory", "source_name": "Corsair", "spider_name": "corsair_ram_spider"},
    {"component_type": "RAM", "brand": "G.Skill", "model": "Trident Z5 DDR5-6000 32GB", "score": 0.90, "source_url": "https://www.gskill.com/product/1/1700/167454", "source_name": "G.Skill", "spider_name": "gskill_ram_spider"},
    {"component_type": "RAM", "brand": "Kingston", "model": "Fury DDR5-5600 32GB", "score": 0.85, "source_url": "https://www.kingston.com/unitedstates/en/memory/gaming/kf556c40bbk2-32", "source_name": "Kingston", "spider_name": "kingston_ram_spider"},
    # Motherboards
    {"component_type": "MAINBOARD", "brand": "ASUS", "model": "ROG Strix Z790-E", "score": 0.95, "source_url": "https://www.asus.com/us/motherboards-components/rog-strix/rog-strix-z790-e-gaming-wifi/", "source_name": "ASUS", "spider_name": "asus_mainboard_spider"},
    {"component_type": "MAINBOARD", "brand": "MSI", "model": "MPG Z790 Edge", "score": 0.95, "source_url": "https://www.msi.com/Motherboard/MPG-Z790-EDGE-WIFI", "source_name": "MSI", "spider_name": "msi_mainboard_spider"},
    {"component_type": "MAINBOARD", "brand": "Gigabyte", "model": "Z790 Aorus Elite", "score": 0.90, "source_url": "https://www.gigabyte.com/Motherboard/Z790-AORUS-ELITE-rev-1x", "source_name": "Gigabyte", "spider_name": "gigabyte_mainboard_spider"},
    {"component_type": "MAINBOARD", "brand": "ASUS", "model": "TUF Gaming B650-Plus", "score": 0.90, "source_url": "https://www.asus.com/us/motherboards-components/tuf-gaming/tuf-gaming-b650-plus/", "source_name": "ASUS", "spider_name": "asus_mainboard_spider"},
    # Storage
    {"component_type": "DISK", "brand": "Samsung", "model": "990 PRO 2TB", "part_number": "MZ-V9P2T0BW", "score": 0.95, "source_url": "https://www.samsung.com/us/computing/memory-storage/solid-state-drives/990-pro-nvme-ssd-2tb-mz-v9p2t0bw/", "source_name": "Samsung", "spider_name": "samsung_storage_spider"},
    {"component_type": "DISK", "brand": "WD", "model": "Black SN850X 2TB", "part_number": "WDS200T2X0E", "score": 0.90, "source_url": "https://www.wdc.com/en/us/products/internal-ssd/wd-black-sn850x.html", "source_name": "WD", "spider_name": "wdc_storage_spider"},
]

if __name__ == "__main__":
    catalog = load_catalog()
    added = 0
    for comp in NEW:
        if add_component(catalog, comp):
            added += 1
    save_catalog(catalog)
    print(f"Added {added} components. Total: {len(catalog)}")
