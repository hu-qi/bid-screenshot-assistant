from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup

from bid_screenshot_assistant.adapters.profiles import GD_GP_PROFILE, PlatformBrowserProfile

from .models import GdGpDetail, GdGpListEntry


class PageContractError(RuntimeError):
    """The current Guangdong government procurement response is not a valid public contract."""


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


def _json_payload(value: str) -> dict:
    text = (value or "").strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise PageContractError("Official response did not contain a JSON object") from None
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise PageContractError("Official response JSON could not be decoded") from exc
    if not isinstance(payload, dict):
        raise PageContractError("Official response root must be an object")
    if str(payload.get("code")) != "200":
        message = normalized_text(str(payload.get("msg") or "unknown response status"))
        raise PageContractError(f"Official response returned a non-success status: {message}")
    return payload


def has_explicit_no_results(value: str) -> bool:
    payload = _json_payload(value)
    rows = (payload.get("data") or {}).get("rows") or []
    return isinstance(rows, list) and not rows


def parse_search_payload(
    value: str,
    profile: PlatformBrowserProfile = GD_GP_PROFILE,
) -> list[GdGpListEntry]:
    payload = _json_payload(value)
    data = payload.get("data") or {}
    rows = data.get("rows") or []
    if not isinstance(rows, list):
        raise PageContractError("Search response rows must be a list")

    entries: list[GdGpListEntry] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        record_id = normalized_text(str(row.get("id") or ""))
        title = _plain_title(str(row.get("title") or ""))
        if not record_id or not title or record_id in seen:
            continue
        detail_api_url = (
            "https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/getInfoById?"
            + urlencode({"id": record_id})
        )
        portal_url = _portal_route(row)
        if not profile.matches_detail_url(detail_api_url):
            raise PageContractError(f"Generated detail API URL is outside the allowlist: {record_id}")
        if not profile.matches_detail_url(portal_url):
            raise PageContractError(f"Generated portal URL is outside the allowlist: {record_id}")
        entries.append(
            GdGpListEntry(
                title=title,
                record_id=record_id,
                detail_api_url=detail_api_url,
                portal_url=portal_url,
                published_at=parse_datetime(str(row.get("noticeTime") or "")),
                notice_type=normalized_text(
                    str(row.get("noticeTypeName") or row.get("channelName") or "")
                )
                or None,
                purchaser=normalized_text(str(row.get("purchaser") or "")) or None,
                project_code=normalized_text(str(row.get("openTenderCode") or "")) or None,
                region=normalized_text(str(row.get("regionName") or "广东")) or "广东",
                description=_plain_text(str(row.get("description") or "")),
            )
        )
        seen.add(record_id)
    return entries


def parse_detail_payload(
    value: str,
    source_url: str,
    profile: PlatformBrowserProfile = GD_GP_PROFILE,
) -> GdGpDetail:
    if not profile.matches_detail_url(source_url):
        raise PageContractError("Detail API URL is outside the Guangdong government procurement allowlist")
    payload = _json_payload(value)
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        raise PageContractError("Detail response data must be an object")

    title = _plain_title(str(data.get("title") or ""))
    body_text = _plain_text(str(data.get("content") or data.get("noticeContent") or ""))
    if not title:
        raise PageContractError("Detail response title is missing")
    if not body_text:
        raise PageContractError("Detail response content is missing")

    attachments: list[str] = []
    seen: set[str] = set()
    for row in data.get("attchList") or []:
        if not isinstance(row, dict):
            continue
        url = str(row.get("fileUrl") or "").strip()
        if not url:
            continue
        absolute_url = urljoin(source_url, url)
        if not profile.is_allowed_host(absolute_url) or absolute_url in seen:
            continue
        attachments.append(absolute_url)
        seen.add(absolute_url)

    soup = BeautifulSoup(str(data.get("content") or ""), "html.parser")
    for link in soup.find_all("a", href=True):
        absolute_url = urljoin(source_url, str(link.get("href") or "").strip())
        if not profile.is_allowed_host(absolute_url) or absolute_url in seen:
            continue
        label = normalized_text(link.get_text(" ", strip=True)).lower()
        path = absolute_url.lower().split("?", 1)[0]
        if "附件" not in label and not path.endswith(
            (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar")
        ):
            continue
        attachments.append(absolute_url)
        seen.add(absolute_url)

    return GdGpDetail(
        title=title,
        published_at=parse_datetime(str(data.get("noticeTime") or "")),
        notice_type=normalized_text(str(data.get("noticeTypeName") or "")) or None,
        purchaser=normalized_text(str(data.get("purchaser") or "")) or None,
        project_code=normalized_text(str(data.get("openTenderCode") or "")) or None,
        purchase_manner=normalized_text(str(data.get("purchaseMannerName") or "")) or None,
        budget=normalized_text(str(data.get("budget") or "")) or None,
        body_text=body_text,
        attachment_urls=tuple(attachments),
    )


def _plain_title(value: str) -> str:
    return normalized_text(BeautifulSoup(value or "", "html.parser").get_text("", strip=True))


def _plain_text(value: str) -> str:
    return normalized_text(BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True))


def _portal_route(row: dict) -> str:
    base_url = "https://gdgpo.czt.gd.gov.cn"
    notice_id = str(row.get("id") or "")
    channel = str(row.get("channel") or "")
    channel_name = normalized_text(str(row.get("channelName") or ""))
    notice_type = str(row.get("noticeType") or "")
    notice_types = {item.strip() for item in notice_type.split(",") if item.strip()}

    if channel in {
        "fca71be5-fc0c-45db-96af-f513e9abda9d",
        "958b68d2-d97f-4f98-a0f4-3a5802ec94a9",
    }:
        if notice_types.intersection({"59", "001051", "001009", "00105A"}):
            path = "/articleGd"
            params = {"id": notice_id, "channelName": channel_name}
        elif notice_type == "001101":
            path = "/articleRedHeadGd"
            params = {"id": notice_id, "channelName": channel_name}
        else:
            path = "/noticeGd"
            params = {
                "type": "notice",
                "id": notice_id,
                "channel": channel,
                "openTenderCode": row.get("openTenderCode") or "",
                "channelName": channel_name,
            }
    elif channel == "95ff31f3-a1af-4bc4-b1a2-54c894476193":
        path = "/articleRedHeadGd"
        params = {"id": notice_id, "channelName": channel_name}
    elif channel == "82fad126-7447-43a2-94aa-d42647349ae9":
        path = "/noticeKjxyGd"
        params = {
            "id": notice_id,
            "channel": channel,
            "kcProjectCode": row.get("kcProjectCode") or "",
        }
    else:
        path = "/articleGd"
        params = {"type": "article", "id": notice_id, "channelName": channel_name}
    return f"{base_url}{path}?{urlencode(params)}"
