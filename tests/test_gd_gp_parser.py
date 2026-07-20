from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters.gd_gp.parser import (
    PageContractError,
    has_explicit_no_results,
    parse_detail_payload,
    parse_search_payload,
)


FIXTURES = Path(__file__).parent / "fixtures" / "gd_gp"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_search_parser_restores_highlighted_title_and_urls():
    entries = parse_search_payload(read_fixture("search_found.json"))

    assert len(entries) == 1
    entry = entries[0]
    assert entry.title == "惠州市算力中心服务器采购项目结果公告"
    assert entry.record_id == "19249ba9-5d33-48e4-b9cb-def134be8824"
    assert "/gpcms/rest/web/v2/info/getInfoById?id=" in entry.detail_api_url
    assert entry.portal_url.startswith("https://gdgpo.czt.gd.gov.cn/articleGd?")
    assert entry.project_code == "HZBY-2026A002"


def test_explicit_no_result_requires_valid_success_payload():
    assert has_explicit_no_results(read_fixture("search_not_found.json"))
    with pytest.raises(PageContractError):
        has_explicit_no_results('{"code":"500","msg":"系统异常"}')


def test_detail_parser_extracts_fields_and_filters_external_attachments():
    source_url = (
        "https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/getInfoById?"
        "id=19249ba9-5d33-48e4-b9cb-def134be8824"
    )
    detail = parse_detail_payload(read_fixture("detail_found.json"), source_url)

    assert detail.title == "惠州市算力中心服务器采购项目结果公告"
    assert detail.project_code == "HZBY-2026A002"
    assert detail.purchaser == "惠州市政务服务和数据管理局"
    assert "计算服务器" in detail.body_text
    assert detail.attachment_urls == (
        "https://gdgpo.czt.gd.gov.cn/freecms/download/server-result.pdf",
    )


def test_detail_parser_rejects_unverified_source_url():
    with pytest.raises(PageContractError):
        parse_detail_payload(read_fixture("detail_found.json"), "https://evil.example/detail")
