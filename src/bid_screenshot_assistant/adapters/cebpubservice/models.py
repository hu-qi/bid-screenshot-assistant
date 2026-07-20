from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BrowserSnapshot:
    url: str
    html: str
    body_text: str
    screenshot: bytes
    search_completed: bool = False
    completion_signal: str = ""


@dataclass(frozen=True, slots=True)
class CebListEntry:
    title: str
    url: str
    published_at: datetime | None = None
    notice_type: str | None = None


@dataclass(frozen=True, slots=True)
class CebDetail:
    title: str
    published_at: datetime | None
    notice_type: str | None
    publisher: str | None
    source_channel: str | None
    body_text: str
    attachment_urls: tuple[str, ...] = ()
