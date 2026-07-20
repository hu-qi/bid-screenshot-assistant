"""Executable SwarmFlow skeleton for the bid-screenshot assistant.

Business-side tool calls are represented through agent prompts in this baseline. Replace
those prompts with the registered MCP tools once the production MCP server is enabled.
"""

import json
from string import Template

from swarmflow import agent, compact, log, map_parallel, phase

META = {
    "name": "bid-screenshot",
    "description": "Collect traceable tender notice evidence across configured platforms.",
    "whenToUse": "When project names must be searched, evidenced, packaged and delivered.",
    "phases": [
        {"title": "Normalize task", "detail": "Validate and normalize task input."},
        {"title": "Collect platform evidence", "detail": "Execute bounded platform fan-out."},
        {"title": "Validate and package", "detail": "Check evidence and produce final summary."},
    ],
}

NORMALIZE_SCHEMA = {
    "type": "object",
    "properties": {
        "task_name": {"type": "string"},
        "query_names": {"type": "array", "items": {"type": "string"}},
        "platform_ids": {"type": "array", "items": {"type": "string"}},
        "recipients": {"type": "array", "items": {"type": "string"}},
        "verdict": {"type": "string"},
    },
}

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "query_name": {"type": "string"},
        "platform_id": {"type": "string"},
        "status": {"type": "string"},
        "evidence_count": {"type": "integer"},
        "feedback": {"type": "string"},
    },
}

FINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "summary": {"type": "string"},
        "archive": {"type": "string"},
        "unresolved_items": {"type": "array", "items": {"type": "object"}},
    },
}

NORMALIZE_PROMPT = Template(
    """You normalize a bid screenshot task.
Input: $payload
Return JSON only. Preserve exact project names; remove blank lines and exact duplicates.
Never invent platform success. verdict must be valid or invalid.
"""
)

COLLECT_PROMPT = Template(
    """You execute exactly one platform item through the registered bid-screenshot business tool.
Item: $payload
Return JSON only with query_name, platform_id, status, evidence_count, feedback.
FOUND and NOT_FOUND require evidence. Stop for login, captcha, risk-control or permission gates.
"""
)

FINAL_PROMPT = Template(
    """You validate and summarize one bid screenshot run.
Payload: $payload
Return JSON only. Collection status and delivery status must remain separate.
List every unresolved item. Do not call simulation evidence real website evidence.
"""
)


def parse_args(args):
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            return json.loads(args) if args.strip() else {}
        except json.JSONDecodeError:
            return {}
    return {}


def extract_json(value, fallback=None):
    fallback_value = {} if fallback is None else fallback
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return fallback_value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else fallback_value
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(value[start : end + 1])
                return parsed if isinstance(parsed, dict) else fallback_value
            except json.JSONDecodeError:
                return fallback_value
    return fallback_value


def build_items(task):
    names = task.get("query_names", []) if isinstance(task, dict) else []
    platforms = task.get("platform_ids", []) if isinstance(task, dict) else []
    return [
        {"query_name": name, "platform_id": platform}
        for name in names[:100]
        for platform in platforms[:9]
    ]


async def collect_item(item):
    raw = await agent(
        COLLECT_PROMPT.substitute(payload=json.dumps(item, ensure_ascii=False)),
        label="collect-platform-item",
        phase="Collect platform evidence",
        schema=ITEM_SCHEMA,
    )
    return extract_json(
        raw,
        fallback={
            "query_name": item.get("query_name", ""),
            "platform_id": item.get("platform_id", ""),
            "status": "FAILED",
            "evidence_count": 0,
            "feedback": "tool_or_schema_failure",
        },
    )


async def run(args):
    args = parse_args(args)

    phase("Normalize task")
    log("Normalizing bid screenshot task input")
    normalized_raw = await agent(
        NORMALIZE_PROMPT.substitute(payload=json.dumps(args, ensure_ascii=False)),
        label="normalize-task",
        phase="Normalize task",
        schema=NORMALIZE_SCHEMA,
    )
    normalized = extract_json(normalized_raw, fallback={"verdict": "invalid"})
    if normalized.get("verdict") != "valid":
        return {"status": "invalid", "summary": "Task input is invalid.", "items": []}

    items = build_items(normalized)
    if not items:
        return {"status": "invalid", "summary": "No query/platform items.", "items": []}

    phase("Collect platform evidence")
    log(f"Collecting {len(items)} bounded platform items")
    raw_items = await map_parallel(items, collect_item)
    collected = compact([item for item in raw_items if isinstance(item, dict)])

    phase("Validate and package")
    log("Validating evidence and preparing package summary")
    final_raw = await agent(
        FINAL_PROMPT.substitute(
            payload=json.dumps(
                {"task": normalized, "items": collected}, ensure_ascii=False
            )
        ),
        label="validate-package",
        phase="Validate and package",
        schema=FINAL_SCHEMA,
    )
    final = extract_json(
        final_raw,
        fallback={
            "status": "degraded",
            "summary": "Final validation failed.",
            "archive": "",
            "unresolved_items": collected,
        },
    )
    return {"status": final.get("status", "degraded"), "items": collected, "final": final}
