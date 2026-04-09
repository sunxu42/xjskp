from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.ui_atlas.extract import build_atlas_from_pages_dir, write_atlas_json
from src.ui_atlas.merge import apply_overlay, diff_overlay_against_generated


def _cmd_generate(args: argparse.Namespace) -> int:
    pages = Path(args.pages)
    out = Path(args.out)
    repo = Path(args.repo_root).resolve()

    def source_key(p: Path) -> str:
        return str(p.resolve().relative_to(repo))

    atlas = build_atlas_from_pages_dir(pages, source_key=source_key)
    write_atlas_json(atlas, out)
    return 0


def _cmd_merge(args: argparse.Namespace) -> int:
    gen_path = Path(args.generated)
    overlay_path = Path(args.overlay)
    out_path = Path(args.out)
    generated = json.loads(gen_path.read_text(encoding="utf-8"))
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    merged = apply_overlay(generated, overlay)
    write_atlas_json(merged, out_path)
    return 0


def _cmd_sync(args: argparse.Namespace) -> int:
    pages = Path(args.pages)
    overlay_path = Path(args.overlay)
    out_gen = Path(args.out_generated)
    out_merged = Path(args.out_merged)
    repo = Path(args.repo_root).resolve()

    def source_key(p: Path) -> str:
        return str(p.resolve().relative_to(repo))

    atlas = build_atlas_from_pages_dir(pages, source_key=source_key)
    write_atlas_json(atlas, out_gen)
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    merged = apply_overlay(atlas, overlay)
    write_atlas_json(merged, out_merged)
    report = diff_overlay_against_generated(atlas, overlay)
    print(json.dumps(report, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.ui_atlas.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Export pages JSON to generated atlas")
    p_gen.add_argument("--pages", required=True, help="Directory of Label Studio exports")
    p_gen.add_argument("--out", required=True, help="Output ui-atlas.generated.json path")
    p_gen.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for source keys in sources map (default: cwd)",
    )
    p_gen.set_defaults(func=_cmd_generate)

    p_m = sub.add_parser("merge", help="Merge overlay into generated atlas")
    p_m.add_argument("--generated", required=True)
    p_m.add_argument("--overlay", required=True)
    p_m.add_argument("--out", required=True)
    p_m.set_defaults(func=_cmd_merge)

    p_s = sub.add_parser("sync", help="generate + merge + print diff report")
    p_s.add_argument("--pages", required=True)
    p_s.add_argument("--overlay", required=True)
    p_s.add_argument("--out-generated", required=True)
    p_s.add_argument("--out-merged", required=True)
    p_s.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for source keys (default: cwd)",
    )
    p_s.set_defaults(func=_cmd_sync)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
