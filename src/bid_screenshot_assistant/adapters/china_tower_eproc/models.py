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
class TowerListEntry:
    title: str
    url: str
    published_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TowerDetail:
    title: str
    published_at: datetime | None
    body_text: str
    attachment_urls: tuple[str, ...]
