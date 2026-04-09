# xjskp UI Atlas（界面图鉴 JSON）设计说明

**日期**: 2026-04-09  
**状态**: 已实现（代码与命令见 `docs/superpowers/plans/2026-04-09-xjskp-ui-atlas-implementation-plan.md`）

## 1. 目标

- 将 `assets/pages/` 下各 Label Studio 导出 JSON 中的**矩形**与**点**抽取为统一、可更新的**界面图鉴**数据。
- 产出一个（或构建时合并出的）**大 JSON**，供 AI 阅读：快速了解有哪些界面、每个界面有哪些可交互区域、各区域的说明与相互引用。
- 模型强调**数据驱动**：只描述「界面与控件及其关系」，**不**嵌入任务流、状态机或 Label Studio 的 `task` / `annotation` 层级。

## 2. 数据来源与形状（输入）

- 输入文件位于 `assets/pages/*.json`，为 Label Studio 任务列表导出。
- 每条标注结果在 `annotations[].result[]` 中：
  - **矩形**：`type === "rectanglelabels"`，`value` 含 `rectanglelabels`、`x`、`y`、`width`、`height`（百分比）、可选 `rotation`。
  - **点**：`type === "keypointlabels"`，`value` 含 `keypointlabels`、`x`、`y`，以及标注工具产生的小范围 `width`（视为点尺寸，非业务矩形宽高）。

## 3. 多截图 / 多任务（同一源文件）的处理规则

**选定方案：拆分（选项 B）**

- 若单个源 JSON 内存在**多条任务**（多张截图、多个顶层任务对象），在图鉴中**不**合并为单一界面。
- 每条源任务对应图鉴中的**一个独立 `screen`**，与其它界面**平级**。
- 图鉴 JSON **不出现** `task_id`、`inner_id`、`file_upload` 等流程或导出元信息作为结构层级；若需追溯，仅可作为可选调试字段写入某屏的 `meta`（默认不输出给 AI 主路径，见第 8 节）。

**同一文件多屏的命名**

- `name_zh`：以源文件名中的界面名为基底（如 `深渊`），若同文件多屏，在中文名上加可区分后缀（如 `深渊·战场分页`），具体文案在生成后由你确认或通过问答补全。
- 英文 `screen` key：稳定、唯一，建议模式 `{file_stem}_{ordinal}` 或 `{file_stem}_{short_slug}`（实现阶段在计划中细化），保证同一仓库内不冲突。

## 4. 输出 JSON 顶层结构

- 使用 **`schemaVersion`**（整数）与可选 **`generatedAt`**（ISO 时间）、**`sources`**（各源文件校验和或修改时间，便于 diff）便于演进与更新。
- 使用 **`screens`** 对象：键为**全英文**界面 id（`screen_id`），值为该界面的定义。
- **禁止**使用中文作为 JSON 的 key（避免编码、排序与工具链问题）。

### 4.1 每个 screen 的字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name_zh` | 是 | 中文界面名，供 AI 将你的自然语言描述对齐到具体 `screen_id`。 |
| `name_en` | 否 | 产品侧英文界面名；无则省略。 |
| `elements` | 是 | 该界面下所有点与矩形的扁平数组。 |

若某屏仅有英文 key、无法自动得到可靠 `name_zh`，**必须先向你询问**再写入。

### 4.2 每个 element 的字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `source_id` | 是 | 源标注中该条 `result` 的 `id`（如 Label Studio 生成的字符串），用于日后重新导出时合并与对齐。 |
| `kind` | 是 | `"rectangle"` 或 `"point"`。 |
| `label_zh` | 条件 | 来自 `rectanglelabels` / `keypointlabels` 的主标签；若导出仅为英文或内部代号，可留空并由问答补全。 |
| `label_en` | 否 | 可选英文标签。 |
| `x`, `y`, `width`, `height` | 是 | 与导出一致，采用百分比坐标系；`kind === "point"` 时 `width`/`height` 表示标注点尺寸，无业务矩形含义时可与实现约定为保留数值或 `null`（实现计划在脚本中二选一并写死）。 |
| `description_zh` | 否 | 你对该控件「作用」的说明，初始可为空，后续由你或问答填充。 |
| `relations` | 否 | 结构化关系对象，见第 5 节；初始可为 `{}` 或省略。 |

**中文缺失策略**：界面或控件缺少可用的中文名/描述时，AI **应主动询问你**后再写入，避免臆造。

## 5. 关系（relations）——仍是数据，不是流程

`relations` 内使用**固定键名**表达可序列化事实，例如（实现时可选用子集，以计划为准）：

- `opens_screen`: 目标 `screen_id`（字符串）。
- `pairs_with_source_id`: 同一 `screen` 内与之配对的另一控件的 `source_id`。
- 后续可按需要扩展，但**不**引入「步骤列表」或「任务 DAG」作为一等结构。

跨界面引用一律用英文 `screen_id`，不用中文界面名做 key。

## 6. 生成后与 AI 协作方式

1. 从导出 JSON **自动生成**几何与 `label_zh`（若有）、`source_id`、`kind`。
2. 你补充或审核每个控件的 `description_zh`。
3. AI 按**固定模板**提问（例如：邻近配对、命名模式、跨屏跳转），将你的回答写入对应 `relations` 字段。
4. **沟通约定**：多项选择时选项使用 **A / B / C** 标注，不使用其它字母体系。

## 7. 更新策略

- 重新导出 `assets/pages/*.json` 后，用 `source_id` 将已有 `description_zh` 与 `relations` **合并回**新几何；对不上时输出「新增 / 删除 / 待认领」清单供人工处理。
- 若 Label Studio 重新生成导致 `source_id` 变化，需在计划中约定次要匹配键（如 `kind` + `label_zh` + 量化后的 bbox 中心）作为 fallback，冲突时人工裁决。

## 8. 给 AI 的阅读路径

- **主交付物（合并后，含 overlay 语义）**：仓库内 `assets/ui-atlas.json`。
- **可再生几何**（仅导出，不含你写的说明）：`assets/ui-atlas.generated.json`（由 `sync` / `generate` 覆盖写入）。
- **人工维护的说明与关系**：`assets/ui-atlas.overlay.json`，键格式 `"{screen_id}::{source_id}"`。
- **更新命令**（在 `xjskp` 根目录、已安装 `requirements-ui-atlas.txt`）：

```bash
python -m src.ui_atlas.cli sync \
  --pages assets/pages \
  --overlay assets/ui-atlas.overlay.json \
  --out-generated assets/ui-atlas.generated.json \
  --out-merged assets/ui-atlas.json \
  --repo-root .
```

- 可选：从同一数据生成简短 `README` 或索引说明 **schemaVersion** 与字段含义；**不**强制，以免重复维护。

## 9. 非目标（本期明确不做）

- 不在图鉴 JSON 内存储 Label Studio 完整导出或任务工作流。
- 不把「自动化跑关」脚本逻辑写入该文件；脚本可**读取**图鉴作为数据输入。

## 10. 自检记录

- 已消除「甲/乙」表述，多截图策略在正文固定为 **拆分（原选项 B）**。
- 对话中多选项统一为 **A / B / C**（用户偏好，已记入第 6 节）。

---

审阅通过后，下一步：使用 **writing-plans** 编写抽取脚本、合并规则、`screen_id` 命名、以及合并更新的具体实现计划。
