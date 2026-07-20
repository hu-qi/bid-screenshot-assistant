from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from xml.sax.saxutils import escape

from bid_screenshot_assistant.adapters.base import PlatformAdapter
from bid_screenshot_assistant.domain.models import (
    AdapterRequest,
    PlatformDescriptor,
    PlatformExecutionResult,
    PlatformRunStatus,
    SearchHit,
)
from bid_screenshot_assistant.services.artifacts import write_artifact


class SimulationPlatformAdapter(PlatformAdapter):
    """Deterministic adapter for validating orchestration without live websites."""

    def __init__(self, descriptor: PlatformDescriptor) -> None:
        self.descriptor = descriptor

    async def execute(
        self,
        request: AdapterRequest,
        item_dir: Path,
    ) -> PlatformExecutionResult:
        started_at = datetime.now(UTC)
        started_perf = perf_counter()
        await asyncio.sleep(0.005)

        if "失败" in request.query_name:
            status = PlatformRunStatus.PLATFORM_ERROR
            hits: list[SearchHit] = []
            feedback = "Simulation requested a platform failure."
            error_code = "SIMULATED_PLATFORM_ERROR"
            retryable = True
        elif "未命中" in request.query_name:
            status = PlatformRunStatus.NOT_FOUND
            hits = []
            feedback = "Simulation completed the search and returned zero results."
            error_code = None
            retryable = False
        else:
            status = PlatformRunStatus.FOUND
            hits = [
                SearchHit(
                    title=f"{request.query_name}（模拟公告）",
                    source_url=f"https://example.invalid/{request.platform_id}/{request.query_id}",
                    match_score=1.0,
                    match_reason="Deterministic simulation exact match",
                )
            ]
            feedback = "Simulation generated one deterministic hit."
            error_code = None
            retryable = False

        item_dir.mkdir(parents=True, exist_ok=True)
        status_text = status.value
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">
  <rect width="1280" height="720" fill="#f5f7fa"/>
  <rect x="72" y="72" width="1136" height="576" rx="18" fill="#ffffff" stroke="#dce2ea"/>
  <text x="112" y="150" font-size="34" font-family="sans-serif" fill="#172033">SIMULATION EVIDENCE</text>
  <text x="112" y="225" font-size="26" font-family="sans-serif" fill="#2457d6">{escape(self.descriptor.display_name)}</text>
  <text x="112" y="300" font-size="22" font-family="sans-serif" fill="#172033">查询名称：{escape(request.query_name)}</text>
  <text x="112" y="365" font-size="22" font-family="sans-serif" fill="#172033">状态：{escape(status_text)}</text>
  <text x="112" y="430" font-size="18" font-family="sans-serif" fill="#5b667a">该文件仅验证工程闭环，不代表真实网站查询结果。</text>
</svg>"""
        artifacts = [
            write_artifact(
                item_dir=item_dir,
                filename="result-page.simulation.svg",
                content=svg.encode("utf-8"),
                kind="result-page",
                mime_type="image/svg+xml",
                source_url=None,
                simulation=True,
            )
        ]

        if hits:
            detail_svg = svg.replace("SIMULATION EVIDENCE", "SIMULATION DETAIL").replace(
                "该文件仅验证工程闭环，不代表真实网站查询结果。",
                escape(hits[0].title),
            )
            artifacts.append(
                write_artifact(
                    item_dir=item_dir,
                    filename="detail-001.simulation.svg",
                    content=detail_svg.encode("utf-8"),
                    kind="detail-page",
                    mime_type="image/svg+xml",
                    source_url=str(hits[0].source_url),
                    simulation=True,
                )
            )

        finished_at = datetime.now(UTC)
        duration_ms = max(1, int((perf_counter() - started_perf) * 1000))
        return PlatformExecutionResult(
            query_id=request.query_id,
            query_name=request.query_name,
            platform_id=request.platform_id,
            status=status,
            hits=hits,
            artifacts=artifacts,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            current_step="simulation_complete",
            feedback=feedback,
            error_code=error_code,
            retryable=retryable,
            attempt=request.attempt,
        )
