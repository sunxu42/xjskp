---
name: ui-atlas-sync
description: >-
  Regenerates xjskp UI atlas from Label Studio JSON under assets/pages (sync CLI).
  Use when the user wants to refresh ui-atlas.json after changing exports, or says
  /ui-atlas-sync, @ui-atlas-sync, or asks to update the atlas from pages.
---

# UI Atlas Sync（Label Studio → ui-atlas.json）

将 `assets/pages/*.json`（Label Studio 任务数组导出）同步为 `assets/ui-atlas.generated.json` 与合并后的 `assets/ui-atlas.json`（含 `assets/ui-atlas.overlay.json` 中的说明与关系）。

## 原则

- **不依赖导出文件名**：`screen_id` 使用导出内的 `project` + `task.id`（`ls_p{project}_t{id}`），与 xjskp-AI 中 `scripts/transform_label_studio_points.py` 一样，以**标注内容 / 任务载荷**为真源，而非磁盘路径。
- **schemaVersion 2**：顶层**无** `sources` 路径映射。

## 执行步骤（代理须实际运行命令）

1. 工作目录：`xjskp` 仓库根目录（含 `src/ui_atlas`、`assets/pages`）。
2. 执行：

```bash
cd /path/to/xjskp && python -m src.ui_atlas.cli sync \
  --pages assets/pages \
  --overlay assets/ui-atlas.overlay.json \
  --out-generated assets/ui-atlas.generated.json \
  --out-merged assets/ui-atlas.json
```

3. 将命令标准输出中的 JSON（`stale_keys` / `missing_in_overlay`）简要告知用户：`stale_keys` 表示 overlay 里已有键在最新几何中不存在；`missing_in_overlay` 表示尚未在 overlay 中填写说明的控件键。
4. 确认已写入上述三个 JSON 路径（尤其 `assets/ui-atlas.json`）。

## 依赖

- Python 3.11+（与项目一致即可），**无需**额外 `pip` 包；仅标准库 + 仓库内 `src/ui_atlas`。

## 用户如何调用

| 方式 | 说明 |
|------|------|
| **@ui-atlas-sync** | 在 Cursor 对话中 @ 引用本技能，模型应按上文执行 `sync`。 |
| **自然语言** | 例如：「用 ui-atlas 技能把 pages 更新到 atlas」「同步界面图鉴」。 |
| **手动** | 在终端运行上文 `python -m src.ui_atlas.cli sync ...`。 |

## 相关文档

- 设计：`docs/superpowers/specs/2026-04-09-xjskp-ui-atlas-design.md`
- 实现计划：`docs/superpowers/plans/2026-04-09-xjskp-ui-atlas-implementation-plan.md`（部分早期步骤已被 schema v2 替代，以 spec 与代码为准）

## 升级说明（v1 → v2）

若 overlay 曾使用旧版 `screen_id`（如拼音文件名键），v2 的键已变为 `ls_p*_t*`。**需按新 `missing_in_overlay` 列表重新填写** `assets/ui-atlas.overlay.json` 中的 `elements` 键。
