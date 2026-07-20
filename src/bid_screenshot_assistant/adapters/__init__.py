from bid_screenshot_assistant.adapters.catalog import (
    DESCRIPTORS,
    build_cebpubservice_registry,
    build_china_mobile_registry,
    build_china_tower_eproc_registry,
    build_china_unicom_registry,
    build_gd_gp_registry,
    build_simulation_registry,
    get_descriptor,
)
from bid_screenshot_assistant.adapters.profiles import BROWSER_PROFILES, get_browser_profile

__all__ = [
    "BROWSER_PROFILES",
    "DESCRIPTORS",
    "build_cebpubservice_registry",
    "build_china_mobile_registry",
    "build_china_tower_eproc_registry",
    "build_china_unicom_registry",
    "build_gd_gp_registry",
    "build_simulation_registry",
    "get_browser_profile",
    "get_descriptor",
]
