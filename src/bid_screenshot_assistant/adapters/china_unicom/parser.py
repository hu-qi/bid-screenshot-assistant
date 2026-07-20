from __future__ import annotations

import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from bid_screenshot_assistant.adapters.profiles import CHINA_UNICOM_PROFILE, PlatformBrowserProfile

from .models import UnicomDetail, UnicomListEntry

_PUBLISHED_AT = re.compile(
    r"发布时间[：:\s]*([12]\d{3}-\d{1,2}-\d{1,2}(?:\s+\d{1,2}:\d{2}:\d{2})?)"
)
_GENERIC_DATE = re.compile(r"([12]\d{3}-\d{1,2}-\d{1,2})")
_BID_NUMBER = re.compile(
    r"(?:招标编号|采购项目编号|采购代理编号)[：:\s]*([^\s，,；;。]{3,100})"
)
_ATTACHMENT_SUFFIXES = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar")
_UNHYDRATED_MARKERS = (
    "请求错误，请联系管理员。错误码：501",
    "请开启JavaScript",
    "please enable javascript",
)


class PageContractError(RuntimeError):
    """The current Unicom page does not satisfy the verified public contract."""


def normalized_text(value: str) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def _normalized_match_text(value: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", (value or "").lower())


def parse_datetime(value: str) -> datetime | None:
    cleaned = normalized_text(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def find_published_at(text: str) -> datetime | None:
    match = _PUBLISHED_AT.search(text)
    if match:
        return parse_datetime(match.group(1))
    match = _GENERIC_DATE.search(text)
    return parse_datetime(match.group(1)) if match else None


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


def is_unhydrated_or_error(html_or_text: str) -> bool:
    soup = BeautifulSoup(html_or_text or "", "html.parser")
    text = normalized_text(soup.get_text(" ", strip=True)).lower()
    return any(marker.lower() in text for marker in _UNHYDRATED_MARKERS)


def has_explicit_no_results(
    html_or_text: str,
    profile: PlatformBrowserProfile = CHINA_UNICOM_PROFILE,
) -> bool:
    soup = BeautifulSoup(html_or_text or "", "html.parser")
    text = normalized_text(soup.get_text(" ", strip=True))
    return any(marker in text for marker in profile.no_result_markers)


def parse_list_page(
    html: str,
    profile: PlatformBrowserProfile = CHINA_UNICOM_PROFILE,
) -> list[UnicomListEntry]:
    if is_unhydrated_or_error(html):
        raise PageContractError("Unicom list page is unhydrated or returned error 501")

    soup = BeautifulSoup(html or "", "html.parser")
    entries: list[UnicomListEntry] = []
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
        context = normalized_text(container.get_text(" ", strip=True)) if container else title
        entries.append(
            UnicomListEntry(
                title=title,
                url=absolute_url,
                published_at=find_published_at(context),
            )
        )
        seen_urls.add(absolute_url)
    return entries


def parse_detail_page(
    html: str,
    source_url: str,
    profile: PlatformBrowserProfile = CHINA_UNICOM_PROFILE,
) -> UnicomDetail:
    if not profile.matches_detail_url(source_url):
        raise PageContractError("Detail URL is outside the verified China Unicom pattern")
    if is_unhydrated_or_error(html):
        raise PageContractError("Unicom detail page is unhydrated or returned error 501")

    soup = BeautifulSoup(html or "", "html.parser")
    body_text = normalized_text(soup.get_text(" ", strip=True))
    published_at = find_published_at(body_text)
    if published_at is None or "发布时间" not in body_text:
        raise PageContractError("Detail page fingerprint is missing 发布时间")

    title = _extract_title(soup)
    if not title:
        raise PageContractError("Detail page title could not be extracted")

    number_match = _BID_NUMBER.search(body_text)
    bid_number = normalized_text(number_match.group(1)) if number_match else None

    attachment_urls: list[str] = []
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
        attachment_urls.append(absolute_url)
        seen.add(absolute_url)

    return UnicomDetail(
        title=title,
        bid_number=bid_number,
        published_at=published_at,
        body_text=body_text,
        attachment_urls=tuple(attachment_urls),
    )


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in ("h1", "h2", ".ant-typography", ".detail-title", ".title"):
        for node in soup.select(selector):
            candidate = normalized_text(node.get_text(" ", strip=True))
            if len(candidate) >= 8 and candidate not in {"招标详情", "采购与招标网"}:
                return candidate
    lines = [normalized_text(line) for line in soup.get_text("\n").splitlines()]
    return next(
        (
            line
            for line in lines
            if len(line) >= 8
            and "发布时间" not in line
            and "招标编号" not in line
            and line not in {"招标详情", "采购与招标网"}
        ),
        "",
    )
