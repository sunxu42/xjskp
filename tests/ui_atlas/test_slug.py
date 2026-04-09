from src.ui_atlas.slug import stem_to_screen_id


def test_ascii_stem_unchanged_normalized():
    assert stem_to_screen_id("base", task_index=0, task_count=1) == "base"


def test_chinese_stem_pinyin_snake():
    sid = stem_to_screen_id("历练大厅", task_index=0, task_count=1)
    assert sid == "li_lian_da_ting"


def test_multi_task_adds_suffix():
    assert stem_to_screen_id("深渊", task_index=0, task_count=2) == "shen_yuan_1"
    assert stem_to_screen_id("深渊", task_index=1, task_count=2) == "shen_yuan_2"
