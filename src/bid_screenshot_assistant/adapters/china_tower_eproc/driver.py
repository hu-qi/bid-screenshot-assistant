from __future__ import annotations

import re
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import Callable, Protocol

from bid_screenshot_assistant.adapters.profiles import (
    CHINA_TOWER_EPROC_PROFILE,
    PlatformBrowserProfile,
)

from .models import BrowserSnapshot
from .parser import PageContractError, normalized_text


class TowerBrowserDriver(Protocol):
    async def search(self, query_name: str) -> BrowserSnapshot: ...

    async def fetch_detail(self, url: str) -> BrowserSnapshot: ...


TowerDriverFactory = Callable[[], AbstractAsyncContextManager[TowerBrowserDriver]]


class PlaywrightTowerDriver:
    def __init__(
        self,
        profile: PlatformBrowserProfile = CHINA_TOWER_EPROC_PROFILE,
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

    async def __aenter__(self) -> PlaywrightTowerDriver:
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
                str(self.user_data_dir), headless=self.headless
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
        await page.goto(self.profile.search_url, wait_until="domcontentloaded")
        await self._wait_after_navigation(page)
        list_text = normalized_text(await page.locator("body").inner_text())
        self._verify_text(self.profile.list_fingerprint.required_text, list_text, "list")

        await page.get_by_placeholder(self.profile.search_placeholders[0]).first.fill(query_name)
        await page.get_by_role("button", name=re.compile(r"查\s*询")).first.click()
        await self._wait_after_navigation(page)
        return await self._snapshot(page)

    async def fetch_detail(self, url: str) -> BrowserSnapshot:
        if not self.profile.matches_detail_url(url):
            raise PageContractError(f"Blocked unverified detail URL: {url}")
        if self._context is None:
            raise RuntimeError("Driver is not started")
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await self._wait_after_navigation(page)
            body_text = normalized_text(await page.locator("body").inner_text())
            self._verify_text(self.profile.detail_fingerprint.required_text, body_text, "detail")
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
            # Public pages may retain polling connections; fingerprints remain decisive.
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

    @staticmethod
    def _verify_text(required: tuple[str, ...], text: str, page_type: str) -> None:
        for marker in required:
            if marker not in text:
                raise PageContractError(f"{page_type} page fingerprint missing: {marker}")
