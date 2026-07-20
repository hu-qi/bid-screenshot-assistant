from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BrowserSnapshot:
    url: str
    html: str
    body_text: str
    screenshot: bytes


@dataclass(frozen=True, slots=True)
class GdGpListEntry:
    title: str
    record_id: str
    detail_api_url: str
    portal_url: str
    published_at: datetime | None = None
    notice_type: str | None = None
    purchaser: str | None = None
    project_code: str | None = None
    region: str | None = None
    description: str = ""


@dataclass(frozen=True, slots=True)
class GdGpDetail:
    title: str
    published_at: datetime | None
    notice_type: str | None
    purchaser: str | None
    project_code: str | None
    purchase_manner: str | None
    budget: str | None
    body_text: str
    attachment_urls: tuple[str, ...] = ()
