from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

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
        state.running = True
        state.logs.append(f"start: {selected}")
        return {"accepted": True, "task_ids": selected}

    @router.get("/")
    def index() -> FileResponse:
        return FileResponse(Path("src/web/index.html"))

    return router
