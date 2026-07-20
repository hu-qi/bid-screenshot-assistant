from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from bid_screenshot_assistant.adapters import (
    build_china_tower_eproc_registry,
    build_simulation_registry,
)
from bid_screenshot_assistant.config import settings
from bid_screenshot_assistant.domain.models import PlatformId, Task, TaskCreate
from bid_screenshot_assistant.services.orchestrator import TaskRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bid-screenshot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run the deterministic nine-platform simulation")
    demo.add_argument("--query", action="append", required=True, help="Project/query name")
    demo.add_argument("--task-name", default="标讯截图模拟任务")
    demo.add_argument("--artifact-root", type=Path, default=settings.artifact_root)

    tower = subparsers.add_parser(
        "tower-eproc",
        help="Run the experimental China Tower public-announcement adapter",
    )
    tower.add_argument("--query", action="append", required=True, help="Project/query name")
    tower.add_argument("--task-name", default="中国铁塔电子采购平台实验任务")
    tower.add_argument("--artifact-root", type=Path, default=settings.artifact_root)
    tower.add_argument("--user-data-dir", type=Path)
    tower.add_argument("--timeout-ms", type=int, default=45_000)
    tower.add_argument("--headed", action="store_true", help="Show the Chromium window")
    tower.add_argument(
        "--acknowledge-experimental",
        action="store_true",
        required=True,
        help="Acknowledge that the live adapter is experimental and public pages may change",
    )
    return parser


async def run_demo(args) -> int:
    task = Task(request=TaskCreate(name=args.task_name, query_names=args.query))
    runner = TaskRunner(
        registry=build_simulation_registry(),
        artifact_root=args.artifact_root,
        max_parallel=settings.max_parallel_platforms,
        execution_mode="simulation",
    )
    result = await runner.run(task)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


async def run_tower_eproc(args) -> int:
    task = Task(
        request=TaskCreate(
            name=args.task_name,
            query_names=args.query,
            platform_ids=[PlatformId.CHINA_TOWER_EPROC],
        )
    )
    runner = TaskRunner(
        registry=build_china_tower_eproc_registry(
            headless=not args.headed,
            timeout_ms=args.timeout_ms,
            user_data_dir=args.user_data_dir,
        ),
        artifact_root=args.artifact_root,
        max_parallel=1,
        execution_mode="experimental-live",
    )
    result = await runner.run(task)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "demo":
        raise SystemExit(asyncio.run(run_demo(args)))
    if args.command == "tower-eproc":
        raise SystemExit(asyncio.run(run_tower_eproc(args)))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
