from bid_screenshot_assistant.adapters.base import AdapterRegistry
from bid_screenshot_assistant.adapters.mock import SimulationPlatformAdapter
from bid_screenshot_assistant.domain.models import PlatformDescriptor, PlatformId


DESCRIPTORS = [
    PlatformDescriptor(
        platform_id=PlatformId.CHINA_MOBILE,
        display_name="中国移动采购与招标网",
    ),
    PlatformDescriptor(
        platform_id=PlatformId.CHINA_UNICOM,
        display_name="中国联通采购与招标网",
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


def build_simulation_registry() -> AdapterRegistry:
    return AdapterRegistry([SimulationPlatformAdapter(descriptor) for descriptor in DESCRIPTORS])
