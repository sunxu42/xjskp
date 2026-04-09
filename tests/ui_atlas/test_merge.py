from src.ui_atlas.merge import apply_overlay, diff_overlay_against_generated


def test_apply_overlay_merges_description():
    generated = {
        "screens": {
            "hub": {
                "name_zh": "hub",
                "elements": [
                    {
                        "source_id": "rect-a",
                        "kind": "rectangle",
                        "label_zh": "入口",
                        "x": 1,
                        "y": 2,
                        "width": 3,
                        "height": 4,
                    }
                ],
            }
        }
    }
    overlay = {
        "version": 1,
        "elements": {"hub::rect-a": {"description_zh": "进入游戏", "relations": {}}},
    }
    out = apply_overlay(generated, overlay)
    el = out["screens"]["hub"]["elements"][0]
    assert el["description_zh"] == "进入游戏"


def test_diff_overlay_stale_and_missing():
    generated = {
        "screens": {
            "a": {"name_zh": "a", "elements": [{"source_id": "e1", "kind": "point", "x": 0, "y": 0, "width": 1, "height": None}]}
        }
    }
    overlay = {"version": 1, "elements": {"gone::e1": {"description_zh": "x"}}}
    d = diff_overlay_against_generated(generated, overlay)
    assert d["stale_keys"] == ["gone::e1"]
    assert d["missing_in_overlay"] == ["a::e1"]
