from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 18765
    log_dir: Path = Path("logs")
    web_dir: Path = Path("src/web")


CONFIG = AppConfig()
