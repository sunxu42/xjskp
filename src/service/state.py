from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List


@dataclass
class RuntimeState:
    running: bool = False
    logs: Deque[str] = field(default_factory=lambda: deque(maxlen=2000))
    tasks: List[Dict[str, str]] = field(
        default_factory=lambda: [
            {"id": "demo_branch_task", "name": "演示任务：识别后条件分支"}
        ]
    )
