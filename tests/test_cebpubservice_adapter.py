from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters import get_descriptor
from bid_screenshot_assistant.adapters.cebpubservice import CebpubserviceAdapter
from bid_screenshot_assistant.adapters.cebpubservice.models import BrowserSnapshot
from bid_screenshot_assistant.adapters.profiles import CEBPUBSERVICE_PROFILE
from bid_screenshot_assistant.domain.models import AdapterRequest, PlatformId, PlatformRunStatus

FIXTURES = Path(__file__).parent / "fixtures" / "cebpubservice"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeCebDriver:
    def __init__(
        self,
        search_html: str,
        detail_html: str | None = None,
        detail_error=None,
        *,
        search_completed: bool = True,
    ):
        self.search_html = search_html
        self.detail_html = detail_html
        self.detail_error = detail_error
        self.search_completed = search_completed

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def search(self, query_name: str) -> BrowserSnapshot:
        return BrowserSnapshot(
            url=CEBPUBSERVICE_PROFILE.search_url,
            html=self.search_html,
            body_text=self.search_html,
            screenshot=b"search-png",
            search_completed=self.search_completed,
            completion_signal="fixture_search_complete" if self.search_completed else "",
        )

    async def fetch_detail(self, url: str) -> BrowserSnapshot:
        if self.detail_error:
            raise self.detail_error
        return BrowserSnapshot(
            url=url,
            html=self.detail_html or "",
            body_text=self.detail_html or "",
            screenshot=b"detail-png",
            search_completed=True,
            completion_signal="detail_loaded",
        )


def build_request(query_name: str = "智慧园区") -> AdapterRequest:
    return AdapterRequest(
        task_id="task-1",
        run_id="run-1",
        query_id="query-1",
        query_name=query_name,
        platform_id=PlatformId.CEBPUBSERVICE,
        max_hits=1,
    )


@pytest.mark.asyncio
async def test_ceb_adapter_found(tmp_path: Path):
    driver = FakeCebDriver(
        read_fixture("list_found.html"),
        detail_html=read_fixture("detail_found.html"),
    )
    adapter = CebpubserviceAdapter(
        get_descriptor(PlatformId.CEBPUBSERVICE), driver_factory=lambda: driver
    )
    result = await adapter.execute(build_request(), tmp_path)
    assert result.status == PlatformRunStatus.FOUND
    assert len(result.hits) == 1
    assert all(not artifact.simulation for artifact in result.artifacts)
    assert {artifact.kind for artifact in result.artifacts} == {
        "result-page",
        "execution-diagnostics",
        "detail-page",
        "detail-metadata",
    }


@pytest.mark.asyncio
async def test_ceb_adapter_not_found_requires_completed_search(tmp_path: Path):
    driver = FakeCebDriver(read_fixture("list_not_found.html"), search_completed=True)
    adapter = CebpubserviceAdapter(
        get_descriptor(PlatformId.CEBPUBSERVICE), driver_factory=lambda: driver
    )
    result = await adapter.execute(build_request("不存在的项目"), tmp_path)
    assert result.status == PlatformRunStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_ceb_ambiguous_empty_page_is_page_changed(tmp_path: Path):
    driver = FakeCebDriver(read_fixture("list_not_found.html"), search_completed=False)
    adapter = CebpubserviceAdapter(
        get_descriptor(PlatformId.CEBPUBSERVICE), driver_factory=lambda: driver
    )
    result = await adapter.execute(build_request("不存在的项目"), tmp_path)
    assert result.status == PlatformRunStatus.PAGE_CHANGED
    assert result.status != PlatformRunStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_ceb_captcha_stops_for_manual_action(tmp_path: Path):
    driver = FakeCebDriver(read_fixture("list_captcha.html"), search_completed=False)
    adapter = CebpubserviceAdapter(
        get_descriptor(PlatformId.CEBPUBSERVICE), driver_factory=lambda: driver
    )
    result = await adapter.execute(build_request(), tmp_path)
    assert result.status == PlatformRunStatus.CAPTCHA_REQUIRED
    assert not result.retryable
    assert result.error_code == "CAPTCHA_REQUIRED"


@pytest.mark.asyncio
async def test_ceb_preserves_list_hit_when_detail_fails(tmp_path: Path):
    driver = FakeCebDriver(
        read_fixture("list_found.html"), detail_error=RuntimeError("detail unavailable")
    )
    adapter = CebpubserviceAdapter(
        get_descriptor(PlatformId.CEBPUBSERVICE), driver_factory=lambda: driver
    )
    result = await adapter.execute(build_request(), tmp_path)
    assert result.status == PlatformRunStatus.PARTIAL
    assert len(result.hits) == 1
    assert result.retryable
