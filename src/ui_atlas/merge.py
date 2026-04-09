from __future__ import annotations

import copy
from typing import Any

OVERLAY_KEY_SEP = "::"


def apply_overlay(generated: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(generated)
    elements_overlay = (overlay or {}).get("elements") or {}
    screens = out.get("screens") or {}
    for key, patch in elements_overlay.items():
        if OVERLAY_KEY_SEP not in key:
            continue
        screen_id, source_id = key.split(OVERLAY_KEY_SEP, 1)
        screen = screens.get(screen_id)
        if not screen:
            continue
        for el in screen.get("elements", []):
            if el.get("source_id") == source_id:
                if "description_zh" in patch:
                    el["description_zh"] = patch["description_zh"]
                if "relations" in patch:
                    el["relations"] = copy.deepcopy(patch["relations"])
                break
    return out


def diff_overlay_against_generated(
    generated: dict[str, Any],
    overlay: dict[str, Any],
) -> dict[str, Any]:
    elements_overlay = (overlay or {}).get("elements") or {}
    valid_pairs: set[str] = set()
    for sid, screen in (generated or {}).get("screens", {}).items():
        for el in screen.get("elements", []):
            sid_src = el.get("source_id")
            if sid_src is not None:
                valid_pairs.add(f"{sid}{OVERLAY_KEY_SEP}{sid_src}")
    stale_keys = [k for k in elements_overlay if k not in valid_pairs]
    missing = sorted(valid_pairs - set(elements_overlay.keys()))
    return {"stale_keys": stale_keys, "missing_in_overlay": missing}
