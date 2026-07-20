import pytest

from bid_screenshot_assistant.adapters.profiles import (
    BROWSER_PROFILES,
    CHINA_MOBILE_PROFILE,
    CHINA_TOWER_EPROC_PROFILE,
    CHINA_UNICOM_PROFILE,
)
from bid_screenshot_assistant.domain.models import PlatformId
from bid_screenshot_assistant.services.url_guard import (
    UnsafeNavigationError,
    validate_detail_url,
    validate_navigation_url,
)


def test_priority_profiles_are_unique_and_https():
    assert set(BROWSER_PROFILES) == {
        PlatformId.CHINA_MOBILE,
        PlatformId.CHINA_UNICOM,
        PlatformId.CHINA_TOWER_EPROC,
    }
    for profile in BROWSER_PROFILES.values():
        assert profile.start_url.startswith("https://")
        assert profile.search_url.startswith("https://")
        assert profile.list_fingerprint.required_text


def test_unicom_detail_url_pattern():
    url = "https://www.chinaunicombidding.cn/bidInformation/detail?id=2039648933262467072"
    assert validate_detail_url(CHINA_UNICOM_PROFILE, url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://ebid.chinatowercom.cn/zgtt/gggs/003001/20260718/60351801-c5ce-405a-9c51-cd0daf04342f.html",
        "https://ebid.chinatowercom.cn/zgtt/gggs/003005/20260310/2031253312750497793.html",
    ],
)
def test_tower_detail_url_patterns(url: str):
    assert validate_detail_url(CHINA_TOWER_EPROC_PROFILE, url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://b2b.10086.cn/b2b/main/viewNoticeContent.html?noticeBean.id=1024001",
        "https://b2b.10086.cn/b2b/main/viewVendorNoticeContent.html?noticeBean.id=21064",
    ],
)
def test_mobile_candidate_detail_url_patterns(url: str):
    assert validate_detail_url(CHINA_MOBILE_PROFILE, url) == url


def test_deceptive_and_external_hosts_are_rejected():
    for url in (
        "https://ebid.chinatowercom.cn.evil.example/zgtt/gggs/003001/detail.html",
        "https://evil.example/?next=https://ebid.chinatowercom.cn/",
        "http://ebid.chinatowercom.cn/zgtt/",
        "https://user:password@ebid.chinatowercom.cn/zgtt/",
        "https://ebid.chinatowercom.cn:8443/zgtt/",
    ):
        with pytest.raises(UnsafeNavigationError):
            validate_navigation_url(CHINA_TOWER_EPROC_PROFILE, url)


def test_arbitrary_mobile_url_is_rejected():
    with pytest.raises(UnsafeNavigationError):
        validate_detail_url(CHINA_MOBILE_PROFILE, "https://b2b.10086.cn/anything")
