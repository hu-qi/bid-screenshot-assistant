import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParseResult:
    names: list[str]
    duplicates: list[str]
    ignored: list[str]


_PREFIX = re.compile(r"^\s*(?:[-*•]|\d+[.、)]|[（(]?[一二三四五六七八九十]+[）)、.]?)\s*")
_SPLIT = re.compile(r"[\n\r;；]+")


def parse_query_names(raw_text: str) -> ParseResult:
    names: list[str] = []
    duplicates: list[str] = []
    ignored: list[str] = []
    seen: set[str] = set()

    for raw in _SPLIT.split(raw_text or ""):
        candidate = _PREFIX.sub("", raw).strip()
        if not candidate:
            if raw.strip():
                ignored.append(raw.strip())
            continue
        if candidate in seen:
            duplicates.append(candidate)
            continue
        seen.add(candidate)
        names.append(candidate)

    return ParseResult(names=names, duplicates=duplicates, ignored=ignored)
