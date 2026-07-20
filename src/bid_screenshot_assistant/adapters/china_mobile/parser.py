from __future__ import annotations

import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from bid_screenshot_assistant.adapters.profiles import (
    CHINA_MOBILE_PROFILE,
    PlatformBrowserProfile,
)

from .models import MobileDetail, MobileListEntry

_DATE_PATTERNS = (
    re.compile(r"(?:发布时间|发布日期|公告时间)[：:\s]*([12]\d{3}-\d{1,2}-\d{1,2})"),
    re.compile(r"(?:发布时间|发布日期|公告时间)[：:\s]*([12]\d{3}/\d{1,2}/\d{1,2})"),
    re.compile(r"(?:发布时间|发布日期|公告时间)[：:\s]*([12]\d{3}年\d{1,2}月\d{1,2}日)"),
)
_GENERIC_DATE = re.compile(r"([12]\d{3}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)")
_ATTACHMENT_SUFFIXES = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar")
_NO_RESULT_MARKERS = ("无匹配数据", "暂无数据", "暂无相关公告", "未查询到相关公告")
_ERROR_MARKERS = ("系统异常", "请求错误", "服务暂不可用", "访问过于频繁", "请稍后重试")
_NOTICE_TYPES = (
    "招标公告",
    "采购公告",
    "资格预审公告",
    "候选人公示",
    "中选候选人公示",
    "中标候选人公示",
    "中选结果公示",
    "中标结果公示",
    "供应商公告",
)


class PageContractError(RuntimeError):
    """The page does not match the verified/candidate China Mobile contract."""


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
    profile: PlatformBrowserProfile = CHINA_MOBILE_PROFILE,
) -> list[MobileListEntry]:
    soup = BeautifulSoup(html or "", "html.parser")
    entries: list[MobileListEntry] = []
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
            MobileListEntry(
                title=title,
                url=absolute_url,
                published_at=find_date(context_text),
                notice_type=_find_notice_type(context_text),
            )
        )
        seen_urls.add(absolute_url)
    return entries


def has_explicit_no_results(html_or_text: str) -> bool:
    soup = BeautifulSoup(html_or_text or "", "html.parser")
    text = normalized_text(soup.get_text(" ", strip=True))
    return any(marker in text for marker in _NO_RESULT_MARKERS)


def is_error_page(html_or_text: str) -> bool:
    soup = BeautifulSoup(html_or_text or "", "html.parser")
    text = normalized_text(soup.get_text(" ", strip=True))
    return any(marker in text for marker in _ERROR_MARKERS)


def parse_detail_page(
    html: str,
    source_url: str,
    profile: PlatformBrowserProfile = CHINA_MOBILE_PROFILE,
) -> MobileDetail:
    if not profile.matches_detail_url(source_url):
        raise PageContractError("Detail URL is outside the candidate China Mobile patterns")

    soup = BeautifulSoup(html or "", "html.parser")
    body_text = normalized_text(soup.get_text(" ", strip=True))
    if is_error_page(body_text):
        raise PageContractError("China Mobile detail page returned an explicit error state")

    title = _extract_title(soup)
    if not title:
        raise PageContractError("China Mobile detail title could not be extracted")
    if len(body_text) < 30:
        raise PageContractError("China Mobile detail body is unexpectedly short")

    attachments: list[str] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        href = str(link.get("href") or "").strip()
        absolute_url = urljoin(source_url, href)
        parsed = urlsplit(absolute_url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or hostname not in profile.allowed_hosts:
            continue
        label = normalized_text(link.get_text(" ", strip=True)).lower()
        path = parsed.path.lower()
        is_download_path = path.endswith("/commondownload.html")
        if "附件" not in label and not is_download_path and not path.endswith(_ATTACHMENT_SUFFIXES):
            continue
        if absolute_url in seen:
            continue
        attachments.append(absolute_url)
        seen.add(absolute_url)

    return MobileDetail(
        title=title,
        published_at=find_date(body_text),
        notice_type=_find_notice_type(body_text),
        body_text=body_text,
        attachment_urls=tuple(attachments),
    )


def _find_notice_type(text: str) -> str | None:
    return next((notice_type for notice_type in _NOTICE_TYPES if notice_type in text), None)


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in (
        "h1",
        "h2",
        "h3",
        ".article-title",
        ".notice-title",
        ".detail-title",
        ".title",
    ):
        for node in soup.select(selector):
            candidate = normalized_text(node.get_text(" ", strip=True))
            if len(candidate) >= 8 and candidate not in {"招标采购公告", "采购公告"}:
                return candidate
    lines = [normalized_text(line) for line in soup.get_text("\n").splitlines()]
    return next(
        (
            line
            for line in lines
            if len(line) >= 8
            and not any(marker in line for marker in ("发布时间", "发布日期"))
            and line not in {"招标采购公告", "采购公告"}
        ),
        "",
    )
