import json
from pathlib import Path

from src.ui_atlas.extract import screen_id_from_label_studio_task

FIX = Path(__file__).resolve().parent / "fixtures"


def test_screen_id_stable_across_filename():
    raw = json.loads((FIX / "one_rect_one_task.json").read_text(encoding="utf-8"))
    task = raw[0]
    assert screen_id_from_label_studio_task(task) == "ls_p99_t9001"


def test_screen_id_fallback_hash_when_no_ids():
    task = {"annotations": [{"result": []}]}
    sid = screen_id_from_label_studio_task(task)
    assert sid.startswith("ls_h")
    assert len(sid) == len("ls_h") + 12
