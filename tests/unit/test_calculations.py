from __future__ import annotations

from hardwarextractor.utils.calculations import bw_pcie_external_gbs, bw_ram_gbs, bw_sata_gbs, bw_usb_gbs


def test_bw_ram():
    assert bw_ram_gbs(3200, 2) == 51.2


def test_bw_pcie():
    assert bw_pcie_external_gbs("4.0", 16) == 31.51


def test_bw_sata_usb():
    assert bw_sata_gbs("SATA III") == 6.0
    assert bw_usb_gbs("USB 3.2") == 20.0
