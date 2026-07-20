from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from bid_screenshot_assistant.adapters.base import PlatformAdapter
from bid_screenshot_assistant.adapters.profiles import CEBPUBSERVICE_PROFILE
from bid_screenshot_assistant.domain.models import (
    AdapterRequest,
    PlatformDescriptor,
    PlatformExecutionResult,
    PlatformRunStatus,
    SearchHit,
)
from bid_screenshot_assistant.services.artifacts import write_artifact

from .driver import CebDriverFactory, PlaywrightCebDriver
from .parser import (
    CaptchaRequiredError,
    PageContractError,
    has_captcha,
    has_explicit_no_results,
    is_error_page,
    match_score,
    parse_detail_page,
    parse_list_page,
)


class CebpubserviceAdapter(PlatformAdapter):
    """Experimental public announcement adapter for CEB Public Service."""

    def __init__(
        self,
        descriptor: PlatformDescriptor,
        *,
        driver_factory: CebDriverFactory | None = None,
        headless: bool = True,
        timeout_ms: int = 45_000,
        user_data_dir: Path | None = None,
    ) -> None:
        self.descriptor = descriptor
        self.profile = CEBPUBSERVICE_PROFILE
        self.driver_factory = driver_factory or (
            lambda: PlaywrightCebDriver(
                self.profile,
                headless=headless,
                timeout_ms=timeout_ms,
                user_data_dir=user_data_dir,
            )
        )

    async def execute(self, request: AdapterRequest, item_dir: Path) -> PlatformExecutionResult:
        started_at = datetime.now(UTC)
        started_perf = perf_counter()
        artifacts = []
        hits: list[SearchHit] = []
        detail_errors: list[dict[str, str]] = []
        current_step = "start"

        try:
            async with self.driver_factory() as driver:
                current_step = "search"
                search_snapshot = await driver.search(request.query_name)
                artifacts.append(
                    write_artifact(
                        item_dir=item_dir,
                        filename="result-page.png",
                        content=search_snapshot.screenshot,
                        kind="result-page",
                        mime_type="image/png",
                        source_url=search_snapshot.url,
                        simulation=False,
                    )
                )
                artifacts.append(
                    self._write_json(
                        item_dir,
                        "search-signals.json",
                        {
                            "query_name": request.query_name,
                            "search_completed": search_snapshot.search_completed,
                            "completion_signal": search_snapshot.completion_signal,
                            "source_url": search_snapshot.url,
                        },
                        "execution-diagnostics",
                        search_snapshot.url,
                    )
                )

                raw = search_snapshot.html or search_snapshot.body_text
                if has_captcha(raw):
                    raise CaptchaRequiredError("Captcha is blocking the search result")
                if is_error_page(raw):
                    raise RuntimeError("CEB portal returned an explicit error state")

                ranked = []
                for entry in parse_list_page(search_snapshot.html, self.profile):
                    score, reason = match_score(request.query_name, entry.title)
                    if score >= 0.55:
                        ranked.append((score, reason, entry))
                ranked.sort(key=lambda item: item[0], reverse=True)
                selected = ranked[: request.max_hits]

                if not selected:
                    if not search_snapshot.search_completed:
                        raise PageContractError("CEB search completion could not be verified")
                    if has_explicit_no_results(raw):
                        return self._result(
                            request, started_at, started_perf, PlatformRunStatus.NOT_FOUND,
                            "search_complete", artifacts, [],
                            "Search completed with an explicit no-result state.", False,
                        )
                    raise PageContractError(
                        "Search completed without matched detail links or a no-result marker"
                    )

                for index, (score, reason, entry) in enumerate(selected, start=1):
                    current_step = f"detail_{index:03d}"
                    try:
                        snapshot = await driver.fetch_detail(entry.url)
                        detail = parse_detail_page(snapshot.html, entry.url, self.profile)
                        artifacts.extend(self._write_detail(item_dir, index, snapshot, detail))
                        hits.append(
                            SearchHit(
                                title=detail.title,
                                source_url=entry.url,
                                published_at=detail.published_at or entry.published_at,
                                notice_type=detail.notice_type or entry.notice_type or "公告公示",
                                match_score=score,
                                match_reason=reason,
                            )
                        )
                    except CaptchaRequiredError:
                        raise
                    except Exception as exc:
                        detail_errors.append(
                            {"url": entry.url, "error_code": type(exc).__name__, "message": str(exc)}
                        )
                        hits.append(
                            SearchHit(
                                title=entry.title,
                                source_url=entry.url,
                                published_at=entry.published_at,
                                notice_type=entry.notice_type or "公告公示",
                                match_score=score,
                                match_reason=f"{reason}; detail capture failed",
                            )
                        )

                if detail_errors:
                    artifacts.append(
                        self._write_json(
                            item_dir,
                            "detail-errors.json",
                            detail_errors,
                            "execution-diagnostics",
                            search_snapshot.url,
                        )
                    )
                    return self._result(
                        request, started_at, started_perf, PlatformRunStatus.PARTIAL,
                        "detail_complete_with_errors", artifacts, hits,
                        f"Collected {len(hits)} list hits; {len(detail_errors)} details failed.",
                        True, "DETAIL_CAPTURE_FAILED",
                    )

                return self._result(
                    request, started_at, started_perf, PlatformRunStatus.FOUND,
                    "complete", artifacts, hits,
                    f"Collected {len(hits)} verified public detail pages.", False,
                )
        except CaptchaRequiredError as exc:
            return self._result(
                request, started_at, started_perf, PlatformRunStatus.CAPTCHA_REQUIRED,
                current_step, artifacts, hits, str(exc), False, "CAPTCHA_REQUIRED",
            )
        except PageContractError as exc:
            return self._result(
                request, started_at, started_perf, PlatformRunStatus.PAGE_CHANGED,
                current_step, artifacts, hits, str(exc), False, "PAGE_CONTRACT_MISMATCH",
            )
        except Exception as exc:
            timeout = type(exc).__name__ == "TimeoutError"
            return self._result(
                request,
                started_at,
                started_perf,
                PlatformRunStatus.TIMEOUT if timeout else PlatformRunStatus.PLATFORM_ERROR,
                current_step,
                artifacts,
                hits,
                str(exc),
                True,
                type(exc).__name__,
            )

    def _write_detail(self, item_dir, index, snapshot, detail):
        screenshot = write_artifact(
            item_dir=item_dir,
            filename=f"detail-{index:03d}.png",
            content=snapshot.screenshot,
            kind="detail-page",
            mime_type="image/png",
            source_url=snapshot.url,
            simulation=False,
        )
        metadata = self._write_json(
            item_dir,
            f"detail-{index:03d}.json",
            {
                "title": detail.title,
                "notice_type": detail.notice_type,
                "published_at": detail.published_at,
                "publisher": detail.publisher,
                "source_channel": detail.source_channel,
                "source_url": snapshot.url,
                "attachment_urls": detail.attachment_urls,
                "body_excerpt": detail.body_text[:1000],
            },
            "detail-metadata",
            snapshot.url,
        )
        return [screenshot, metadata]

    @staticmethod
    def _write_json(item_dir, filename, payload, kind, source_url):
        content = (json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n").encode()
        return write_artifact(
            item_dir=item_dir,
            filename=filename,
            content=content,
            kind=kind,
            mime_type="application/json",
            source_url=source_url,
            simulation=False,
        )

    @staticmethod
    def _result(
        request,
        started_at,
        started_perf,
        status,
        current_step,
        artifacts,
        hits,
        feedback,
        retryable,
        error_code=None,
    ):
        finished_at = datetime.now(UTC)
        return PlatformExecutionResult(
            query_id=request.query_id,
            query_name=request.query_name,
            platform_id=request.platform_id,
            status=status,
            hits=hits,
            artifacts=artifacts,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=max(1, int((perf_counter() - started_perf) * 1000)),
            current_step=current_step,
            feedback=feedback,
            error_code=error_code,
            retryable=retryable,
            browser_session_id=request.browser_session_id,
            attempt=request.attempt,
        )
