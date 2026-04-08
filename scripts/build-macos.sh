#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m PyInstaller xjskp.spec --noconfirm
mkdir -p artifacts
hdiutil create -volname "xjskp" -srcfolder "dist/xjskp.app" -ov -format UDZO "artifacts/xjskp.dmg"
echo "DMG created at artifacts/xjskp.dmg"
