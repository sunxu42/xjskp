from fastapi import FastAPI

from src.service.routes import build_router
from src.service.state import RuntimeState

state = RuntimeState()
app = FastAPI(title="xjskp local service")
app.include_router(build_router(state))
