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
class UnicomListEntry:
    title: str
    url: str
    published_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class UnicomDetail:
    title: str
    bid_number: str | None
    published_at: datetime
    body_text: str
    attachment_urls: tuple[str, ...]
