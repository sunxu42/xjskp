import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIX = Path(__file__).resolve().parent / "fixtures"


def test_cli_generate_writes_schema(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "any_name.json").write_bytes((FIX / "one_rect_one_task.json").read_bytes())
    out = tmp_path / "out.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "src.ui_atlas.cli",
            "generate",
            "--pages",
            str(pages),
            "--out",
            str(out),
        ],
        cwd=str(REPO),
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 2
    assert "screens" in data
    assert "sources" not in data
    assert "ls_p99_t9001" in data["screens"]
