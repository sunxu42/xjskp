import json
import logging
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("xjskp")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def log_event(logger: logging.Logger, level: str, **kwargs: str) -> None:
    payload = {"timestamp": datetime.utcnow().isoformat(), "level": level, **kwargs}
    logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(payload, ensure_ascii=False))
