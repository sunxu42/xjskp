# xjskp MVP（壳子优先）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先交付可安装、可启动、可观测的 macOS 桌面壳子，再接入 1 个“识别 + 条件判断 + 分支”的真实演示任务，确保项目可中断可恢复推进。

**Architecture:** 采用严格串行：先完成 Desktop Launcher + Local Service + Web UI 的运行闭环，再接入 Task Runtime 与 Automation Adapters。UI 仅通过 HTTP API 与后端通信，日志统一经过结构化日志层并同时输出到 UI 与文件。打包使用 PyInstaller，应用启动自动拉起服务并打开系统浏览器。

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Jinja2/静态 HTML, pytest, PyInstaller, shell scripts (macOS), SSE（日志流）

---

## File Structure (planned)

- Create: `src/shared/config.py`（端口、路径、应用配置）
- Create: `src/shared/logging.py`（结构化日志与文件落盘）
- Create: `src/service/app.py`（FastAPI 应用与路由注册）
- Create: `src/service/routes.py`（任务列表、执行入口、日志流接口）
- Create: `src/service/state.py`（任务状态与内存事件总线）
- Create: `src/web/index.html`（任务勾选、执行按钮、日志面板）
- Create: `src/launcher/main.py`（启动服务、打开浏览器、退出清理）
- Create: `src/runtime/engine.py`（任务执行引擎与分支执行）
- Create: `src/runtime/tasks/demo_branch_task.py`（MVP 演示任务）
- Create: `src/adapters/macos/window_capture.py`（窗口抓取适配）
- Create: `src/adapters/macos/input_actions.py`（输入动作适配）
- Create: `scripts/run-dev.sh`（开发态一键启动）
- Create: `scripts/build-macos.sh`（PyInstaller + dmg 打包）
- Create: `tests/service/test_health_and_tasks.py`
- Create: `tests/service/test_logs_stream.py`
- Create: `tests/runtime/test_demo_branch_task.py`
- Create: `.gitignore`
- Create: `README.md`
- Modify (later): `docs/superpowers/specs/2026-04-08-xjskp-desktop-script-app-design.md`（仅更新进度状态）

---

### Task 1: 初始化工程骨架与开发基线（M0）

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `scripts/run-dev.sh`
- Create: `src/shared/config.py`
- Create: `src/shared/logging.py`

- [ ] **Step 1: 初始化 git 仓库并设置 Python 目录结构**

Run: `cd /Users/arthursun/Codes/xjskp && git init && mkdir -p src/{shared,service,web,launcher,runtime/tasks,adapters/macos} tests/{service,runtime} scripts artifacts`
Expected: 输出 `Initialized empty Git repository`，并创建目标目录。

- [ ] **Step 2: 写入 `.gitignore`**

```gitignore
__pycache__/
.pytest_cache/
.venv/
artifacts/
dist/
build/
*.spec
.DS_Store
.superpowers/
logs/
```

- [ ] **Step 3: 写入 `src/shared/config.py` 最小配置**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 18765
    log_dir: Path = Path("logs")
    web_dir: Path = Path("src/web")


CONFIG = AppConfig()
```

- [ ] **Step 4: 写入 `src/shared/logging.py` 结构化日志基础**

```python
import json
import logging
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("xjskp")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def log_event(logger: logging.Logger, level: str, **kwargs: str) -> None:
    payload = {"timestamp": datetime.utcnow().isoformat(), "level": level, **kwargs}
    logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(payload, ensure_ascii=False))
```

- [ ] **Step 5: 写入 `README.md`（开发启动说明）**

```markdown
# xjskp

## Dev Start

```bash
bash scripts/run-dev.sh
```

## Test

```bash
pytest -q
```
```

- [ ] **Step 6: 写入 `scripts/run-dev.sh` 并赋权**

```bash
#!/usr/bin/env bash
set -euo pipefail

python -m uvicorn src.service.app:app --host 127.0.0.1 --port 18765 --reload
```

Run: `cd /Users/arthursun/Codes/xjskp && chmod +x scripts/run-dev.sh`
Expected: 无报错退出。

- [ ] **Step 7: 提交 M0 基线**

Run:
```bash
cd /Users/arthursun/Codes/xjskp
git add .gitignore README.md scripts/run-dev.sh src/shared/config.py src/shared/logging.py
git commit -m "chore: bootstrap project skeleton and shared config logging"
```
Expected: 生成首个提交。

---

### Task 2: 实现本地服务与最简 UI（M1-1）

**Files:**
- Create: `src/service/state.py`
- Create: `src/service/routes.py`
- Create: `src/service/app.py`
- Create: `src/web/index.html`
- Test: `tests/service/test_health_and_tasks.py`

- [ ] **Step 1: 先写失败测试 `tests/service/test_health_and_tasks.py`**

```python
from fastapi.testclient import TestClient

from src.service.app import app


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_tasks_endpoint():
    client = TestClient(app)
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "demo_branch_task"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /Users/arthursun/Codes/xjskp && pytest tests/service/test_health_and_tasks.py -v`
Expected: FAIL，提示 `src.service.app` 或路由不存在。

- [ ] **Step 3: 写 `src/service/state.py`（任务状态与日志事件）**

```python
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List


@dataclass
class RuntimeState:
    running: bool = False
    logs: Deque[str] = field(default_factory=lambda: deque(maxlen=2000))
    tasks: List[Dict[str, str]] = field(
        default_factory=lambda: [
            {"id": "demo_branch_task", "name": "演示任务：识别后条件分支"}
        ]
    )
```

- [ ] **Step 4: 写 `src/service/routes.py`（health/tasks/start/ui）**

```python
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from src.service.state import RuntimeState


def build_router(state: RuntimeState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.get("/api/tasks")
    def tasks() -> list[dict]:
        return state.tasks

    @router.post("/api/start")
    def start(payload: dict) -> dict:
        selected = payload.get("task_ids", [])
        state.running = True
        state.logs.append(f"start: {selected}")
        return {"accepted": True, "task_ids": selected}

    @router.get("/")
    def index() -> FileResponse:
        return FileResponse(Path("src/web/index.html"))

    return router
```

- [ ] **Step 5: 写 `src/service/app.py`（应用组装）**

```python
from fastapi import FastAPI

from src.service.routes import build_router
from src.service.state import RuntimeState

state = RuntimeState()
app = FastAPI(title="xjskp local service")
app.include_router(build_router(state))
```

- [ ] **Step 6: 写 `src/web/index.html`（任务勾选 + 执行按钮 + 日志区）**

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>xjskp</title>
</head>
<body>
  <h1>xjskp 任务面板</h1>
  <div id="tasks"></div>
  <button id="run">执行</button>
  <pre id="logs"></pre>
  <script>
    async function loadTasks() {
      const data = await fetch('/api/tasks').then(r => r.json());
      const root = document.getElementById('tasks');
      root.innerHTML = data.map(t => `<label><input type="checkbox" value="${t.id}">${t.name}</label><br/>`).join('');
    }
    document.getElementById('run').addEventListener('click', async () => {
      const taskIds = Array.from(document.querySelectorAll('#tasks input:checked')).map(i => i.value);
      const resp = await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task_ids: taskIds})
      }).then(r => r.json());
      document.getElementById('logs').textContent += JSON.stringify(resp) + '\n';
    });
    loadTasks();
  </script>
</body>
</html>
```

- [ ] **Step 7: 重新运行测试确认通过**

Run: `cd /Users/arthursun/Codes/xjskp && pytest tests/service/test_health_and_tasks.py -v`
Expected: PASS（2 passed）。

- [ ] **Step 8: 提交 M1-1**

Run:
```bash
cd /Users/arthursun/Codes/xjskp
git add src/service/state.py src/service/routes.py src/service/app.py src/web/index.html tests/service/test_health_and_tasks.py
git commit -m "feat: add local service and minimal task UI endpoints"
```

---

### Task 3: 实时日志流与启动器（M1-2）

**Files:**
- Modify: `src/service/state.py`
- Modify: `src/service/routes.py`
- Create: `src/launcher/main.py`
- Test: `tests/service/test_logs_stream.py`

- [ ] **Step 1: 先写失败测试 `tests/service/test_logs_stream.py`**

```python
from fastapi.testclient import TestClient

from src.service.app import app


def test_logs_stream_has_sse_format():
    client = TestClient(app)
    resp = client.get("/api/logs", headers={"accept": "text/event-stream"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /Users/arthursun/Codes/xjskp && pytest tests/service/test_logs_stream.py -v`
Expected: FAIL，提示 `/api/logs` 不存在。

- [ ] **Step 3: 修改 `src/service/state.py` 添加日志推送方法**

```python
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List


@dataclass
class RuntimeState:
    running: bool = False
    logs: Deque[str] = field(default_factory=lambda: deque(maxlen=2000))
    tasks: List[Dict[str, str]] = field(
        default_factory=lambda: [
            {"id": "demo_branch_task", "name": "演示任务：识别后条件分支"}
        ]
    )

    def push_log(self, line: str) -> None:
        self.logs.append(line)
```

- [ ] **Step 4: 修改 `src/service/routes.py` 添加 `/api/logs`（SSE）**

```python
import json
from pathlib import Path
from time import sleep

from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse

from src.service.state import RuntimeState


def build_router(state: RuntimeState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.get("/api/tasks")
    def tasks() -> list[dict]:
        return state.tasks

    @router.post("/api/start")
    def start(payload: dict) -> dict:
        selected = payload.get("task_ids", [])
        state.running = True
        state.push_log(json.dumps({"event": "start", "task_ids": selected}, ensure_ascii=False))
        return {"accepted": True, "task_ids": selected}

    @router.get("/api/logs")
    def logs() -> StreamingResponse:
        def event_stream():
            for line in list(state.logs):
                yield f"data: {line}\n\n"
            sleep(0.01)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @router.get("/")
    def index() -> FileResponse:
        return FileResponse(Path("src/web/index.html"))

    return router
```

- [ ] **Step 5: 创建 `src/launcher/main.py`（拉起服务 + 打开浏览器）**

```python
import atexit
import subprocess
import time
import webbrowser


def main() -> None:
    proc = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "src.service.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "18765",
        ]
    )

    def _cleanup() -> None:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)

    atexit.register(_cleanup)
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:18765")
    proc.wait()


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd /Users/arthursun/Codes/xjskp && pytest tests/service/test_logs_stream.py -v`
Expected: PASS（1 passed）。

- [ ] **Step 7: 提交 M1-2**

Run:
```bash
cd /Users/arthursun/Codes/xjskp
git add src/service/state.py src/service/routes.py src/launcher/main.py tests/service/test_logs_stream.py
git commit -m "feat: add sse logs endpoint and desktop launcher entrypoint"
```

---

### Task 4: macOS 打包流程（M1-3）

**Files:**
- Create: `scripts/build-macos.sh`
- Create: `xjskp.spec`
- Modify: `README.md`

- [ ] **Step 1: 写 `xjskp.spec`（PyInstaller 入口）**

```python
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['src/launcher/main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/web/index.html', 'src/web')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='xjskp', console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name='xjskp')
app = BUNDLE(coll, name='xjskp.app', icon=None, bundle_identifier='com.arthursun.xjskp')
```

- [ ] **Step 2: 写 `scripts/build-macos.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m PyInstaller xjskp.spec --noconfirm
mkdir -p artifacts
hdiutil create -volname "xjskp" -srcfolder "dist/xjskp.app" -ov -format UDZO "artifacts/xjskp.dmg"
echo "DMG created at artifacts/xjskp.dmg"
```

- [ ] **Step 3: 赋权并本地构建一次**

Run: `cd /Users/arthursun/Codes/xjskp && chmod +x scripts/build-macos.sh && bash scripts/build-macos.sh`
Expected: 生成 `artifacts/xjskp.dmg`。

- [ ] **Step 4: 更新 `README.md` 加入打包章节**

```markdown
## Build macOS DMG

```bash
bash scripts/build-macos.sh
```
```

- [ ] **Step 5: 提交 M1-3**

Run:
```bash
cd /Users/arthursun/Codes/xjskp
git add xjskp.spec scripts/build-macos.sh README.md
git commit -m "build: add pyinstaller and dmg packaging scripts for macos"
```

---

### Task 5: 接入任务运行时与 1 个分支演示任务（M2）

**Files:**
- Create: `src/runtime/engine.py`
- Create: `src/runtime/tasks/demo_branch_task.py`
- Modify: `src/service/routes.py`
- Test: `tests/runtime/test_demo_branch_task.py`

- [ ] **Step 1: 先写失败测试 `tests/runtime/test_demo_branch_task.py`**

```python
from src.runtime.tasks.demo_branch_task import run_demo_branch_task


def test_demo_branch_task_true_branch():
    logs = run_demo_branch_task({"enemy_detected": True})
    assert logs[-1]["branch"] == "attack_path"


def test_demo_branch_task_false_branch():
    logs = run_demo_branch_task({"enemy_detected": False})
    assert logs[-1]["branch"] == "wait_path"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /Users/arthursun/Codes/xjskp && pytest tests/runtime/test_demo_branch_task.py -v`
Expected: FAIL，提示模块不存在。

- [ ] **Step 3: 写 `src/runtime/tasks/demo_branch_task.py`**

```python
from typing import Any, Dict, List


def run_demo_branch_task(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    logs: List[Dict[str, Any]] = []
    logs.append({"step": "capture_window", "result": "ok"})
    logs.append({"step": "detect_target_button", "result": "ok"})

    if context.get("enemy_detected"):
        logs.append({"step": "branch_decision", "branch": "attack_path", "reason": "enemy_detected=true"})
        logs.append({"step": "click_attack", "result": "ok"})
    else:
        logs.append({"step": "branch_decision", "branch": "wait_path", "reason": "enemy_detected=false"})
        logs.append({"step": "wait_2s", "result": "ok"})

    return logs
```

- [ ] **Step 4: 写 `src/runtime/engine.py`**

```python
from typing import Any, Dict, List

from src.runtime.tasks.demo_branch_task import run_demo_branch_task


def execute_task(task_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    if task_id == "demo_branch_task":
        return run_demo_branch_task(context)
    raise ValueError(f"Unsupported task_id: {task_id}")
```

- [ ] **Step 5: 修改 `src/service/routes.py` 调用运行时并写日志**

```python
import json
from pathlib import Path
from time import sleep

from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse

from src.runtime.engine import execute_task
from src.service.state import RuntimeState


def build_router(state: RuntimeState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.get("/api/tasks")
    def tasks() -> list[dict]:
        return state.tasks

    @router.post("/api/start")
    def start(payload: dict) -> dict:
        selected = payload.get("task_ids", [])
        context = payload.get("context", {})
        for task_id in selected:
            state.push_log(json.dumps({"event": "task_start", "task_id": task_id}, ensure_ascii=False))
            for log_item in execute_task(task_id, context):
                state.push_log(json.dumps({"task_id": task_id, **log_item}, ensure_ascii=False))
            state.push_log(json.dumps({"event": "task_done", "task_id": task_id}, ensure_ascii=False))
        return {"accepted": True, "task_ids": selected}

    @router.get("/api/logs")
    def logs() -> StreamingResponse:
        def event_stream():
            for line in list(state.logs):
                yield f"data: {line}\n\n"
            sleep(0.01)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @router.get("/")
    def index() -> FileResponse:
        return FileResponse(Path("src/web/index.html"))

    return router
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd /Users/arthursun/Codes/xjskp && pytest tests/runtime/test_demo_branch_task.py -v`
Expected: PASS（2 passed）。

- [ ] **Step 7: 执行关键回归测试**

Run: `cd /Users/arthursun/Codes/xjskp && pytest tests/service/test_health_and_tasks.py tests/service/test_logs_stream.py tests/runtime/test_demo_branch_task.py -v`
Expected: 全部 PASS。

- [ ] **Step 8: 提交 M2**

Run:
```bash
cd /Users/arthursun/Codes/xjskp
git add src/runtime/engine.py src/runtime/tasks/demo_branch_task.py src/service/routes.py tests/runtime/test_demo_branch_task.py
git commit -m "feat: add minimal runtime and demo branch task execution"
```

---

### Task 6: 里程碑跟踪与中断恢复机制落地（M3）

**Files:**
- Modify: `docs/superpowers/specs/2026-04-08-xjskp-desktop-script-app-design.md`
- Create: `docs/superpowers/plans/progress-tracker.md`

- [ ] **Step 1: 创建 `docs/superpowers/plans/progress-tracker.md`**

```markdown
# xjskp Progress Tracker

## Current Milestone
M0 (Not Started)

## Done
- none

## Risks/Blockers
- none

## Next
- initialize repository skeleton
```

- [ ] **Step 2: 更新设计文档增加“当前状态”小节**

在 `docs/superpowers/specs/2026-04-08-xjskp-desktop-script-app-design.md` 末尾追加：

```markdown
## 12. 当前实施状态

Current Milestone: M0 (Not Started)
Done:
- none
Risks/Blockers:
- none
Next:
- initialize repository skeleton
```

- [ ] **Step 3: 验证文档完整性**

Run: `cd /Users/arthursun/Codes/xjskp && rg "Current Milestone|Risks/Blockers|Next" docs/superpowers/specs docs/superpowers/plans`
Expected: 在 spec 与 progress-tracker 中都能检索到状态模板字段。

- [ ] **Step 4: 提交 M3**

Run:
```bash
cd /Users/arthursun/Codes/xjskp
git add docs/superpowers/specs/2026-04-08-xjskp-desktop-script-app-design.md docs/superpowers/plans/progress-tracker.md
git commit -m "docs: add milestone tracker and resume workflow anchors"
```

---

## 执行顺序与检查点

1. 先执行 Task 1~4，完成 M1（壳子闭环）。
2. M1 完成后做一次人工验收：安装、启动、自动打开浏览器、日志可见。
3. 再执行 Task 5 完成 M2（真实分支任务）。
4. 最后执行 Task 6 固化 M3（可中断恢复机制）。

每完成一个 Task 都要执行一次对应测试并提交，避免跨任务回滚范围过大。

## Self-Review

### 1) Spec coverage

- “可打包与安装启动” -> Task 4（打包）+ Task 3（启动器）。
- “浏览器最简 UI（任务/勾选/执行/日志）” -> Task 2 + Task 3。
- “1 个识别+条件分支任务” -> Task 5。
- “可中断/可继续（里程碑级）” -> Task 6。
- “macOS MVP 优先” -> Task 4 仅定义 macOS 构建流程。

结论：spec 关键需求均有对应任务。

### 2) Placeholder scan

已检查本计划，不含 `TBD` / `TODO` / “implement later” 等占位语句。

### 3) Type consistency

- `task_id` 主键统一为 `demo_branch_task`。
- 任务执行入口统一为 `execute_task(task_id, context)`。
- 日志事件统一走 `/api/logs` SSE。

结论：命名与接口前后一致。
