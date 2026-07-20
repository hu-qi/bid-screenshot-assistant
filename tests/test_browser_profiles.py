import pytest

from bid_screenshot_assistant.adapters.profiles import (
    BROWSER_PROFILES,
    CEBPUBSERVICE_PROFILE,
    CHINA_MOBILE_PROFILE,
    CHINA_TOWER_EPROC_PROFILE,
    CHINA_UNICOM_PROFILE,
    GD_GP_PROFILE,
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
        PlatformId.CEBPUBSERVICE,
        PlatformId.GD_GP,
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


@pytest.mark.parametrize(
    "url",
    [
        "https://bulletin.cebpubservice.com/biddingBulletin/2026-07-10/ea173ca71daa4f73aaa8188ed2fb1ca3.html",
        "https://bulletin.cebpubservice.com/changeBulletin/2026-03-24/e4c22aa8a6804beba06130b65a45f3b2.html",
    ],
)
def test_ceb_detail_url_patterns(url: str):
    assert validate_detail_url(CEBPUBSERVICE_PROFILE, url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/getInfoById?id=19249ba9-5d33-48e4-b9cb-def134be8824",
        "https://gdgpo.czt.gd.gov.cn/articleGd?type=article&id=19249ba9-5d33-48e4-b9cb-def134be8824&channelName=%E9%87%87%E8%B4%AD%E7%BB%93%E6%9E%9C%E5%85%AC%E5%91%8A",
    ],
)
def test_gd_gp_detail_url_patterns(url: str):
    assert validate_detail_url(GD_GP_PROFILE, url) == url


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


def test_arbitrary_urls_are_rejected():
    with pytest.raises(UnsafeNavigationError):
        validate_detail_url(CHINA_MOBILE_PROFILE, "https://b2b.10086.cn/anything")
    with pytest.raises(UnsafeNavigationError):
        validate_detail_url(CEBPUBSERVICE_PROFILE, "https://bulletin.cebpubservice.com/anything")
    with pytest.raises(UnsafeNavigationError):
        validate_detail_url(GD_GP_PROFILE, "https://gdgpo.czt.gd.gov.cn/anything")
