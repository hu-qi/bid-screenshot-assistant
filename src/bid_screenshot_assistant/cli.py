from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from bid_screenshot_assistant.adapters import build_simulation_registry
from bid_screenshot_assistant.config import settings
from bid_screenshot_assistant.domain.models import Task, TaskCreate
from bid_screenshot_assistant.services.orchestrator import TaskRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bid-screenshot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="Run the deterministic nine-platform simulation")
    demo.add_argument("--query", action="append", required=True, help="Project/query name")
    demo.add_argument("--task-name", default="标讯截图模拟任务")
    demo.add_argument("--artifact-root", type=Path, default=settings.artifact_root)
    return parser


async def run_demo(args) -> int:
    task = Task(request=TaskCreate(name=args.task_name, query_names=args.query))
    runner = TaskRunner(
        registry=build_simulation_registry(),
        artifact_root=args.artifact_root,
        max_parallel=settings.max_parallel_platforms,
    )
    result = await runner.run(task)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "demo":
        raise SystemExit(asyncio.run(run_demo(args)))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
