from typing import Any, Dict, List

from src.runtime.tasks.demo_branch_task import run_demo_branch_task


def execute_task(task_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    if task_id == "demo_branch_task":
        return run_demo_branch_task(context)
    raise ValueError(f"Unsupported task_id: {task_id}")
