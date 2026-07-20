from __future__ import annotations

import asyncio
import re
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from time import monotonic
from typing import Callable, Protocol
from urllib.parse import urlsplit

from bid_screenshot_assistant.adapters.profiles import CHINA_MOBILE_PROFILE, PlatformBrowserProfile

from .models import BrowserSnapshot
from .parser import PageContractError, is_error_page, normalized_text


class MobileBrowserDriver(Protocol):
    async def search(self, query_name: str) -> BrowserSnapshot: ...

    async def fetch_detail(self, url: str) -> BrowserSnapshot: ...


MobileDriverFactory = Callable[[], AbstractAsyncContextManager[MobileBrowserDriver]]


class PlaywrightMobileDriver:
    def __init__(
        self,
        profile: PlatformBrowserProfile = CHINA_MOBILE_PROFILE,
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

    async def __aenter__(self) -> PlaywrightMobileDriver:
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
        await page.goto(self.profile.search_url, wait_until="domcontentloaded")
        await self._wait_after_navigation(page)

        placeholder = self.profile.search_placeholders[0]
        search_input = page.get_by_placeholder(placeholder).first
        try:
            await search_input.wait_for(state="visible")
        except Exception as exc:
            raise PageContractError("China Mobile search input is not visible") from exc

        body_before = normalized_text(await page.locator("body").inner_text())
        self._verify_text(self.profile.list_fingerprint.required_text, body_before, "list")
        if is_error_page(body_before):
            raise PageContractError("China Mobile homepage returned an explicit error state")

        url_before = page.url
        detail_count_before = await self._detail_links(page).count()
        response_urls: list[str] = []

        def record_response(response) -> None:
            try:
                parsed = urlsplit(response.url)
                resource_type = response.request.resource_type
                lower_url = response.url.lower()
                if (
                    parsed.hostname == "b2b.10086.cn"
                    and resource_type in {"xhr", "fetch", "document"}
                    and any(token in lower_url for token in ("notice", "search", "list"))
                ):
                    response_urls.append(response.url)
            except Exception:
                return

        page.on("response", record_response)
        await search_input.fill(query_name)
        await self._submit_search(page, search_input)
        await self._wait_after_navigation(page)

        completed, signal = await self._wait_for_search_completion(
            page=page,
            search_input=search_input,
            query_name=query_name,
            url_before=url_before,
            body_before=body_before,
            detail_count_before=detail_count_before,
            response_urls=response_urls,
        )
        return await self._snapshot(
            page,
            search_completed=completed,
            completion_signal=signal,
            response_urls=tuple(dict.fromkeys(response_urls)),
        )

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
            if is_error_page(body_text):
                raise PageContractError("China Mobile detail page returned an error state")
            return await self._snapshot(page)
        finally:
            await page.close()

    async def _submit_search(self, page, search_input) -> None:
        button = page.get_by_role("button", name=re.compile(r"搜\s*索")).first
        try:
            if await button.count() > 0 and await button.is_visible():
                await button.click()
                return
        except Exception:
            pass
        await search_input.press("Enter")

    async def _wait_for_search_completion(
        self,
        *,
        page,
        search_input,
        query_name: str,
        url_before: str,
        body_before: str,
        detail_count_before: int,
        response_urls: list[str],
    ) -> tuple[bool, str]:
        deadline = monotonic() + min(self.timeout_ms, 15_000) / 1000
        while monotonic() < deadline:
            try:
                input_value = await search_input.input_value()
                body_text = normalized_text(await page.locator("body").inner_text())
                detail_count = await self._detail_links(page).count()
                if input_value == query_name:
                    if page.url != url_before:
                        return True, "url_changed"
                    if detail_count != detail_count_before:
                        return True, "detail_link_count_changed"
                    if response_urls:
                        return True, "notice_network_response"
                    if query_name in body_text and query_name not in body_before:
                        return True, "query_rendered_in_result_region"
            except Exception:
                pass
            await asyncio.sleep(0.25)
        return False, "search_completion_unverified"

    def _detail_links(self, page):
        return page.locator(
            "a[href*='viewNoticeContent.html'], "
            "a[href*='viewVendorNoticeContent.html']"
        )

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

    async def _snapshot(
        self,
        page,
        *,
        search_completed: bool = False,
        completion_signal: str = "",
        response_urls: tuple[str, ...] = (),
    ) -> BrowserSnapshot:
        if not self.profile.is_allowed_host(page.url):
            raise PageContractError(f"Navigation left the official host: {page.url}")
        return BrowserSnapshot(
            url=page.url,
            html=await page.content(),
            body_text=await page.locator("body").inner_text(),
            screenshot=await page.screenshot(full_page=True, type="png"),
            search_completed=search_completed,
            completion_signal=completion_signal,
            response_urls=response_urls,
        )

    @staticmethod
    def _verify_text(required: tuple[str, ...], text: str, page_type: str) -> None:
        for marker in required:
            if marker not in text:
                raise PageContractError(f"{page_type} page fingerprint missing: {marker}")
