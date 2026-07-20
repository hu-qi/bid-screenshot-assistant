from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Protocol
from urllib.parse import urlencode

from bid_screenshot_assistant.adapters.profiles import GD_GP_PROFILE, PlatformBrowserProfile

from .models import BrowserSnapshot
from .parser import PageContractError, normalized_text


class GdGpBrowserDriver(Protocol):
    async def search(self, query_name: str) -> BrowserSnapshot: ...

    async def fetch_detail_api(self, url: str) -> BrowserSnapshot: ...

    async def fetch_portal(self, url: str) -> BrowserSnapshot: ...


GdGpDriverFactory = Callable[[], AbstractAsyncContextManager[GdGpBrowserDriver]]


class PlaywrightGdGpDriver:
    def __init__(
        self,
        profile: PlatformBrowserProfile = GD_GP_PROFILE,
        *,
        headless: bool = True,
        timeout_ms: int = 45_000,
        user_data_dir: Path | None = None,
    ) -> None:
        self.profile = profile
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.user_data_dir = user_data_dir
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def __aenter__(self) -> PlaywrightGdGpDriver:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install the browser extra and Chromium."
            ) from exc

        self._playwright = await async_playwright().start()
        if self.user_data_dir:
            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            self._context = await self._playwright.chromium.launch_persistent_context(
                str(self.user_data_dir), headless=self.headless, locale="zh-CN"
            )
        else:
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context(locale="zh-CN")
        self._context.set_default_timeout(self.timeout_ms)
        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    async def search(self, query_name: str) -> BrowserSnapshot:
        page = self._require_page()
        await page.goto(self.profile.start_url, wait_until="domcontentloaded")
        await self._wait_after_navigation(page)
        if not self.profile.is_allowed_host(page.url):
            raise PageContractError(f"Landing navigation left the official host: {page.url}")

        params = {
            "currPage": 1,
            "pageSize": 20,
            "siteId": "cd64e06a-21a7-4620-aebc-0576bab7e07a",
            "channel": (
                "fca71be5-fc0c-45db-96af-f513e9abda9d,"
                "95ff31f3-a1af-4bc4-b1a2-54c894476193"
            ),
            "noticeType": "",
            "purchaser": "",
            "agency": "",
            "operationStartTime": "2000-01-01 00:00:00",
            "operationEndTime": datetime.now(UTC).strftime("%Y-%m-%d 23:59:59"),
            "searchKey": query_name,
            "regionCode": "",
            "selectTimeName": "noticeTime",
            "cityOrAreal": "",
            "requestSource": "qwjs",
            "purchaseManner": "",
        }
        url = f"{self.profile.search_url}?{urlencode(params)}"
        await page.goto(url, wait_until="domcontentloaded")
        await self._wait_after_navigation(page)
        return await self._snapshot(page)

    async def fetch_detail_api(self, url: str) -> BrowserSnapshot:
        if not self.profile.matches_detail_url(url) or "/gpcms/rest/" not in url:
            raise PageContractError(f"Blocked unverified detail API URL: {url}")
        if self._context is None:
            raise RuntimeError("Driver is not started")
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await self._wait_after_navigation(page)
            return await self._snapshot(page)
        finally:
            await page.close()

    async def fetch_portal(self, url: str) -> BrowserSnapshot:
        if not self.profile.matches_detail_url(url) or "/gpcms/rest/" in url:
            raise PageContractError(f"Blocked unverified portal URL: {url}")
        if self._context is None:
            raise RuntimeError("Driver is not started")
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await self._wait_after_navigation(page)
            text = normalized_text(await page.locator("body").inner_text())
            if not text or text in {"403", "404"} or "Access Denied" in text:
                raise PageContractError("Portal detail route was not directly accessible")
            return await self._snapshot(page)
        finally:
            await page.close()

    def _require_page(self):
        if self._page is None:
            raise RuntimeError("Driver is not started")
        return self._page

    async def _wait_after_navigation(self, page) -> None:
        await page.wait_for_load_state("domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=min(self.timeout_ms, 15_000))
        except Exception:
            pass

    async def _snapshot(self, page) -> BrowserSnapshot:
        if not self.profile.is_allowed_host(page.url):
            raise PageContractError(f"Navigation left the official host: {page.url}")
        return BrowserSnapshot(
            url=page.url,
            html=await page.content(),
            body_text=await page.locator("body").inner_text(),
            screenshot=await page.screenshot(full_page=True, type="png"),
        )
