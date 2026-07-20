from __future__ import annotations

import asyncio
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from bid_screenshot_assistant.adapters.base import AdapterRegistry
from bid_screenshot_assistant.domain.models import (
    AdapterRequest,
    PlatformExecutionResult,
    PlatformRunStatus,
    RunSummary,
    Task,
    TaskStatus,
)
from bid_screenshot_assistant.services.artifacts import build_zip, safe_slug, write_json


class TaskRunner:
    def __init__(
        self,
        registry: AdapterRegistry,
        artifact_root: Path,
        max_parallel: int = 4,
    ) -> None:
        self.registry = registry
        self.artifact_root = artifact_root
        self.max_parallel = max(1, max_parallel)

    async def run(self, task: Task) -> RunSummary:
        run_id = uuid4().hex
        started_at = datetime.now(UTC)
        run_dir = self.artifact_root / task.task_id / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_one(query_index: int, query_name: str, platform_id):
            async with semaphore:
                query_id = f"q{query_index + 1:03d}"
                item_dir = (
                    run_dir
                    / "queries"
                    / f"{query_id}-{safe_slug(query_name)}"
                    / str(platform_id)
                    / "attempt-001"
                )
                request = AdapterRequest(
                    task_id=task.task_id,
                    run_id=run_id,
                    query_id=query_id,
                    query_name=query_name,
                    platform_id=platform_id,
                    match_mode=task.request.match_mode,
                    max_hits=task.request.max_hits_per_platform,
                )
                adapter = self.registry.get(platform_id)
                try:
                    return await adapter.execute(request, item_dir)
                except Exception as exc:
                    now = datetime.now(UTC)
                    return PlatformExecutionResult(
                        query_id=query_id,
                        query_name=query_name,
                        platform_id=platform_id,
                        status=PlatformRunStatus.FAILED,
                        started_at=now,
                        finished_at=now,
                        duration_ms=0,
                        current_step="adapter_boundary",
                        feedback=str(exc),
                        error_code=type(exc).__name__,
                        retryable=True,
                    )

        coroutines = [
            execute_one(query_index, query_name, platform_id)
            for query_index, query_name in enumerate(task.request.query_names)
            for platform_id in task.request.platform_ids
        ]
        items = list(await asyncio.gather(*coroutines))
        finished_at = datetime.now(UTC)
        counts = Counter(item.status.value for item in items)

        human_states = {
            PlatformRunStatus.LOGIN_REQUIRED,
            PlatformRunStatus.CAPTCHA_REQUIRED,
        }
        technical_failures = {
            PlatformRunStatus.PAGE_CHANGED,
            PlatformRunStatus.TIMEOUT,
            PlatformRunStatus.PLATFORM_ERROR,
            PlatformRunStatus.FAILED,
        }
        if any(item.status in human_states for item in items):
            task_status = TaskStatus.WAITING_FOR_HUMAN
        elif any(item.status in technical_failures for item in items):
            task_status = TaskStatus.COMPLETED_WITH_ERRORS
        else:
            task_status = TaskStatus.COMPLETED

        summary_payload = {
            "task": task.model_dump(mode="json"),
            "run": {
                "run_id": run_id,
                "started_at": started_at,
                "finished_at": finished_at,
                "status": task_status,
                "counts": dict(counts),
            },
            "items": [item.model_dump(mode="json") for item in items],
        }
        write_json(run_dir / "summary.json", summary_payload)

        manifest_entries = []
        for item in items:
            for artifact in item.artifacts:
                artifact_path = Path(artifact.relative_path)
                manifest_entries.append(
                    {
                        "item_id": item.item_id,
                        "query_id": item.query_id,
                        "platform_id": item.platform_id,
                        "kind": artifact.kind,
                        "path": str(artifact_path.relative_to(run_dir)),
                        "sha256": artifact.sha256,
                        "size_bytes": artifact.size_bytes,
                        "simulation": artifact.simulation,
                    }
                )
        write_json(
            run_dir / "manifest.json",
            {
                "schema_version": "1.0",
                "task_id": task.task_id,
                "run_id": run_id,
                "generated_at": finished_at,
                "artifacts": manifest_entries,
            },
        )
        report = _build_html_report(task, run_id, items, counts)
        (run_dir / "report.html").write_text(report, encoding="utf-8")

        archive_path = self.artifact_root / task.task_id / f"{run_id}.zip"
        build_zip(run_dir, archive_path)

        return RunSummary(
            run_id=run_id,
            task_id=task.task_id,
            status=task_status,
            started_at=started_at,
            finished_at=finished_at,
            items=items,
            archive_path=str(archive_path),
            counts=dict(counts),
            metadata={"simulation": True, "platform_count": len(task.request.platform_ids)},
        )


def _build_html_report(task: Task, run_id: str, items, counts) -> str:
    rows = "".join(
        f"<tr><td>{item.query_name}</td><td>{item.platform_id}</td>"
        f"<td>{item.status}</td><td>{item.duration_ms} ms</td>"
        f"<td>{len(item.artifacts)}</td></tr>"
        for item in items
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>标讯截图执行报告</title>
<style>body{{font-family:system-ui,sans-serif;margin:32px;color:#172033}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #dce2ea;padding:10px;text-align:left}}th{{background:#f5f7fa}}</style>
</head><body><h1>{task.request.name}</h1><p>Run ID: {run_id}</p>
<p>本报告由 simulation 模式生成，不代表真实网站查询。</p>
<pre>{dict(counts)}</pre><table><thead><tr><th>查询名称</th><th>平台</th><th>状态</th><th>耗时</th><th>证据数</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""
