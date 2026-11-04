# PyInstaller build of the app, run through packaging/build.py.
# A folder build, and a .app on macOS: it starts faster than one file and unpacks nothing.
import os
import re
import sys

from PyInstaller.utils.hooks import collect_data_files

ROOT = os.path.dirname(SPECPATH)
VERSION = os.environ.get("ECFPYDESK_VERSION", "0.0.0")

SRM = "SRM.exe" if sys.platform == "win32" else "SRM"
# Named one by one: srm/ can also hold run leftovers and mc.txt, which must not ship
SRM_FILES = ["srm_eval.txt", "srmAP.txt", "srmGEP.txt", "srmGP.txt", "data_1var.txt", "data_2var.txt", "data_2var_log.txt"]
ICONS = ["pause.png", "start.png", "stop.png", "stop_grey.png"]

analysis = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    # As a binary, so that it stays executable and gets signed with the rest on macOS
    binaries=[(os.path.join(ROOT, "srm", SRM), "srm")],
    datas=[
        (os.path.join(ROOT, "config.json"), "."),
        *[(os.path.join(ROOT, "srm", name), "srm") for name in SRM_FILES],
        *[(os.path.join(ROOT, "resources", name), "resources") for name in ICONS],
        *collect_data_files("customtkinter"),
    ],
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    exclude_binaries=True,
    name="ECFpyDesk",
    console=False,
    upx=False,
)

folder = COLLECT(executable, analysis.binaries, analysis.datas, name="ECFpyDesk", upx=False)

if sys.platform == "darwin":
    app = BUNDLE(
        folder,
        name="ECFpyDesk.app",
        bundle_identifier="io.github.jivancevic.ecfpydesk",
        # A bundle version is numbers only, so 1.0.0-rc.1 goes in as 1.0.0
        version=re.match(r"[\d.]*", VERSION).group().rstrip(".") or "0.0.0",
        info_plist={
            "NSHighResolutionCapable": True,
            # What the numpy wheel needs, the highest of all parts. The smoke run prints the real value.
            "LSMinimumSystemVersion": "14.0",
        },
    )
