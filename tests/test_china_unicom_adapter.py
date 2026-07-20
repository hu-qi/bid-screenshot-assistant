from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters import get_descriptor
from bid_screenshot_assistant.adapters.china_unicom import ChinaUnicomAdapter
from bid_screenshot_assistant.adapters.china_unicom.models import BrowserSnapshot
from bid_screenshot_assistant.adapters.profiles import CHINA_UNICOM_PROFILE
from bid_screenshot_assistant.domain.models import (
    AdapterRequest,
    PlatformId,
    PlatformRunStatus,
)

FIXTURES = Path(__file__).parent / "fixtures" / "china_unicom"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeUnicomDriver:
    def __init__(self, search_html: str, detail_html: str | None = None, detail_error=None):
        self.search_html = search_html
        self.detail_html = detail_html
        self.detail_error = detail_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def search(self, query_name: str) -> BrowserSnapshot:
        return BrowserSnapshot(
            url=CHINA_UNICOM_PROFILE.search_url,
            html=self.search_html,
            body_text=self.search_html,
            screenshot=b"search-png",
        )

    async def fetch_detail(self, url: str) -> BrowserSnapshot:
        if self.detail_error:
            raise self.detail_error
        return BrowserSnapshot(
            url=url,
            html=self.detail_html or "",
            body_text=self.detail_html or "",
            screenshot=b"detail-png",
        )


def build_request(query_name: str = "智慧工厂") -> AdapterRequest:
    return AdapterRequest(
        task_id="task-1",
        run_id="run-1",
        query_id="query-1",
        query_name=query_name,
        platform_id=PlatformId.CHINA_UNICOM,
        max_hits=1,
    )


@pytest.mark.asyncio
async def test_adapter_found_writes_non_simulation_evidence(tmp_path: Path):
    driver = FakeUnicomDriver(
        read_fixture("list_found.html"),
        detail_html=read_fixture("detail_found.html"),
    )
    adapter = ChinaUnicomAdapter(
        get_descriptor(PlatformId.CHINA_UNICOM),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.FOUND
    assert len(result.hits) == 1
    assert result.hits[0].title.startswith("2026江苏产互")
    assert {item.kind for item in result.artifacts} == {
        "result-page",
        "detail-page",
        "detail-metadata",
    }
    assert all(not item.simulation for item in result.artifacts)


@pytest.mark.asyncio
async def test_adapter_not_found_requires_explicit_marker(tmp_path: Path):
    driver = FakeUnicomDriver(read_fixture("list_not_found.html"))
    adapter = ChinaUnicomAdapter(
        get_descriptor(PlatformId.CHINA_UNICOM),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request("不存在的项目"), tmp_path)

    assert result.status == PlatformRunStatus.NOT_FOUND
    assert result.hits == []
    assert len(result.artifacts) == 1


@pytest.mark.asyncio
async def test_adapter_501_is_page_changed_not_not_found(tmp_path: Path):
    driver = FakeUnicomDriver(read_fixture("list_501.html"))
    adapter = ChinaUnicomAdapter(
        get_descriptor(PlatformId.CHINA_UNICOM),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.PAGE_CHANGED
    assert result.error_code == "PAGE_CONTRACT_MISMATCH"
    assert result.status != PlatformRunStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_adapter_preserves_list_hit_when_detail_fails(tmp_path: Path):
    driver = FakeUnicomDriver(
        read_fixture("list_found.html"),
        detail_error=RuntimeError("detail unavailable"),
    )
    adapter = ChinaUnicomAdapter(
        get_descriptor(PlatformId.CHINA_UNICOM),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.PARTIAL
    assert len(result.hits) == 1
    assert any(item.kind == "execution-diagnostics" for item in result.artifacts)
    assert result.retryable


@pytest.mark.asyncio
async def test_ambiguous_empty_page_is_page_changed(tmp_path: Path):
    driver = FakeUnicomDriver(
        "<html><body><h1>搜索公告</h1><input placeholder='请输入公告关键词'></body></html>"
    )
    adapter = ChinaUnicomAdapter(
        get_descriptor(PlatformId.CHINA_UNICOM),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.PAGE_CHANGED
    assert not result.retryable
