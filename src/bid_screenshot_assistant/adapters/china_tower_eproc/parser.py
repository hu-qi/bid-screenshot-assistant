from __future__ import annotations

import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from bid_screenshot_assistant.adapters.profiles import (
    CHINA_TOWER_EPROC_PROFILE,
    PlatformBrowserProfile,
)

from .models import TowerDetail, TowerListEntry

_DATE_PATTERNS = (
    re.compile(r"信息时间[：:\s]*([12]\d{3}-\d{1,2}-\d{1,2})"),
    re.compile(r"信息时间[：:\s]*([12]\d{3}/\d{1,2}/\d{1,2})"),
    re.compile(r"信息时间[：:\s]*([12]\d{3}年\d{1,2}月\d{1,2}日)"),
)
_GENERIC_DATE = re.compile(r"([12]\d{3}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)")
_ATTACHMENT_SUFFIXES = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar")
_NO_RESULT_MARKERS = ("暂无数据", "暂无相关数据", "未查询到相关公告", "无匹配数据")


class PageContractError(RuntimeError):
    """The current page does not match the verified public-page contract."""


def normalized_text(value: str) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def _normalized_match_text(value: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", (value or "").lower())


def _parse_date(value: str) -> datetime | None:
    cleaned = value.strip().replace("年", "-").replace("月", "-").replace("日", "")
    cleaned = cleaned.replace("/", "-").replace(".", "-")
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def find_date(text: str) -> datetime | None:
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return _parse_date(match.group(1))
    match = _GENERIC_DATE.search(text)
    return _parse_date(match.group(1)) if match else None


def match_score(query_name: str, title: str) -> tuple[float, str]:
    query = _normalized_match_text(query_name)
    candidate = _normalized_match_text(title)
    if not query or not candidate:
        return 0.0, "empty normalized text"
    if query == candidate:
        return 1.0, "normalized exact match"
    if query in candidate:
        return 0.98, "query is contained in announcement title"
    return SequenceMatcher(None, query, candidate).ratio(), "normalized sequence similarity"


def parse_list_page(
    html: str,
    profile: PlatformBrowserProfile = CHINA_TOWER_EPROC_PROFILE,
) -> list[TowerListEntry]:
    soup = BeautifulSoup(html or "", "html.parser")
    entries: list[TowerListEntry] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = str(link.get("href") or "").strip()
        absolute_url = urljoin(profile.search_url, href)
        if absolute_url in seen_urls or not profile.matches_detail_url(absolute_url):
            continue
        title = normalized_text(link.get_text(" ", strip=True))
        if not title:
            title = normalized_text(str(link.get("title") or ""))
        if not title:
            continue
        container = link.find_parent(["li", "tr", "article", "div"]) or link.parent
        context_text = normalized_text(container.get_text(" ", strip=True)) if container else title
        entries.append(
            TowerListEntry(title=title, url=absolute_url, published_at=find_date(context_text))
        )
        seen_urls.add(absolute_url)
    return entries


def has_explicit_no_results(html_or_text: str) -> bool:
    soup = BeautifulSoup(html_or_text or "", "html.parser")
    text = normalized_text(soup.get_text(" ", strip=True))
    return any(marker in text for marker in _NO_RESULT_MARKERS)


def parse_detail_page(
    html: str,
    source_url: str,
    profile: PlatformBrowserProfile = CHINA_TOWER_EPROC_PROFILE,
) -> TowerDetail:
    if not profile.matches_detail_url(source_url):
        raise PageContractError("Detail URL is outside the verified China Tower pattern")

    soup = BeautifulSoup(html or "", "html.parser")
    body_text = normalized_text(soup.get_text(" ", strip=True))
    if "信息时间" not in body_text:
        raise PageContractError("Detail page fingerprint is missing 信息时间")

    title = _extract_title(soup)
    if not title:
        raise PageContractError("Detail page title could not be extracted")

    attachments: list[str] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        href = str(link.get("href") or "").strip()
        absolute_url = urljoin(source_url, href)
        if not profile.is_allowed_host(absolute_url):
            continue
        label = normalized_text(link.get_text(" ", strip=True)).lower()
        path = absolute_url.lower().split("?", 1)[0]
        if "附件" not in label and not path.endswith(_ATTACHMENT_SUFFIXES):
            continue
        if absolute_url in seen:
            continue
        attachments.append(absolute_url)
        seen.add(absolute_url)

    return TowerDetail(
        title=title,
        published_at=find_date(body_text),
        body_text=body_text,
        attachment_urls=tuple(attachments),
    )


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in ("h1", "h2", "h3", ".article-title", ".detail-title", ".title"):
        for node in soup.select(selector):
            candidate = normalized_text(node.get_text(" ", strip=True))
            if len(candidate) >= 8 and candidate not in {"公告公示", "采购公告"}:
                return candidate
    lines = [normalized_text(line) for line in soup.get_text("\n").splitlines()]
    return next(
        (
            line
            for line in lines
            if len(line) >= 8
            and "信息时间" not in line
            and line not in {"公告公示", "采购公告"}
        ),
        "",
    )
