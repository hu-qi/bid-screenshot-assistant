from datetime import UTC, datetime
from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters.china_mobile.parser import (
    PageContractError,
    has_explicit_no_results,
    parse_detail_page,
    parse_list_page,
)

FIXTURES = Path(__file__).parent / "fixtures" / "china_mobile"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_mobile_list_filters_external_links():
    entries = parse_list_page(read_fixture("list_found.html"))
    assert len(entries) == 1
    assert entries[0].title.startswith("中国移动2026年智慧园区")
    assert entries[0].url.endswith("noticeBean.id=1024001")
    assert entries[0].notice_type == "采购公告"
    assert entries[0].published_at == datetime(2026, 7, 18, tzinfo=UTC)


def test_parse_mobile_detail_extracts_official_attachment_only():
    url = "https://b2b.10086.cn/b2b/main/viewNoticeContent.html?noticeBean.id=1024001"
    detail = parse_detail_page(read_fixture("detail_found.html"), url)
    assert detail.title.startswith("中国移动2026年智慧园区")
    assert detail.published_at == datetime(2026, 7, 18, tzinfo=UTC)
    assert detail.notice_type == "采购公告"
    assert detail.attachment_urls == (
        "https://b2b.10086.cn/b2b/main/commonDownload.html?attachId=1001",
    )


def test_mobile_no_result_marker():
    assert has_explicit_no_results(read_fixture("list_not_found.html"))


def test_mobile_detail_rejects_unverified_url():
    with pytest.raises(PageContractError):
        parse_detail_page(
            read_fixture("detail_found.html"),
            "https://evil.example/b2b/main/viewNoticeContent.html?noticeBean.id=1024001",
        )
