from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class PlatformId(StrEnum):
    CHINA_MOBILE = "china-mobile"
    CHINA_UNICOM = "china-unicom"
    CHINA_TELECOM = "china-telecom"
    CHINA_TOWER_ONLINE = "china-tower-online"
    CHINA_TOWER_EPROC = "china-tower-eproc"
    CEBPUBSERVICE = "cebpubservice"
    MIIT = "miit"
    GD_GP = "gd-gp"
    GD_GGZY = "gd-ggzy"


class MatchMode(StrEnum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    SMART = "smart"


class PlatformRunStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    PARTIAL = "PARTIAL"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    PAGE_CHANGED = "PAGE_CHANGED"
    TIMEOUT = "TIMEOUT"
    PLATFORM_ERROR = "PLATFORM_ERROR"
    FAILED = "FAILED"


class TaskStatus(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    FAILED = "FAILED"


class AdapterStage(StrEnum):
    EXPERIMENTAL = "experimental"
    PILOT = "pilot"
    ENABLED = "enabled"
    DISABLED = "disabled"


class PlatformDescriptor(BaseModel):
    platform_id: PlatformId
    display_name: str
    adapter_version: str = "0.1.0"
    stage: AdapterStage = AdapterStage.EXPERIMENTAL
    requires_login: bool = False
    supports_date_filter: bool = False
    supports_notice_type_filter: bool = False
    last_verified_at: datetime | None = None


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    query_names: list[str] = Field(min_length=1, max_length=100)
    platform_ids: list[PlatformId] = Field(default_factory=lambda: list(PlatformId))
    recipients: list[str] = Field(default_factory=list)
    match_mode: MatchMode = MatchMode.SMART
    max_hits_per_platform: int = Field(default=5, ge=1, le=50)

    @field_validator("query_names")
    @classmethod
    def normalize_query_names(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            name = item.strip()
            if name and name not in seen:
                cleaned.append(name)
                seen.add(name)
        if not cleaned:
            raise ValueError("At least one non-empty query name is required")
        return cleaned


class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: TaskStatus = TaskStatus.CREATED
    request: TaskCreate


class SearchHit(BaseModel):
    hit_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    source_url: HttpUrl | str
    published_at: datetime | None = None
    notice_type: str | None = None
    match_score: float = Field(default=1.0, ge=0, le=1)
    match_reason: str = ""


class EvidenceArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: uuid4().hex)
    kind: str
    relative_path: str
    mime_type: str
    sha256: str
    size_bytes: int
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_url: str | None = None
    simulation: bool = False


class AdapterRequest(BaseModel):
    task_id: str
    run_id: str
    query_id: str
    query_name: str
    platform_id: PlatformId
    match_mode: MatchMode = MatchMode.SMART
    max_hits: int = 5
    attempt: int = 1
    browser_session_id: str | None = None


class PlatformExecutionResult(BaseModel):
    item_id: str = Field(default_factory=lambda: uuid4().hex)
    query_id: str
    query_name: str
    platform_id: PlatformId
    status: PlatformRunStatus
    hits: list[SearchHit] = Field(default_factory=list)
    artifacts: list[EvidenceArtifact] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    current_step: str
    feedback: str | None = None
    error_code: str | None = None
    retryable: bool = False
    browser_session_id: str | None = None
    attempt: int = 1


class RunSummary(BaseModel):
    run_id: str
    task_id: str
    status: TaskStatus
    started_at: datetime
    finished_at: datetime
    items: list[PlatformExecutionResult]
    archive_path: str
    counts: dict[str, int]
    metadata: dict[str, Any] = Field(default_factory=dict)
