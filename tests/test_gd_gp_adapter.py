from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters import get_descriptor
from bid_screenshot_assistant.adapters.gd_gp import GdGpAdapter
from bid_screenshot_assistant.adapters.gd_gp.models import BrowserSnapshot
from bid_screenshot_assistant.domain.models import (
    AdapterRequest,
    PlatformId,
    PlatformRunStatus,
)


FIXTURES = Path(__file__).parent / "fixtures" / "gd_gp"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeGdGpDriver:
    def __init__(
        self,
        search_text: str,
        detail_text: str | None = None,
        *,
        detail_error=None,
        portal_error=None,
    ) -> None:
        self.search_text = search_text
        self.detail_text = detail_text
        self.detail_error = detail_error
        self.portal_error = portal_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def search(self, query_name: str) -> BrowserSnapshot:
        return BrowserSnapshot(
            url=(
                "https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/"
                "selectInfoForIndex?searchKey=" + query_name
            ),
            html=f"<pre>{self.search_text}</pre>",
            body_text=self.search_text,
            screenshot=b"search-png",
        )

    async def fetch_detail_api(self, url: str) -> BrowserSnapshot:
        if self.detail_error:
            raise self.detail_error
        return BrowserSnapshot(
            url=url,
            html=f"<pre>{self.detail_text or ''}</pre>",
            body_text=self.detail_text or "",
            screenshot=b"detail-api-png",
        )

    async def fetch_portal(self, url: str) -> BrowserSnapshot:
        if self.portal_error:
            raise self.portal_error
        return BrowserSnapshot(
            url=url,
            html="<html><body><h1>惠州市算力中心服务器采购项目结果公告</h1></body></html>",
            body_text="惠州市算力中心服务器采购项目结果公告",
            screenshot=b"portal-png",
        )


def build_request(query_name: str = "服务器采购") -> AdapterRequest:
    return AdapterRequest(
        task_id="task-1",
        run_id="run-1",
        query_id="query-1",
        query_name=query_name,
        platform_id=PlatformId.GD_GP,
        max_hits=1,
    )


@pytest.mark.asyncio
async def test_adapter_found_writes_api_and_portal_evidence(tmp_path: Path):
    driver = FakeGdGpDriver(
        read_fixture("search_found.json"),
        read_fixture("detail_found.json"),
    )
    adapter = GdGpAdapter(
        get_descriptor(PlatformId.GD_GP),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.FOUND
    assert len(result.hits) == 1
    assert result.hits[0].title == "惠州市算力中心服务器采购项目结果公告"
    assert {item.kind for item in result.artifacts} == {
        "result-page",
        "detail-api-page",
        "detail-metadata",
        "detail-page",
    }
    assert all(not item.simulation for item in result.artifacts)


@pytest.mark.asyncio
async def test_adapter_not_found_requires_official_empty_rows(tmp_path: Path):
    driver = FakeGdGpDriver(read_fixture("search_not_found.json"))
    adapter = GdGpAdapter(
        get_descriptor(PlatformId.GD_GP),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request("不存在的项目"), tmp_path)

    assert result.status == PlatformRunStatus.NOT_FOUND
    assert result.hits == []
    assert len(result.artifacts) == 1


@pytest.mark.asyncio
async def test_portal_capture_failure_is_partial_not_found(tmp_path: Path):
    driver = FakeGdGpDriver(
        read_fixture("search_found.json"),
        read_fixture("detail_found.json"),
        portal_error=RuntimeError("portal route returned 403"),
    )
    adapter = GdGpAdapter(
        get_descriptor(PlatformId.GD_GP),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.PARTIAL
    assert len(result.hits) == 1
    assert any(item.kind == "execution-diagnostics" for item in result.artifacts)
    assert result.retryable


@pytest.mark.asyncio
async def test_invalid_search_contract_is_page_changed(tmp_path: Path):
    driver = FakeGdGpDriver('{"code":"500","msg":"系统异常"}')
    adapter = GdGpAdapter(
        get_descriptor(PlatformId.GD_GP),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.PAGE_CHANGED
    assert result.error_code == "PAGE_CONTRACT_MISMATCH"
