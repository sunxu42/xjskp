import re

from pypinyin import Style, lazy_pinyin


def stem_to_screen_id(stem: str, task_index: int, task_count: int) -> str:
    stem = stem.strip()
    if re.fullmatch(r"[A-Za-z0-9_\-]+", stem):
        base = stem.lower().replace("-", "_")
    else:
        parts = lazy_pinyin(stem, style=Style.NORMAL)
        base = "_".join(p for p in parts if p).lower()
        base = re.sub(r"_+", "_", base).strip("_") or "screen"
    if task_count <= 1:
        return base
    return f"{base}_{task_index + 1}"
