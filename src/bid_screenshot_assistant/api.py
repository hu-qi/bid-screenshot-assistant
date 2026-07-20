from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from bid_screenshot_assistant.adapters import DESCRIPTORS, build_simulation_registry
from bid_screenshot_assistant.config import settings
from bid_screenshot_assistant.domain.models import RunSummary, Task, TaskCreate, TaskStatus
from bid_screenshot_assistant.services.orchestrator import TaskRunner
from bid_screenshot_assistant.services.parser import parse_query_names
from bid_screenshot_assistant.services.task_store import InMemoryTaskStore

app = FastAPI(title="Bid Screenshot Assistant", version="0.1.0")
store = InMemoryTaskStore()
runner = TaskRunner(
    registry=build_simulation_registry(),
    artifact_root=Path(settings.artifact_root),
    max_parallel=settings.max_parallel_platforms,
)


class ParseRequest(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return files("bid_screenshot_assistant.web").joinpath("index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "simulation", "platforms": len(DESCRIPTORS)}


@app.get("/api/platforms")
def list_platforms():
    return [descriptor.model_dump(mode="json") for descriptor in DESCRIPTORS]


@app.post("/api/query-names/parse")
def parse_names(request: ParseRequest):
    result = parse_query_names(request.text)
    return {
        "names": result.names,
        "duplicates": result.duplicates,
        "ignored": result.ignored,
    }


@app.post("/api/tasks", response_model=Task)
def create_task(request: TaskCreate) -> Task:
    return store.create(request)


@app.get("/api/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return store.list_tasks()


@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: str) -> Task:
    try:
        return store.get(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@app.post("/api/tasks/{task_id}/run", response_model=RunSummary)
async def run_task(task_id: str) -> RunSummary:
    try:
        task = store.get(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc

    task.status = TaskStatus.RUNNING
    store.save_task(task)
    run = await runner.run(task)
    task.status = run.status
    store.save_task(task)
    store.save_run(run)
    return run


@app.get("/api/runs/{run_id}", response_model=RunSummary)
def get_run(run_id: str) -> RunSummary:
    try:
        return store.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
