from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from bid_screenshot_assistant.domain.models import EvidenceArtifact


_SLUG = re.compile(r"[^\w\u4e00-\u9fff.-]+", re.UNICODE)


def safe_slug(value: str, fallback: str = "item") -> str:
    slug = _SLUG.sub("-", value.strip()).strip("-.")
    return (slug or fallback)[:100]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_artifact(
    *,
    item_dir: Path,
    filename: str,
    content: bytes,
    kind: str,
    mime_type: str,
    source_url: str | None,
    simulation: bool,
) -> EvidenceArtifact:
    path = item_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return EvidenceArtifact(
        kind=kind,
        relative_path=str(path),
        mime_type=mime_type,
        sha256=sha256_bytes(content),
        size_bytes=len(content),
        source_url=source_url,
        simulation=simulation,
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def build_zip(run_dir: Path, archive_path: Path) -> Path:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(run_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(run_dir))
    return archive_path
