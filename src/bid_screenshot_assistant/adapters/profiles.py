from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from bid_screenshot_assistant.domain.models import PlatformId


@dataclass(frozen=True, slots=True)
class PageFingerprint:
    """Observable page signals used before an adapter performs sensitive actions."""

    required_text: tuple[str, ...] = ()
    any_text: tuple[str, ...] = ()
    expected_path_prefix: str = "/"


@dataclass(frozen=True, slots=True)
class PlatformBrowserProfile:
    platform_id: PlatformId
    display_name: str
    allowed_hosts: tuple[str, ...]
    start_url: str
    search_url: str
    requires_javascript: bool
    public_search: bool
    search_placeholders: tuple[str, ...]
    submit_labels: tuple[str, ...]
    list_fingerprint: PageFingerprint
    detail_url_patterns: tuple[str, ...]
    detail_fingerprint: PageFingerprint
    no_result_markers: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def is_allowed_host(self, url: str) -> bool:
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        return parsed.scheme == "https" and hostname in self.allowed_hosts

    def matches_detail_url(self, url: str) -> bool:
        if not self.is_allowed_host(url):
            return False
        return any(re.fullmatch(pattern, url) for pattern in self.detail_url_patterns)


CHINA_MOBILE_PROFILE = PlatformBrowserProfile(
    platform_id=PlatformId.CHINA_MOBILE,
    display_name="中国移动采购与招标网",
    allowed_hosts=("b2b.10086.cn",),
    start_url="https://b2b.10086.cn/",
    search_url="https://b2b.10086.cn/",
    requires_javascript=True,
    public_search=True,
    search_placeholders=("请输入公告标题包含的关键字",),
    submit_labels=("搜索",),
    list_fingerprint=PageFingerprint(
        required_text=("招标采购公告", "请输入公告标题包含的关键字"),
        any_text=("正在招标", "即将开标", "正在候选人公示"),
        expected_path_prefix="/",
    ),
    # The live result/detail URL shape has not yet been verified in Playwright.
    detail_url_patterns=(),
    detail_fingerprint=PageFingerprint(),
    no_result_markers=("无匹配数据",),
    notes=("Do not classify the initial homepage empty state as NOT_FOUND.",),
)


CHINA_UNICOM_PROFILE = PlatformBrowserProfile(
    platform_id=PlatformId.CHINA_UNICOM,
    display_name="中国联通采购与招标网",
    allowed_hosts=("www.chinaunicombidding.cn", "chinaunicombidding.cn"),
    start_url="https://www.chinaunicombidding.cn/",
    search_url="https://www.chinaunicombidding.cn/bidInformation",
    requires_javascript=True,
    public_search=True,
    search_placeholders=("请输入公告关键词",),
    submit_labels=("搜索",),
    list_fingerprint=PageFingerprint(
        required_text=("搜索公告", "请输入公告关键词"),
        any_text=("今天", "近三天", "近一周", "近一月"),
        expected_path_prefix="/bidInformation",
    ),
    detail_url_patterns=(
        r"https://(?:www\.)?chinaunicombidding\.cn/bidInformation/detail\?(?:cid=\d+&)?id=\d+",
    ),
    detail_fingerprint=PageFingerprint(
        required_text=("发布时间",),
        any_text=("招标编号", "采购项目编号", "采购代理编号"),
        expected_path_prefix="/bidInformation/detail",
    ),
    no_result_markers=("暂无数据", "暂无公告", "没有符合条件的公告", "无匹配数据"),
    notes=(
        "The list page is an Ant Design single-page application.",
        "A static/non-browser client may see a JavaScript notice or error code 501.",
        "Historical detail links may include cid before the numeric id parameter.",
    ),
)


CHINA_TOWER_EPROC_PROFILE = PlatformBrowserProfile(
    platform_id=PlatformId.CHINA_TOWER_EPROC,
    display_name="中国铁塔电子采购平台",
    allowed_hosts=("ebid.chinatowercom.cn",),
    start_url="https://ebid.chinatowercom.cn/",
    search_url="https://ebid.chinatowercom.cn/zgtt/gggs/003001/detailpage.html",
    requires_javascript=True,
    public_search=True,
    search_placeholders=("请输入搜索关键字",),
    submit_labels=("查询",),
    list_fingerprint=PageFingerprint(
        required_text=("公告公示", "省份", "时间", "行业", "搜索关键字", "查询"),
        any_text=("采购公告", "变更公告", "候选人公示", "采购结果公示"),
        expected_path_prefix="/zgtt/gggs/",
    ),
    detail_url_patterns=(
        r"https://ebid\.chinatowercom\.cn/zgtt/gggs/\d{6}/\d{8}/[A-Za-z0-9-]+\.html",
    ),
    detail_fingerprint=PageFingerprint(
        required_text=("信息时间",),
        any_text=("采购公告", "变更公告", "候选人公示", "采购结果公示", "采购项目预公示"),
        expected_path_prefix="/zgtt/gggs/",
    ),
    notes=(
        "Public announcement browsing is separate from supplier login and tender operations.",
        "External mall, CA and legacy portal links are outside the adapter allowlist.",
    ),
)


BROWSER_PROFILES: dict[PlatformId, PlatformBrowserProfile] = {
    profile.platform_id: profile
    for profile in (
        CHINA_MOBILE_PROFILE,
        CHINA_UNICOM_PROFILE,
        CHINA_TOWER_EPROC_PROFILE,
    )
}


def get_browser_profile(platform_id: PlatformId) -> PlatformBrowserProfile:
    try:
        return BROWSER_PROFILES[platform_id]
    except KeyError as exc:
        raise KeyError(f"No verified browser profile for {platform_id}") from exc
