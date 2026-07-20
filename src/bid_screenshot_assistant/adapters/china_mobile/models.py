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
    response_urls: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MobileListEntry:
    title: str
    url: str
    published_at: datetime | None = None
    notice_type: str | None = None


@dataclass(frozen=True, slots=True)
class MobileDetail:
    title: str
    published_at: datetime | None
    notice_type: str | None
    body_text: str
    attachment_urls: tuple[str, ...] = ()
