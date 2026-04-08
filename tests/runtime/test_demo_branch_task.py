from src.runtime.tasks.demo_branch_task import run_demo_branch_task


def test_demo_branch_task_true_branch():
    logs = run_demo_branch_task({"enemy_detected": True})
    assert logs[-1]["branch"] == "attack_path"


def test_demo_branch_task_false_branch():
    logs = run_demo_branch_task({"enemy_detected": False})
    assert logs[-1]["branch"] == "wait_path"
