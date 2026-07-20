from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters.china_unicom import (
    PageContractError,
    has_explicit_no_results,
    is_unhydrated_or_error,
    match_score,
    parse_detail_page,
    parse_list_page,
)

FIXTURES = Path(__file__).parent / "fixtures" / "china_unicom"
DETAIL_URL = (
    "https://www.chinaunicombidding.cn/bidInformation/detail?"
    "id=2029888598345940992"
)


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_list_supports_current_and_historical_detail_urls():
    entries = parse_list_page(read_fixture("list_found.html"))

    assert len(entries) == 2
    assert entries[0].url == DETAIL_URL
    assert entries[0].published_at is not None
    assert "cid=14&id=" in entries[1].url
    assert all("evil.example" not in item.url for item in entries)


def test_unhydrated_501_is_not_treated_as_no_results():
    html = read_fixture("list_501.html")
    assert is_unhydrated_or_error(html)
    assert not has_explicit_no_results(html)
    with pytest.raises(PageContractError):
        parse_list_page(html)


def test_explicit_no_result_marker():
    assert has_explicit_no_results(read_fixture("list_not_found.html"))
    assert not has_explicit_no_results(read_fixture("list_found.html"))


def test_parse_detail_extracts_public_fields_and_filters_external_attachment():
    detail = parse_detail_page(read_fixture("detail_found.html"), DETAIL_URL)

    assert "智慧工厂化养殖项目" in detail.title
    assert detail.bid_number == "HX-JSLT-WXGK-2026070"
    assert detail.published_at.year == 2026
    assert "项目资金由招标人自筹" in detail.body_text
    assert detail.attachment_urls == (
        "https://www.chinaunicombidding.cn/uploads/2026/unicom-attachment.docx",
    )


def test_detail_supports_cid_and_rejects_external_or_missing_fingerprint():
    historical_url = (
        "https://www.chinaunicombidding.cn/bidInformation/detail?"
        "cid=14&id=1938512076293636096"
    )
    assert parse_detail_page(read_fixture("detail_found.html"), historical_url)

    with pytest.raises(PageContractError):
        parse_detail_page(read_fixture("detail_found.html"), "https://evil.example/detail?id=1")
    with pytest.raises(PageContractError):
        parse_detail_page("<html><h1>缺少发布时间</h1></html>", DETAIL_URL)


def test_match_score_prioritizes_containment():
    score, reason = match_score("智慧工厂", "2026江苏产互无锡智慧工厂化养殖项目招标公告")
    assert score == 0.98
    assert "contained" in reason
