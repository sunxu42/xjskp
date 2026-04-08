# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ["src/launcher/main.py"],
    pathex=[],
    binaries=[],
    datas=[("src/web/index.html", "src/web")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="xjskp", console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name="xjskp")
app = BUNDLE(coll, name="xjskp.app", icon=None, bundle_identifier="com.arthursun.xjskp")
