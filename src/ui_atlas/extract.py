from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.ui_atlas.schema import SCHEMA_VERSION


def _result_to_element(item: dict[str, Any]) -> dict[str, Any] | None:
    t = item.get("type")
    vid = item.get("id", "")
    value = item.get("value") or {}
    if t == "rectanglelabels":
        labels = value.get("rectanglelabels") or []
        label_zh = labels[0] if labels else ""
        return {
            "source_id": vid,
            "kind": "rectangle",
            "label_zh": label_zh,
            "x": float(value["x"]),
            "y": float(value["y"]),
            "width": float(value["width"]),
            "height": float(value["height"]),
        }
    if t == "keypointlabels":
        labels = value.get("keypointlabels") or []
        label_zh = labels[0] if labels else ""
        w = value.get("width")
        h = value.get("height")
        return {
            "source_id": vid,
            "kind": "point",
            "label_zh": label_zh,
            "x": float(value["x"]),
            "y": float(value["y"]),
            "width": float(w) if w is not None else None,
            "height": float(h) if h is not None else None,
        }
    return None


def _annotation_results(task: dict[str, Any]) -> list[dict[str, Any]]:
    annotations = task.get("annotations") or []
    if not annotations:
        return []
    return annotations[0].get("result") or []


def _first_label_from_results(results: list[dict[str, Any]]) -> str:
    for item in results:
        t = item.get("type")
        val = item.get("value") or {}
        if t == "rectanglelabels":
            labels = val.get("rectanglelabels") or []
            if labels:
                return str(labels[0])
        if t == "keypointlabels":
            labels = val.get("keypointlabels") or []
            if labels:
                return str(labels[0])
    return ""


def _project_id_for_task(task: dict[str, Any]) -> Any | None:
    proj = task.get("project")
    if proj is not None:
        return proj
    annotations = task.get("annotations") or []
    if annotations:
        ann_proj = annotations[0].get("project")
        if ann_proj is not None:
            return ann_proj
    return None


def screen_id_from_label_studio_task(task: dict[str, Any]) -> str:
    """
    Stable English id from Label Studio export only (no host filename).
    Matches xjskp-AI style: identity comes from export payload, not disk path.
    """
    tid = task.get("id")
    proj = _project_id_for_task(task)
    if tid is not None and proj is not None:
        return f"ls_p{proj}_t{tid}"
    raw = json.dumps(task, sort_keys=True, ensure_ascii=False)
    h = sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"ls_h{h}"


def name_zh_from_task(task: dict[str, Any], task_index: int, task_count: int) -> str:
    results = _annotation_results(task)
    label = _first_label_from_results(results)
    tid = task.get("id", task_index)
    if not label:
        return f"待命名·{tid}"
    if task_count <= 1:
        return label
    return f"{label}·{task_index + 1}"


def extract_screens_from_export_data(
    raw: list[dict[str, Any]] | dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    tasks = raw if isinstance(raw, list) else [raw]
    task_count = len(tasks)
    screens: dict[str, Any] = {}
    for task_index, task in enumerate(tasks):
        screen_id = screen_id_from_label_studio_task(task)
        name_zh = name_zh_from_task(task, task_index, task_count)
        elements: list[dict[str, Any]] = []
        for item in _annotation_results(task):
            el = _result_to_element(item)
            if el is not None:
                elements.append(el)
        screen: dict[str, Any] = {"name_zh": name_zh, "elements": elements}
        tid = task.get("id")
        proj = _project_id_for_task(task)
        if tid is not None and proj is not None:
            screen["meta"] = {"ls_project": proj, "ls_task": tid}
        screens[screen_id] = screen
    meta = {"task_count": task_count}
    return screens, meta


def _unique_screen_id(preferred: str, used: dict[str, Any]) -> str:
    if preferred not in used:
        return preferred
    i = 2
    while True:
        cand = f"{preferred}_{i}"
        if cand not in used:
            return cand
        i += 1


def build_atlas_from_pages_dir(pages_dir: Path) -> dict[str, Any]:
    """
    Scan *.json under pages_dir. Screen identity and names come only from
    Label Studio task payloads (project + task id, annotation labels), not filenames.
    """
    all_screens: dict[str, Any] = {}
    for path in sorted(pages_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        part, _meta = extract_screens_from_export_data(raw)
        for sid, sdata in part.items():
            uid = _unique_screen_id(sid, all_screens)
            all_screens[uid] = sdata

    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "screens": all_screens,
    }


def write_atlas_json(atlas: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(atlas, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
