from __future__ import annotations

import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from bid_screenshot_assistant.adapters.profiles import CEBPUBSERVICE_PROFILE, PlatformBrowserProfile

from .models import CebDetail, CebListEntry

_DATE_PATTERNS = (
    re.compile(r"发布日期[：:\s]*([12]\d{3}年\d{1,2}月\d{1,2}日)"),
    re.compile(r"发布日期[：:\s]*([12]\d{3}-\d{1,2}-\d{1,2})"),
)
_GENERIC_DATE = re.compile(r"([12]\d{3}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)")
_NO_RESULT_MARKERS = ("暂无数据", "未查询到相关公告", "没有符合条件的公告", "无匹配数据")
_CAPTCHA_MARKERS = ("请输入验证码", "图形验证码", "滑动验证", "拖动滑块", "安全验证", "访问验证")
_ERROR_MARKERS = ("系统异常", "请求错误", "服务暂不可用", "请稍后重试")
_NOTICE_TYPES = (
    "招标公告",
    "资格预审公告",
    "中标候选人公示",
    "中标结果公示",
    "更正公告公示",
)


class PageContractError(RuntimeError):
    pass


class CaptchaRequiredError(RuntimeError):
    pass


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
    profile: PlatformBrowserProfile = CEBPUBSERVICE_PROFILE,
) -> list[CebListEntry]:
    soup = BeautifulSoup(html or "", "html.parser")
    entries: list[CebListEntry] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        absolute_url = urljoin(profile.search_url, str(link.get("href") or "").strip())
        if absolute_url in seen or not profile.matches_detail_url(absolute_url):
            continue
        title = normalized_text(str(link.get("title") or "")) or normalized_text(
            link.get_text(" ", strip=True)
        )
        if not title:
            continue
        container = link.find_parent(["li", "tr", "article", "div"]) or link.parent
        context = normalized_text(container.get_text(" ", strip=True)) if container else title
        entries.append(
            CebListEntry(
                title=title,
                url=absolute_url,
                published_at=find_date(context),
                notice_type=_find_notice_type(context),
            )
        )
        seen.add(absolute_url)
    return entries


def has_explicit_no_results(value: str) -> bool:
    text = normalized_text(BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True))
    return any(marker in text for marker in _NO_RESULT_MARKERS)


def has_captcha(value: str) -> bool:
    text = normalized_text(BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True))
    return any(marker in text for marker in _CAPTCHA_MARKERS)


def is_error_page(value: str) -> bool:
    text = normalized_text(BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True))
    return any(marker in text for marker in _ERROR_MARKERS)


def parse_detail_page(
    html: str,
    source_url: str,
    profile: PlatformBrowserProfile = CEBPUBSERVICE_PROFILE,
) -> CebDetail:
    if not profile.matches_detail_url(source_url):
        raise PageContractError("Detail URL is outside the candidate CEB patterns")
    soup = BeautifulSoup(html or "", "html.parser")
    body_text = normalized_text(soup.get_text(" ", strip=True))
    if has_captcha(body_text):
        raise CaptchaRequiredError("Captcha appeared while reading a public detail page")
    if is_error_page(body_text):
        raise PageContractError("CEB detail page returned an explicit error state")
    title = _extract_title(soup)
    if not title:
        raise PageContractError("CEB detail title could not be extracted")
    if "发布日期" not in body_text or len(body_text) < 40:
        raise PageContractError("CEB detail fingerprint is incomplete")

    attachments: list[str] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        absolute_url = urljoin(source_url, str(link.get("href") or "").strip())
        parsed = urlsplit(absolute_url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        label = normalized_text(link.get_text(" ", strip=True))
        if parsed.scheme != "https" or hostname not in profile.allowed_hosts:
            continue
        if "附件" not in label and "download" not in parsed.path.lower():
            continue
        if absolute_url not in seen:
            attachments.append(absolute_url)
            seen.add(absolute_url)

    return CebDetail(
        title=title,
        published_at=find_date(body_text),
        notice_type=_find_notice_type(body_text),
        publisher=_extract_labeled_value(body_text, "发布媒介"),
        source_channel=_extract_labeled_value(body_text, "来源渠道"),
        body_text=body_text,
        attachment_urls=tuple(attachments),
    )


def _find_notice_type(text: str) -> str | None:
    return next((item for item in _NOTICE_TYPES if item in text), None)


def _extract_labeled_value(text: str, label: str) -> str | None:
    match = re.search(rf"{re.escape(label)}[：:]\s*([^\s]+)", text)
    return match.group(1) if match else None


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in ("h1", "h2", "h3", ".article-title", ".title", ".detail-title"):
        for node in soup.select(selector):
            candidate = normalized_text(node.get_text(" ", strip=True))
            if len(candidate) >= 6 and candidate not in set(_NOTICE_TYPES):
                return candidate
    return ""
