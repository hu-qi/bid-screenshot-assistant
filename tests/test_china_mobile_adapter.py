from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters import get_descriptor
from bid_screenshot_assistant.adapters.china_mobile import ChinaMobileAdapter
from bid_screenshot_assistant.adapters.china_mobile.models import BrowserSnapshot
from bid_screenshot_assistant.adapters.profiles import CHINA_MOBILE_PROFILE
from bid_screenshot_assistant.domain.models import (
    AdapterRequest,
    PlatformId,
    PlatformRunStatus,
)

FIXTURES = Path(__file__).parent / "fixtures" / "china_mobile"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeMobileDriver:
    def __init__(
        self,
        search_html: str,
        detail_html: str | None = None,
        detail_error=None,
        *,
        search_completed: bool = True,
        completion_signal: str = "fake_search_response",
    ):
        self.search_html = search_html
        self.detail_html = detail_html
        self.detail_error = detail_error
        self.search_completed = search_completed
        self.completion_signal = completion_signal

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def search(self, query_name: str) -> BrowserSnapshot:
        return BrowserSnapshot(
            url=CHINA_MOBILE_PROFILE.search_url,
            html=self.search_html,
            body_text=self.search_html,
            screenshot=b"search-png",
            search_completed=self.search_completed,
            completion_signal=self.completion_signal,
            response_urls=("https://b2b.10086.cn/search-notice",),
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


def build_request(query_name: str = "智慧园区") -> AdapterRequest:
    return AdapterRequest(
        task_id="task-1",
        run_id="run-1",
        query_id="query-1",
        query_name=query_name,
        platform_id=PlatformId.CHINA_MOBILE,
        max_hits=1,
    )


@pytest.mark.asyncio
async def test_mobile_adapter_found_writes_real_evidence(tmp_path: Path):
    driver = FakeMobileDriver(
        read_fixture("list_found.html"),
        detail_html=read_fixture("detail_found.html"),
    )
    adapter = ChinaMobileAdapter(
        get_descriptor(PlatformId.CHINA_MOBILE),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.FOUND
    assert len(result.hits) == 1
    assert result.hits[0].title.startswith("中国移动2026年智慧园区")
    assert {item.kind for item in result.artifacts} == {
        "result-page",
        "execution-diagnostics",
        "detail-page",
        "detail-metadata",
    }
    assert all(not item.simulation for item in result.artifacts)


@pytest.mark.asyncio
async def test_mobile_not_found_requires_completed_search(tmp_path: Path):
    driver = FakeMobileDriver(read_fixture("list_not_found.html"), search_completed=True)
    adapter = ChinaMobileAdapter(
        get_descriptor(PlatformId.CHINA_MOBILE),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request("不存在的项目"), tmp_path)

    assert result.status == PlatformRunStatus.NOT_FOUND
    assert result.hits == []
    assert len(result.artifacts) == 2


@pytest.mark.asyncio
async def test_mobile_initial_empty_state_is_not_not_found(tmp_path: Path):
    driver = FakeMobileDriver(read_fixture("list_not_found.html"), search_completed=False)
    adapter = ChinaMobileAdapter(
        get_descriptor(PlatformId.CHINA_MOBILE),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request("不存在的项目"), tmp_path)

    assert result.status == PlatformRunStatus.PAGE_CHANGED
    assert result.status != PlatformRunStatus.NOT_FOUND
    assert "completion" in (result.feedback or "").lower()


@pytest.mark.asyncio
async def test_mobile_preserves_list_hit_when_detail_fails(tmp_path: Path):
    driver = FakeMobileDriver(
        read_fixture("list_found.html"),
        detail_error=RuntimeError("detail unavailable"),
    )
    adapter = ChinaMobileAdapter(
        get_descriptor(PlatformId.CHINA_MOBILE),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.PARTIAL
    assert len(result.hits) == 1
    assert result.retryable
    assert any(item.relative_path.endswith("detail-errors.json") for item in result.artifacts)


@pytest.mark.asyncio
async def test_mobile_ambiguous_completed_page_is_page_changed(tmp_path: Path):
    html = "<html><body><h1>招标采购公告</h1><input placeholder='请输入公告标题包含的关键字'></body></html>"
    driver = FakeMobileDriver(html, search_completed=True)
    adapter = ChinaMobileAdapter(
        get_descriptor(PlatformId.CHINA_MOBILE),
        driver_factory=lambda: driver,
    )

    result = await adapter.execute(build_request(), tmp_path)

    assert result.status == PlatformRunStatus.PAGE_CHANGED
    assert not result.retryable
