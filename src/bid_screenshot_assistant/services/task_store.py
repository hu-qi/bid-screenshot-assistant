from threading import RLock

from bid_screenshot_assistant.domain.models import RunSummary, Task, TaskCreate


class InMemoryTaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._runs: dict[str, RunSummary] = {}
        self._lock = RLock()

    def create(self, request: TaskCreate) -> Task:
        task = Task(request=request)
        with self._lock:
            self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> Task:
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(task_id)
            return self._tasks[task_id]

    def save_task(self, task: Task) -> None:
        with self._lock:
            self._tasks[task.task_id] = task

    def save_run(self, run: RunSummary) -> None:
        with self._lock:
            self._runs[run.run_id] = run

    def get_run(self, run_id: str) -> RunSummary:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            return self._runs[run_id]

    def list_tasks(self) -> list[Task]:
        with self._lock:
            return list(self._tasks.values())
