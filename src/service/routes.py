import json
from pathlib import Path
from time import sleep

from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse

from src.runtime.engine import execute_task
from src.service.state import RuntimeState


def build_router(state: RuntimeState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.get("/api/tasks")
    def tasks() -> list[dict]:
        return state.tasks

    @router.post("/api/start")
    def start(payload: dict) -> dict:
        selected = payload.get("task_ids", [])
        context = payload.get("context", {})
        state.running = True
        state.push_log(json.dumps({"event": "start", "task_ids": selected}, ensure_ascii=False))
        for task_id in selected:
            state.push_log(json.dumps({"event": "task_start", "task_id": task_id}, ensure_ascii=False))
            for log_item in execute_task(task_id, context):
                state.push_log(json.dumps({"task_id": task_id, **log_item}, ensure_ascii=False))
            state.push_log(json.dumps({"event": "task_done", "task_id": task_id}, ensure_ascii=False))
        return {"accepted": True, "task_ids": selected}

    @router.get("/api/logs")
    def logs() -> StreamingResponse:
        def event_stream():
            for line in list(state.logs):
                yield f"data: {line}\n\n"
            sleep(0.01)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @router.get("/")
    def index() -> FileResponse:
        return FileResponse(Path("src/web/index.html"))

    return router
