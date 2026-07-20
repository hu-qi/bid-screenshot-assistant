---
name: bid-screenshot
version: "0.1.0"
description: Create and execute evidence-first tender notice screenshot tasks across configured procurement platforms, then package and deliver traceable results.
---

# Bid Screenshot Skill

## When to use

Use when the user asks to query one or more project names across configured tender/procurement platforms, capture result/detail evidence, package the results, retry failed platform items, or schedule recurring monitoring.

Do not use to bypass login, captcha, risk-control, paywalls, or access restrictions.

## Inputs

- task name;
- one or more exact project/query names;
- optional recipients;
- optional platform subset and date/notice filters;
- execution mode: immediate or scheduled.

## Workflow

1. Normalize names without changing their legal/business meaning.
2. Preview deduplicated inputs when the input is ambiguous.
3. Create the business task through the bid-screenshot tool/API.
4. Fan out query × platform items with a visible concurrency cap.
5. Require evidence for `FOUND` and `NOT_FOUND`.
6. Preserve login/captcha items for human handoff.
7. Package summary, manifest and evidence.
8. Deliver only after reporting collection status separately from delivery status.

## Output

Return:

- task/run identifiers;
- platform status matrix summary;
- found/not-found/failed/human-action counts;
- archive path or download URL;
- delivery status;
- explicit list of unresolved items.

## Files

- `scripts/workflow.py` — executable SwarmFlow orchestration skeleton.
