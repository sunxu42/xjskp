from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.ui_atlas.schema import SCHEMA_VERSION
from src.ui_atlas.slug import stem_to_screen_id


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


def extract_screens_from_export_data(
    raw: list[dict[str, Any]] | dict[str, Any],
    source_stem: str,
    source_relpath: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    tasks = raw if isinstance(raw, list) else [raw]
    task_count = len(tasks)
    screens: dict[str, Any] = {}
    for task_index, task in enumerate(tasks):
        screen_id = stem_to_screen_id(source_stem, task_index, task_count)
        if task_count == 1:
            name_zh = source_stem
        else:
            name_zh = f"{source_stem}·{task_index + 1}"
        elements: list[dict[str, Any]] = []
        annotations = task.get("annotations") or []
        results: list[dict[str, Any]] = []
        if annotations:
            results = annotations[0].get("result") or []
        for item in results:
            el = _result_to_element(item)
            if el is not None:
                elements.append(el)
        screens[screen_id] = {"name_zh": name_zh, "elements": elements}
    meta = {"task_count": task_count, "source_relpath": source_relpath}
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


def build_atlas_from_pages_dir(
    pages_dir: Path,
    *,
    source_key: Callable[[Path], str] | None = None,
) -> dict[str, Any]:
    if source_key is None:
        source_key = lambda p: p.name

    all_screens: dict[str, Any] = {}
    sources: dict[str, Any] = {}
    for path in sorted(pages_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        stem = path.stem
        rel = source_key(path)
        part, _meta = extract_screens_from_export_data(raw, stem, rel)
        final_ids: list[str] = []
        for sid, sdata in part.items():
            uid = _unique_screen_id(sid, all_screens)
            all_screens[uid] = sdata
            final_ids.append(uid)
        digest = sha256(path.read_bytes()).hexdigest()
        sources[rel] = {"sha256": digest, "screen_ids": final_ids}

    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": sources,
        "screens": all_screens,
    }


def write_atlas_json(atlas: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(atlas, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
