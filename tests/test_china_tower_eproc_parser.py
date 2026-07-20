from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters.china_tower_eproc import (
    PageContractError,
    has_explicit_no_results,
    match_score,
    parse_detail_page,
    parse_list_page,
)

FIXTURES = Path(__file__).parent / "fixtures" / "china_tower_eproc"
DETAIL_URL = (
    "https://ebid.chinatowercom.cn/zgtt/gggs/003001/20260507/"
    "68fee2cd-e504-468b-83d1-65164b4e4b65.html"
)


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_list_page_keeps_only_verified_detail_links():
    entries = parse_list_page(read_fixture("list_found.html"))

    assert len(entries) == 2
    assert entries[0].url == DETAIL_URL
    assert entries[0].published_at is not None
    assert all("evil.example" not in item.url for item in entries)


def test_no_result_requires_explicit_page_marker():
    assert has_explicit_no_results(read_fixture("list_not_found.html"))
    assert not has_explicit_no_results(read_fixture("list_found.html"))


def test_parse_detail_extracts_title_date_body_and_attachment():
    detail = parse_detail_page(read_fixture("detail_found.html"), DETAIL_URL)

    assert "智慧园区地勘服务采购项目" in detail.title
    assert detail.published_at is not None
    assert "项目编号：TEST-2026-001" in detail.body_text
    assert detail.attachment_urls == (
        "https://ebid.chinatowercom.cn/uploads/2026/tower-announcement.pdf",
    )


def test_detail_contract_rejects_external_url_and_missing_fingerprint():
    with pytest.raises(PageContractError):
        parse_detail_page(read_fixture("detail_found.html"), "https://evil.example/detail.html")

    with pytest.raises(PageContractError):
        parse_detail_page("<html><h1>只有标题没有时间</h1></html>", DETAIL_URL)


def test_match_score_prioritizes_query_containment():
    score, reason = match_score("智慧园区", "[公开招标]中国铁塔智慧园区采购项目公告")
    assert score == 0.98
    assert "contained" in reason
