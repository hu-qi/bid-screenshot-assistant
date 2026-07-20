from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from bid_screenshot_assistant.adapters import (
    build_cebpubservice_registry,
    build_china_mobile_registry,
    build_china_tower_eproc_registry,
    build_china_unicom_registry,
    build_gd_gp_registry,
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

    commands = (
        ("mobile", "China Mobile", "中国移动采购与招标网实验任务"),
        ("tower-eproc", "China Tower", "中国铁塔电子采购平台实验任务"),
        ("unicom", "China Unicom", "中国联通采购与招标网实验任务"),
        ("cebpubservice", "CEB Public Service", "中国招标投标公共服务平台实验任务"),
        ("gd-gp", "Guangdong Government Procurement", "广东政府采购智慧云平台实验任务"),
    )
    for command, label, task_name in commands:
        sub = subparsers.add_parser(
            command,
            help=f"Run the experimental {label} public-announcement adapter",
        )
        _add_experimental_browser_arguments(sub, default_task_name=task_name)
    return parser


def _add_experimental_browser_arguments(parser, *, default_task_name: str) -> None:
    parser.add_argument("--query", action="append", required=True, help="Project/query name")
    parser.add_argument("--task-name", default=default_task_name)
    parser.add_argument("--artifact-root", type=Path, default=settings.artifact_root)
    parser.add_argument("--user-data-dir", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=45_000)
    parser.add_argument("--headed", action="store_true", help="Show the Chromium window")
    parser.add_argument(
        "--acknowledge-experimental",
        action="store_true",
        required=True,
        help="Acknowledge that the live adapter is experimental and public pages may change",
    )


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


async def run_experimental_single_platform(args, platform_id: PlatformId, registry) -> int:
    task = Task(
        request=TaskCreate(
            name=args.task_name,
            query_names=args.query,
            platform_ids=[platform_id],
        )
    )
    runner = TaskRunner(
        registry=registry,
        artifact_root=args.artifact_root,
        max_parallel=1,
        execution_mode="experimental-live",
    )
    result = await runner.run(task)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


def _browser_options(args) -> dict:
    return {
        "headless": not args.headed,
        "timeout_ms": args.timeout_ms,
        "user_data_dir": args.user_data_dir,
    }


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "demo":
        raise SystemExit(asyncio.run(run_demo(args)))

    handlers = {
        "mobile": (PlatformId.CHINA_MOBILE, build_china_mobile_registry),
        "tower-eproc": (PlatformId.CHINA_TOWER_EPROC, build_china_tower_eproc_registry),
        "unicom": (PlatformId.CHINA_UNICOM, build_china_unicom_registry),
        "cebpubservice": (PlatformId.CEBPUBSERVICE, build_cebpubservice_registry),
        "gd-gp": (PlatformId.GD_GP, build_gd_gp_registry),
    }
    if args.command in handlers:
        platform_id, factory = handlers[args.command]
        raise SystemExit(
            asyncio.run(
                run_experimental_single_platform(
                    args,
                    platform_id,
                    factory(**_browser_options(args)),
                )
            )
        )
    raise SystemExit(2)


if __name__ == "__main__":
    main()
