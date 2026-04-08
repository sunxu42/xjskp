from typing import Any, Dict, List


def run_demo_branch_task(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    logs: List[Dict[str, Any]] = []
    logs.append({"step": "capture_window", "result": "ok"})
    logs.append({"step": "detect_target_button", "result": "ok"})

    if context.get("enemy_detected"):
        logs.append(
            {"step": "branch_decision", "branch": "attack_path", "reason": "enemy_detected=true"}
        )
    else:
        logs.append(
            {"step": "branch_decision", "branch": "wait_path", "reason": "enemy_detected=false"}
        )

    return logs
