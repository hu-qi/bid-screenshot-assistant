from datetime import UTC, datetime
from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters.cebpubservice.parser import (
    PageContractError,
    has_captcha,
    has_explicit_no_results,
    parse_detail_page,
    parse_list_page,
)

FIXTURES = Path(__file__).parent / "fixtures" / "cebpubservice"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_ceb_list_filters_external_links():
    entries = parse_list_page(read_fixture("list_found.html"))
    assert len(entries) == 1
    assert entries[0].title.startswith("2026年智慧园区")
    assert entries[0].notice_type == "招标公告"
    assert entries[0].published_at == datetime(2026, 7, 10, tzinfo=UTC)


def test_parse_ceb_detail_keeps_official_attachment_only():
    url = "https://bulletin.cebpubservice.com/biddingBulletin/2026-07-10/ea173ca71daa4f73aaa8188ed2fb1ca3.html"
    detail = parse_detail_page(read_fixture("detail_found.html"), url)
    assert detail.title.startswith("2026年智慧园区")
    assert detail.notice_type == "招标公告"
    assert detail.published_at == datetime(2026, 7, 10, tzinfo=UTC)
    assert detail.publisher == "中国招标投标公共服务平台"
    assert detail.source_channel == "测试电子招标平台"
    assert detail.attachment_urls == (
        "https://bulletin.cebpubservice.com/download/notice-file.pdf",
    )


def test_no_result_and_captcha_markers_are_distinct():
    assert has_explicit_no_results(read_fixture("list_not_found.html"))
    assert has_captcha(read_fixture("list_captcha.html"))
    assert not has_captcha(read_fixture("detail_found.html"))


def test_detail_rejects_external_url():
    with pytest.raises(PageContractError):
        parse_detail_page(read_fixture("detail_found.html"), "https://evil.example/detail.html")
