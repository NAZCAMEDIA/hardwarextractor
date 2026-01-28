from __future__ import annotations

from typing import Optional


def bw_ram_gbs(mt_s: Optional[float], channels: Optional[int]) -> Optional[float]:
    if mt_s is None or channels is None:
        return None
    return round((mt_s * 8 * channels) / 1000, 2)


def bw_gpu_internal_gbs(speed_gbps: Optional[float], bus_width_bits: Optional[int]) -> Optional[float]:
    if speed_gbps is None or bus_width_bits is None:
        return None
    return round((speed_gbps * bus_width_bits) / 8, 2)


PCIE_BW_TABLE = {
    "3.0": {1: 0.985, 4: 3.94, 8: 7.88, 16: 15.75},
    "4.0": {1: 1.969, 4: 7.88, 8: 15.75, 16: 31.51},
    "5.0": {1: 3.938, 4: 15.75, 8: 31.51, 16: 63.02},
}


def bw_pcie_external_gbs(version: Optional[str], lanes: Optional[int]) -> Optional[float]:
    if version is None or lanes is None:
        return None
    table = PCIE_BW_TABLE.get(str(version))
    if not table:
        return None
    return table.get(lanes)


SATA_BW_TABLE_GBS = {
    "SATA I": 1.5,
    "SATA II": 3.0,
    "SATA III": 6.0,
}

USB_BW_TABLE_GBS = {
    "USB 2.0": 0.48,
    "USB 3.0": 5.0,
    "USB 3.1": 10.0,
    "USB 3.2": 20.0,
}


def bw_sata_gbs(version: Optional[str]) -> Optional[float]:
    if version is None:
        return None
    return SATA_BW_TABLE_GBS.get(version)


def bw_usb_gbs(version: Optional[str]) -> Optional[float]:
    if version is None:
        return None
    return USB_BW_TABLE_GBS.get(version)
