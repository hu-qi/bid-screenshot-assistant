from pathlib import Path

from bid_screenshot_assistant.adapters.base import AdapterRegistry
from bid_screenshot_assistant.adapters.mock import SimulationPlatformAdapter
from bid_screenshot_assistant.domain.models import PlatformDescriptor, PlatformId


DESCRIPTORS = [
    PlatformDescriptor(
        platform_id=PlatformId.CHINA_MOBILE,
        display_name="中国移动采购与招标网",
        supports_notice_type_filter=True,
    ),
    PlatformDescriptor(
        platform_id=PlatformId.CHINA_UNICOM,
        display_name="中国联通采购与招标网",
        supports_date_filter=True,
    ),
    PlatformDescriptor(
        platform_id=PlatformId.CHINA_TELECOM,
        display_name="中国电信阳光采购网",
    ),
    PlatformDescriptor(
        platform_id=PlatformId.CHINA_TOWER_ONLINE,
        display_name="中国铁塔在线商务平台",
        requires_login=True,
    ),
    PlatformDescriptor(
        platform_id=PlatformId.CHINA_TOWER_EPROC,
        display_name="中国铁塔电子采购平台",
        supports_date_filter=True,
        supports_notice_type_filter=True,
    ),
    PlatformDescriptor(
        platform_id=PlatformId.CEBPUBSERVICE,
        display_name="中国招标投标公共服务平台",
    ),
    PlatformDescriptor(
        platform_id=PlatformId.MIIT,
        display_name="工信部通信工程建设项目招标投标管理信息平台",
    ),
    PlatformDescriptor(
        platform_id=PlatformId.GD_GP,
        display_name="广东政府采购智慧云平台",
    ),
    PlatformDescriptor(
        platform_id=PlatformId.GD_GGZY,
        display_name="广东省公共资源交易平台",
    ),
]


def get_descriptor(platform_id: PlatformId) -> PlatformDescriptor:
    try:
        return next(item for item in DESCRIPTORS if item.platform_id == platform_id)
    except StopIteration as exc:
        raise KeyError(f"No descriptor registered for {platform_id}") from exc


def build_simulation_registry() -> AdapterRegistry:
    return AdapterRegistry([SimulationPlatformAdapter(descriptor) for descriptor in DESCRIPTORS])


def build_china_mobile_registry(
    *,
    headless: bool = True,
    timeout_ms: int = 45_000,
    user_data_dir: Path | None = None,
) -> AdapterRegistry:
    """Build an explicit experimental registry containing only the real Mobile adapter."""
    from bid_screenshot_assistant.adapters.china_mobile import ChinaMobileAdapter

    descriptor = get_descriptor(PlatformId.CHINA_MOBILE)
    return AdapterRegistry(
        [
            ChinaMobileAdapter(
                descriptor,
                headless=headless,
                timeout_ms=timeout_ms,
                user_data_dir=user_data_dir,
            )
        ]
    )


def build_china_tower_eproc_registry(
    *,
    headless: bool = True,
    timeout_ms: int = 45_000,
    user_data_dir: Path | None = None,
) -> AdapterRegistry:
    """Build an explicit experimental registry containing only the real Tower adapter."""
    from bid_screenshot_assistant.adapters.china_tower_eproc import ChinaTowerEprocAdapter

    descriptor = get_descriptor(PlatformId.CHINA_TOWER_EPROC)
    return AdapterRegistry(
        [
            ChinaTowerEprocAdapter(
                descriptor,
                headless=headless,
                timeout_ms=timeout_ms,
                user_data_dir=user_data_dir,
            )
        ]
    )


def build_china_unicom_registry(
    *,
    headless: bool = True,
    timeout_ms: int = 45_000,
    user_data_dir: Path | None = None,
) -> AdapterRegistry:
    """Build an explicit experimental registry containing only the real Unicom adapter."""
    from bid_screenshot_assistant.adapters.china_unicom import ChinaUnicomAdapter

    descriptor = get_descriptor(PlatformId.CHINA_UNICOM)
    return AdapterRegistry(
        [
            ChinaUnicomAdapter(
                descriptor,
                headless=headless,
                timeout_ms=timeout_ms,
                user_data_dir=user_data_dir,
            )
        ]
    )
