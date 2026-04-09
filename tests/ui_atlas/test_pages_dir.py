from pathlib import Path

from src.ui_atlas.extract import build_atlas_from_pages_dir

FIX = Path(__file__).resolve().parent / "fixtures"


def test_build_merges_multiple_files(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    one = (FIX / "one_rect_one_task.json").read_bytes()
    (pages / "alpha.json").write_bytes(one)
    (pages / "beta.json").write_bytes(one)
    atlas = build_atlas_from_pages_dir(pages)
    assert atlas["schemaVersion"] == 1
    assert len(atlas["screens"]) == 2
    assert "generatedAt" in atlas
    assert len(atlas["sources"]) == 2


def test_unique_screen_id_merges_duplicate_keys():
    from src.ui_atlas.extract import _unique_screen_id

    used: dict = {}
    assert _unique_screen_id("same", used) == "same"
    used["same"] = {}
    assert _unique_screen_id("same", used) == "same_2"
    used["same_2"] = {}
    assert _unique_screen_id("same", used) == "same_3"
