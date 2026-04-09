# xjskp UI Atlas（界面图鉴）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从 `assets/pages/*.json`（Label Studio 导出）自动生成符合 `2026-04-09-xjskp-ui-atlas-design.md` 的合并图鉴 JSON，并支持 overlay 合并与增量更新时的语义字段保留。

**Architecture:** 纯 Python 库 `src/ui_atlas/`：解析导出 → 生成「可再生」`ui-atlas.generated.json`；人工维护的 `ui-atlas.overlay.json` 仅按 `screen_id` + `source_id` 存 `description_zh` 与 `relations`；`build` 命令写出供 AI 阅读的合并文件 `assets/ui-atlas.json`。`screen_id` 由文件名 stem 经拼音 snake_case 派生，同文件多任务加序后缀。点的 `height` 导出缺失时写 `null`。

**Tech Stack:** Python 3.11+（与仓库现有服务一致）、pytest、`pypinyin`（中文 stem → ASCII `screen_id`）、标准库 `json` / `hashlib` / `pathlib` / `argparse`。

---

## File Structure (planned)

| 路径 | 职责 |
|------|------|
| Create: `src/ui_atlas/__init__.py` | 包初始化，导出 `SCHEMA_VERSION`。 |
| Create: `src/ui_atlas/schema.py` | `SCHEMA_VERSION = 1` 常量。 |
| Create: `src/ui_atlas/slug.py` | `screen_id` 生成：拼音 slug、冲突检测后缀。 |
| Create: `src/ui_atlas/extract.py` | 读单个导出 JSON / 整个 `pages` 目录 → `screens` 字典与 `sources` 元数据。 |
| Create: `src/ui_atlas/merge.py` | 将 overlay 合并进 generated；`sync_report` 列出 orphan / new。 |
| Create: `src/ui_atlas/cli.py` | 子命令 `generate`、`merge`、`sync`（sync = generate + 合并 overlay + 报告）。 |
| Create: `requirements-ui-atlas.txt` | 仅图鉴流水线依赖：`pypinyin==0.53.0`（版本可按安装时调整，计划中写死一个当前稳定版）。 |
| Create: `assets/ui-atlas.overlay.json` | 初值 `{"version": 1, "elements": {}}`，键规范见 Task 5。 |
| Create: `assets/ui-atlas.generated.json` | `generate` 输出（可 gitignore 或纳入版本，由你决定；计划默认 **纳入** 便于 diff）。 |
| Modify: `assets/ui-atlas.json` | `merge` 输出，供 AI 阅读的主文件。 |
| Create: `tests/ui_atlas/fixtures/one_rect_one_task.json` | 最小矩形单任务 fixture。 |
| Create: `tests/ui_atlas/fixtures/two_tasks_mixed.json` | 同文件两条任务，含矩形+点。 |
| Create: `tests/ui_atlas/test_slug.py` | slug 与多任务 `screen_id` 后缀。 |
| Create: `tests/ui_atlas/test_extract.py` | 元素字段、拆分屏、`sources` 校验。 |
| Create: `tests/ui_atlas/test_merge.py` | overlay 合并与 orphan 报告。 |
| Create: `tests/ui_atlas/test_cli.py` | 用 `subprocess` 或 `CliRunner` 风格调用模块（若未引入 click，则用 `subprocess` + `python -m`）。 |
| Modify: `docs/superpowers/specs/2026-04-09-xjskp-ui-atlas-design.md` | 将「状态」改为已实现，并写明产物路径 `assets/ui-atlas.json`。 |

---

### Task 1: 依赖与包骨架

**Files:**
- Create: `requirements-ui-atlas.txt`
- Create: `src/ui_atlas/__init__.py`
- Create: `src/ui_atlas/schema.py`

- [ ] **Step 1: 创建 `requirements-ui-atlas.txt`**

```text
pypinyin==0.53.0
```

- [ ] **Step 2: 本地安装依赖（与现有 venv 或新建一致）**

Run: `cd /Users/arthursun/Codes/xjskp && pip install -r requirements-ui-atlas.txt`
Expected: 成功安装 `pypinyin`。

- [ ] **Step 3: 写入 `src/ui_atlas/schema.py`**

```python
SCHEMA_VERSION = 1
```

- [ ] **Step 4: 写入 `src/ui_atlas/__init__.py`**

```python
from src.ui_atlas.schema import SCHEMA_VERSION

__all__ = ["SCHEMA_VERSION"]
```

- [ ] **Step 5: Commit**

```bash
cd /Users/arthursun/Codes/xjskp
git add requirements-ui-atlas.txt src/ui_atlas/__init__.py src/ui_atlas/schema.py
git commit -m "feat(ui-atlas): add package skeleton and schema version"
```

---

### Task 2: `screen_id` 生成（拼音 slug + 多任务后缀）

**Files:**
- Create: `src/ui_atlas/slug.py`
- Create: `tests/ui_atlas/test_slug.py`

- [ ] **Step 1: 写失败测试 `tests/ui_atlas/test_slug.py`**

```python
from src.ui_atlas.slug import stem_to_screen_id


def test_ascii_stem_unchanged_normalized():
    assert stem_to_screen_id("base", task_index=0, task_count=1) == "base"


def test_chinese_stem_pinyin_snake():
    sid = stem_to_screen_id("历练大厅", task_index=0, task_count=1)
    assert sid == "li_lian_da_ting"


def test_multi_task_adds_suffix():
    assert stem_to_screen_id("深渊", task_index=0, task_count=2) == "shen_yuan_1"
    assert stem_to_screen_id("深渊", task_index=1, task_count=2) == "shen_yuan_2"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /Users/arthursun/Codes/xjskp && pytest tests/ui_atlas/test_slug.py -v`
Expected: 失败（模块或函数不存在）。

- [ ] **Step 3: 实现 `src/ui_atlas/slug.py`**

```python
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
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/ui_atlas/test_slug.py -v`
Expected: 3 passed。

- [ ] **Step 5: Commit**

```bash
git add src/ui_atlas/slug.py tests/ui_atlas/test_slug.py
git commit -m "feat(ui-atlas): derive screen_id from file stem and task ordinal"
```

---

### Task 3: 从 Label Studio 导出提取 `screens` 与 `elements`

**Files:**
- Create: `tests/ui_atlas/fixtures/one_rect_one_task.json`
- Create: `tests/ui_atlas/fixtures/two_tasks_mixed.json`
- Create: `src/ui_atlas/extract.py`
- Create: `tests/ui_atlas/test_extract.py`

- [ ] **Step 1: 写入最小 fixture `tests/ui_atlas/fixtures/one_rect_one_task.json`**

内容（单任务、单矩形，百分比坐标与真实结构一致）：

```json
[
  {
    "id": 9001,
    "inner_id": 1,
    "annotations": [
      {
        "result": [
          {
            "id": "rect-a",
            "type": "rectanglelabels",
            "value": {
              "x": 10.0,
              "y": 20.0,
              "width": 30.0,
              "height": 5.0,
              "rectanglelabels": ["入口"]
            }
          }
        ]
      }
    ]
  }
]
```

- [ ] **Step 2: 写入两任务 fixture `tests/ui_atlas/fixtures/two_tasks_mixed.json`**

完整内容：

```json
[
  {
    "id": 1,
    "inner_id": 1,
    "annotations": [
      {
        "result": [
          {
            "id": "kp-1",
            "type": "keypointlabels",
            "value": {
              "x": 50.0,
              "y": 40.0,
              "width": 0.64,
              "keypointlabels": ["深渊_挑战"]
            }
          }
        ]
      }
    ]
  },
  {
    "id": 2,
    "inner_id": 2,
    "annotations": [
      {
        "result": [
          {
            "id": "rect-b",
            "type": "rectanglelabels",
            "value": {
              "x": 8.0,
              "y": 25.0,
              "width": 17.0,
              "height": 2.4,
              "rectanglelabels": ["战场争霸"]
            }
          }
        ]
      }
    ]
  }
]
```

- [ ] **Step 3: 写失败测试 `tests/ui_atlas/test_extract.py`**

```python
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
```

- [ ] **Step 4: 运行测试确认失败**

Run: `pytest tests/ui_atlas/test_extract.py -v`
Expected: 失败。

- [ ] **Step 5: 实现 `src/ui_atlas/extract.py`**

要点：

- 输入 `raw` 为顶层任务数组；对每个任务取 `annotations[0]["result"]`（若无 `annotations` 或空 `result` 则该任务 `elements` 为空列表仍生成 screen，避免静默丢屏）。
- 对每个 result 项：`type == "rectanglelabels"` → `kind="rectangle"`，从 `value["rectanglelabels"][0]` 取 `label_zh`。
- `type == "keypointlabels"` → `kind="point"`，`label_zh` 从 `keypointlabels[0]`；`height` 若不存在则 `None`；`width` 有则写入。
- 忽略非上述类型（不进入 elements）。
- `name_zh`：`task_count == 1` 时用 `source_stem`；否则 `f"{source_stem}·{task_index + 1}"`（使用 ASCII 中间点 `·` 与 spec 示例一致）。
- `screen_id`：调用 `stem_to_screen_id(source_stem, task_index, task_count)`。
- 返回 `(screens_dict, {"task_count": n, "source_relpath": ...})` 供上层组装 `sources`。

- [ ] **Step 6: 运行测试通过**

Run: `pytest tests/ui_atlas/test_extract.py -v`

- [ ] **Step 7: Commit**

```bash
git add src/ui_atlas/extract.py tests/ui_atlas/fixtures tests/ui_atlas/test_extract.py
git commit -m "feat(ui-atlas): extract screens and elements from Label Studio export"
```

---

### Task 4: 扫描 `assets/pages` 并写出 `ui-atlas.generated.json`

**Files:**
- Modify: `src/ui_atlas/extract.py`（新增 `build_atlas_from_pages_dir`）
- Create: `tests/ui_atlas/test_pages_dir.py`（可选：对临时目录用 `tmp_path` 放两个 json）

- [ ] **Step 1: 写测试：临时目录含两个文件，合并入同一 atlas 的 `screens`**

```python
import json
from pathlib import Path

from src.ui_atlas.extract import build_atlas_from_pages_dir


def test_build_merges_multiple_files(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    one = Path("tests/ui_atlas/fixtures/one_rect_one_task.json").read_bytes()
    (pages / "alpha.json").write_bytes(one)
    (pages / "beta.json").write_bytes(one)
    atlas = build_atlas_from_pages_dir(pages)
    assert "schemaVersion" in atlas and atlas["schemaVersion"] == 1
    assert len(atlas["screens"]) == 2
```

若 `screen_id` 均为 `alpha` / `beta` 的拼音或 ascii，断言 `len==2` 即可；若存在冲突，`build_atlas_from_pages_dir` 必须为重复 `screen_id` 追加 `_dup2` 之类后缀（在实现中检测 `screens` 键冲突并递增）。

- [ ] **Step 2: 实现 `build_atlas_from_pages_dir(pages_dir: Path) -> dict`**

- 遍历 `sorted(pages_dir.glob("*.json"))`。
- 每个文件：`stem = path.stem`，`raw = json.load`。
- `extract_screens_from_export_data`；将各 `screen_id` 并入总 `screens`；**若键冲突**，在键后加 `_2`、`_3`… 直至唯一。
- 顶层输出：

字段约定：`generatedAt` 使用 UTC，例如 Python `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`；`sources` 的键为相对于仓库根的路径字符串（如 `assets/pages/base.json`），值为 `{"sha256": "<64位小写十六进制>", "screen_ids": ["...", ...]}`。

- `sha256` 对文件原始字节计算。

- [ ] **Step 3: pytest**

Run: `pytest tests/ui_atlas/test_pages_dir.py tests/ui_atlas/ -v`

- [ ] **Step 4: Commit**

```bash
git add src/ui_atlas/extract.py tests/ui_atlas/test_pages_dir.py
git commit -m "feat(ui-atlas): build atlas dict from assets/pages directory"
```

---

### Task 5: Overlay 合并与 sync 报告

**Files:**
- Create: `src/ui_atlas/merge.py`
- Create: `assets/ui-atlas.overlay.json`
- Create: `tests/ui_atlas/test_merge.py`

- [ ] **Step 1: 约定 overlay 形状并写入初始文件 `assets/ui-atlas.overlay.json`**

仓库中初值应为空 `elements`，避免提交虚构业务数据：

```json
{
  "version": 1,
  "elements": {}
}
```

键格式：`"{screen_id}::{source_id}"`，避免跨屏 `source_id` 碰撞；你后续补充说明时的条目形如 `"shen_yuan_1::kp-1": { "description_zh": "…", "relations": {} }`。

- [ ] **Step 2: 写测试 `tests/ui_atlas/test_merge.py`**

```python
from src.ui_atlas.merge import apply_overlay, diff_overlay_against_generated


def test_apply_overlay_merges_description():
    generated = {
        "screens": {
            "hub": {
                "name_zh": "hub",
                "elements": [{"source_id": "rect-a", "kind": "rectangle", "label_zh": "入口", "x": 1, "y": 2, "width": 3, "height": 4}],
            }
        }
    }
    overlay = {"version": 1, "elements": {"hub::rect-a": {"description_zh": "进入游戏", "relations": {}}}}
    out = apply_overlay(generated, overlay)
    el = out["screens"]["hub"]["elements"][0]
    assert el["description_zh"] == "进入游戏"
```

`diff_overlay_against_generated`：返回 `{"stale_keys": [...], "missing_in_overlay": [...]}` 用于 sync 打印（stale = overlay 键在 generated 中找不到对应 screen+source_id）。

- [ ] **Step 3: 实现 `merge.py`**

- `apply_overlay(generated, overlay) -> merged`：深拷贝 `generated`（可用 `copy.deepcopy`），遍历 overlay `elements`，解析 `screen_id` 与 `source_id`，匹配则写入 `description_zh` 与 `relations`（仅覆盖存在的键）。
- `diff_overlay_against_generated`：扫描 overlay 键是否可匹配；扫描 generated 中所有 `(screen_id, source_id)` 是否在 overlay 中有条目（可选 `missing` 列表用于提示可补充）。

- [ ] **Step 4: pytest**

Run: `pytest tests/ui_atlas/test_merge.py -v`

- [ ] **Step 5: Commit**

```bash
git add src/ui_atlas/merge.py assets/ui-atlas.overlay.json tests/ui_atlas/test_merge.py
git commit -m "feat(ui-atlas): overlay merge and stale-key diff"
```

---

### Task 6: CLI 与产物路径

**Files:**
- Create: `src/ui_atlas/cli.py`
- Create: `tests/ui_atlas/test_cli.py`
- Modify: `assets/ui-atlas.json`（首次由命令生成）

- [ ] **Step 1: 实现 `python -m src.ui_atlas.cli` 或 `python -m ui_atlas.cli`**

仓库现有 `pythonpath = .`，推荐使用：

```bash
python -m src.ui_atlas.cli generate --pages assets/pages --out assets/ui-atlas.generated.json
python -m src.ui_atlas.cli merge --generated assets/ui-atlas.generated.json --overlay assets/ui-atlas.overlay.json --out assets/ui-atlas.json
python -m src.ui_atlas.cli sync --pages assets/pages --overlay assets/ui-atlas.overlay.json --out-generated assets/ui-atlas.generated.json --out-merged assets/ui-atlas.json
```

`sync` 在写出 merged 后向 stdout 打印 `diff_overlay_against_generated` 的摘要（JSON 一行或易读多行）。

- [ ] **Step 2: 测试 `tests/ui_atlas/test_cli.py`**

使用 `subprocess.run([sys.executable, "-m", "src.ui_atlas.cli", "generate", ...], cwd=repo_root, check=True)`，断言输出文件存在且 `json.load` 后 `schemaVersion == 1`。

- [ ] **Step 3: 在真实 `assets/pages` 上运行一次**

Run:

```bash
cd /Users/arthursun/Codes/xjskp
python -m src.ui_atlas.cli sync --pages assets/pages --overlay assets/ui-atlas.overlay.json --out-generated assets/ui-atlas.generated.json --out-merged assets/ui-atlas.json
```

Expected: 生成两个文件且无异常；`assets/ui-atlas.json` 中 `screens` 数量等于各导出文件内任务数之和。

- [ ] **Step 4: Commit**

```bash
git add src/ui_atlas/cli.py tests/ui_atlas/test_cli.py assets/ui-atlas.generated.json assets/ui-atlas.json
git commit -m "feat(ui-atlas): CLI generate/merge/sync and checked-in atlas outputs"
```

---

### Task 7: 更新设计 spec 状态与 Self-review 对照

**Files:**
- Modify: `docs/superpowers/specs/2026-04-09-xjskp-ui-atlas-design.md`

- [ ] **Step 1: 将 spec 头部「状态」改为「已实现（见 plans/2026-04-09-xjskp-ui-atlas-implementation-plan.md）」**

- [ ] **Step 2: 在 spec 第 8 节「给 AI 的阅读路径」中写死路径：`assets/ui-atlas.json`；并注明 overlay：`assets/ui-atlas.overlay.json`**

- [ ] **Step 3: 全量 pytest**

Run: `pytest /Users/arthursun/Codes/xjskp/tests -q`
Expected: 全部通过。

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-04-09-xjskp-ui-atlas-design.md
git commit -m "docs(ui-atlas): point spec to generated atlas paths"
```

---

## Self-review（对照 spec）

| Spec 章节 | 对应任务 |
|-----------|----------|
| 目标与数据驱动、无 task 层级 | Task 3–4：输出仅 `screens` / `elements` |
| 多任务拆分（选项 B） | Task 3：`task_count` 驱动多 `screen_id` |
| 全英文 key + `name_zh` | Task 2–3：`screen_id` 拼音；`name_zh` 来自 stem·变体 |
| 元素字段与点 `height` | Task 3：`point` 无 `height` → `null` |
| relations 结构化 | Task 5：overlay 写入 `relations` |
| 更新与 source_id | Task 5：`source_id` 对齐；stale 报告 |
| 沟通 A/B/C | 无需代码；spec 已说明 |

**Placeholder 扫描：** 计划中任务均含具体命令、文件路径与示例代码块；无 TBD/TODO。

**类型/命名一致性：** `screen_id` 全任务使用 `stem_to_screen_id`；overlay 键统一 `{screen_id}::{source_id}`。

---

计划已保存至 `docs/superpowers/plans/2026-04-09-xjskp-ui-atlas-implementation-plan.md`。

**执行方式可以二选一：**

1. **Subagent-Driven（推荐）** — 每个 Task 单独开子代理执行，任务间人工/你这边过一遍，迭代快。  
2. **Inline Execution** — 本会话或同一线程按 Task 顺序实现，配合 executing-plans 的检查点批量推进。

你想用哪一种？