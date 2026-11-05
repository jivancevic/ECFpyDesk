"""Build the package for this system: dist/ECFpyDesk-<version>-<system>.zip

SRM must be built first, see native/README.md. Install requirements-package.txt, then:

    python packaging/build.py 1.0.0
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def system_name():
    if sys.platform == "win32":
        return "windows-x64"
    if sys.platform == "darwin":
        if platform.machine() != "arm64":
            sys.exit(f"The macOS package is for Apple Silicon, this Python runs on {platform.machine()}")
        return "macos-arm64"
    sys.exit("Packages exist for Windows and macOS only")


def build(version):
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--distpath", str(DIST),
            "--workpath", str(ROOT / "build" / "pyinstaller"),
            str(ROOT / "packaging" / "ECFpyDesk.spec"),
        ],
        check=True,
        env={**os.environ, "ECFPYDESK_VERSION": version},
    )


def archive(version, system):
    target = DIST / f"ECFpyDesk-{version}-{system}.zip"
    target.unlink(missing_ok=True)
    if sys.platform == "darwin":
        # ditto keeps the symbolic links of the bundle, and with them its signature
        subprocess.run(["ditto", "-c", "-k", "--keepParent", str(DIST / "ECFpyDesk.app"), str(target)], check=True)
    else:
        shutil.make_archive(str(target.with_suffix("")), "zip", DIST, "ECFpyDesk")
    return target


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "0.0.0"
    system = system_name()
    build(version)
    print(archive(version, system))
