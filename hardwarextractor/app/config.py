from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    enable_tier2: bool = True
    user_agent: str = "HardwareXtractor/0.1"
    cache_ttl_seconds: int = 60 * 60 * 24 * 7
    retries: int = 2
    throttle_seconds_by_domain: dict = None

    def __post_init__(self) -> None:
        if self.throttle_seconds_by_domain is None:
            object.__setattr__(
                self,
                "throttle_seconds_by_domain",
                {
                    "intel.com": 1.0,
                    "amd.com": 1.0,
                    "nvidia.com": 1.0,
                    "asus.com": 1.0,
                    "msi.com": 1.0,
                    "gigabyte.com": 1.0,
                    "asrock.com": 1.0,
                    "kingston.com": 1.0,
                    "crucial.com": 1.0,
                    "samsung.com": 1.0,
                    "seagate.com": 1.0,
                    "wdc.com": 1.0,
                    "western-digital.com": 1.0,
                    "techpowerup.com": 2.0,
                    "wikichip.org": 2.0,
                },
            )


DEFAULT_CONFIG = AppConfig()
