from __future__ import annotations

import asyncio
import re
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from time import monotonic
from typing import Callable, Protocol

from bid_screenshot_assistant.adapters.profiles import CEBPUBSERVICE_PROFILE, PlatformBrowserProfile

from .models import BrowserSnapshot
from .parser import CaptchaRequiredError, PageContractError, has_captcha, normalized_text


class CebBrowserDriver(Protocol):
    async def search(self, query_name: str) -> BrowserSnapshot: ...

    async def fetch_detail(self, url: str) -> BrowserSnapshot: ...


CebDriverFactory = Callable[[], AbstractAsyncContextManager[CebBrowserDriver]]


class PlaywrightCebDriver:
    def __init__(
        self,
        profile: PlatformBrowserProfile = CEBPUBSERVICE_PROFILE,
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

    async def __aenter__(self) -> PlaywrightCebDriver:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed. Install browser extras.") from exc
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
        await self._wait(page)
        initial_text = normalized_text(await page.locator("body").inner_text())
        if has_captcha(initial_text):
            raise CaptchaRequiredError("Captcha is blocking the public search page")
        self._verify_list_page(initial_text)

        search_input = await self._find_search_input(page)
        if search_input is None:
            raise PageContractError("CEB keyword input could not be located semantically")
        url_before = page.url
        link_count_before = await self._detail_links(page).count()
        await search_input.fill(query_name)
        await self._submit(page, search_input)
        await self._wait(page)
        completed, signal = await self._wait_for_completion(
            page, query_name, url_before, link_count_before
        )
        text = normalized_text(await page.locator("body").inner_text())
        if has_captcha(text):
            raise CaptchaRequiredError("Captcha appeared after submitting the search")
        return await self._snapshot(page, completed, signal)

    async def fetch_detail(self, url: str) -> BrowserSnapshot:
        if not self.profile.matches_detail_url(url):
            raise PageContractError(f"Blocked unverified detail URL: {url}")
        if self._context is None:
            raise RuntimeError("Driver is not started")
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await self._wait(page)
            text = normalized_text(await page.locator("body").inner_text())
            if has_captcha(text):
                raise CaptchaRequiredError("Captcha appeared on the detail page")
            if "发布日期" not in text:
                raise PageContractError("CEB detail page is missing 发布日期")
            return await self._snapshot(page, True, "detail_loaded")
        finally:
            await page.close()

    async def _find_search_input(self, page):
        for placeholder in self.profile.search_placeholders:
            locator = page.get_by_placeholder(placeholder).first
            try:
                if await locator.count() and await locator.is_visible():
                    return locator
            except Exception:
                pass
        candidates = page.locator("input[type='text']:visible")
        count = await candidates.count()
        for index in range(min(count, 10)):
            locator = candidates.nth(index)
            try:
                attrs = " ".join(
                    filter(
                        None,
                        [
                            await locator.get_attribute("placeholder"),
                            await locator.get_attribute("name"),
                            await locator.get_attribute("id"),
                        ],
                    )
                )
                if any(token in attrs.lower() for token in ("key", "keyword", "search", "关键")):
                    return locator
            except Exception:
                continue
        return None

    async def _submit(self, page, search_input) -> None:
        for label in self.profile.submit_labels:
            button = page.get_by_role("button", name=re.compile(label)).first
            try:
                if await button.count() and await button.is_visible():
                    await button.click()
                    return
            except Exception:
                pass
        await search_input.press("Enter")

    async def _wait_for_completion(self, page, query_name, url_before, count_before):
        deadline = monotonic() + min(self.timeout_ms, 15_000) / 1000
        while monotonic() < deadline:
            text = normalized_text(await page.locator("body").inner_text())
            if has_captcha(text):
                raise CaptchaRequiredError("Captcha appeared while waiting for search results")
            count = await self._detail_links(page).count()
            if page.url != url_before:
                return True, "url_changed"
            if count != count_before:
                return True, "detail_link_count_changed"
            if query_name in text:
                return True, "query_rendered"
            await asyncio.sleep(0.25)
        return False, "search_completion_unverified"

    def _detail_links(self, page):
        return page.locator(
            "a[href*='biddingBulletin/'], a[href*='qualifyBulletin/'], "
            "a[href*='candidateBulletin/'], a[href*='resultBulletin/'], "
            "a[href*='changeBulletin/']"
        )

    def _verify_list_page(self, text: str) -> None:
        if "招标公告" not in text:
            raise PageContractError("CEB search page fingerprint missing 招标公告")
        if not any(marker in text for marker in ("全文检索", "高级搜索", "关键字", "发布时间")):
            raise PageContractError("CEB search page search controls are missing")

    async def _snapshot(self, page, completed: bool, signal: str) -> BrowserSnapshot:
        if not self.profile.is_allowed_host(page.url):
            raise PageContractError(f"Navigation left the official host: {page.url}")
        return BrowserSnapshot(
            url=page.url,
            html=await page.content(),
            body_text=await page.locator("body").inner_text(),
            screenshot=await page.screenshot(full_page=True, type="png"),
            search_completed=completed,
            completion_signal=signal,
        )

    async def _wait(self, page) -> None:
        await page.wait_for_load_state("domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=min(self.timeout_ms, 15_000))
        except Exception:
            pass

    def _require_page(self):
        if self._page is None:
            raise RuntimeError("Driver is not started")
        return self._page
