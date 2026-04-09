import json
from pathlib import Path

from src.ui_atlas.extract import extract_screens_from_export_data

FIX = Path(__file__).resolve().parent / "fixtures"


def test_one_task_one_rectangle():
    raw = json.loads((FIX / "one_rect_one_task.json").read_text(encoding="utf-8"))
    screens, meta = extract_screens_from_export_data(raw, source_stem="hub", source_relpath="hub.json")
    assert len(screens) == 1
    sid = next(iter(screens))
    s = screens[sid]
    assert s["name_zh"] == "hub"
    assert len(s["elements"]) == 1
    el = s["elements"][0]
    assert el["source_id"] == "rect-a"
    assert el["kind"] == "rectangle"
    assert el["label_zh"] == "入口"
    assert el["x"] == 10.0 and el["width"] == 30.0
    assert meta["task_count"] == 1


def test_two_tasks_split_screens():
    raw = json.loads((FIX / "two_tasks_mixed.json").read_text(encoding="utf-8"))
    screens, _ = extract_screens_from_export_data(raw, source_stem="深渊", source_relpath="深渊.json")
    assert set(screens.keys()) == {"shen_yuan_1", "shen_yuan_2"}
    pt = [e for e in screens["shen_yuan_1"]["elements"] if e["kind"] == "point"][0]
    assert pt["height"] is None
    assert pt["width"] == 0.64
    assert pt["label_zh"] == "深渊_挑战"
    rect = screens["shen_yuan_2"]["elements"][0]
    assert rect["kind"] == "rectangle"
    assert rect["label_zh"] == "战场争霸"
