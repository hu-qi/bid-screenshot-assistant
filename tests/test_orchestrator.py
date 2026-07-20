import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from bid_screenshot_assistant.adapters import build_simulation_registry
from bid_screenshot_assistant.domain.models import Task, TaskCreate, TaskStatus
from bid_screenshot_assistant.services.orchestrator import TaskRunner


@pytest.mark.asyncio
async def test_simulation_run_creates_manifest_and_zip(tmp_path: Path):
    task = Task(request=TaskCreate(name="test", query_names=["项目A", "项目未命中", "项目失败"]))
    runner = TaskRunner(build_simulation_registry(), tmp_path, max_parallel=3)

    result = await runner.run(task)

    assert len(result.items) == 27
    assert result.status == TaskStatus.COMPLETED_WITH_ERRORS
    assert result.counts["FOUND"] == 9
    assert result.counts["NOT_FOUND"] == 9
    assert result.counts["PLATFORM_ERROR"] == 9

    archive_path = Path(result.archive_path)
    assert archive_path.exists()
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert "summary.json" in names
        assert "manifest.json" in names
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == "1.0"
        for artifact in manifest["artifacts"]:
            content = archive.read(artifact["path"])
            assert hashlib.sha256(content).hexdigest() == artifact["sha256"]
