"""Check a built package the way a user gets it: python packaging/smoke_test.py dist/ECFpyDesk-....zip

The archive goes to a new folder outside the repo, and the app starts there with its self-test,
as a user with a space and non-ASCII letters in their paths and no Python on the PATH. Before
that, the package is checked for what the build machine has and a user's machine may not.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from settings import MINIMUM_MACOS

TIMEOUT = 660  # seconds, longer than the self-test's own limit, so that it can report first
FOLDER_NAME = "smoke run čž"

# The Visual C++ runtime comes with Python, not with Windows. It is on every build machine, so
# a package that lacks it only fails on a clean computer.
VISUAL_CPP_RUNTIME = re.compile(r"^(msvcp|vcruntime|concrt|vcomp|vccorlib)\d", re.IGNORECASE)
MACOS_SYSTEM_LIBRARIES = ("/usr/lib/", "/System/Library/")
MINIMUM_SYSTEM = re.compile(r"LC_BUILD_VERSION.*?minos (\d+)\.(\d+)|LC_VERSION_MIN_MACOSX.*?version (\d+)\.(\d+)", re.DOTALL)


def extract(archive, folder):
    if sys.platform == "darwin":
        subprocess.run(["ditto", "-x", "-k", str(archive), str(folder)], check=True)
    else:
        with zipfile.ZipFile(archive) as file:
            file.extractall(folder)


def executable_in(folder):
    if sys.platform == "darwin":
        return folder / "ECFpyDesk.app" / "Contents" / "MacOS" / "ECFpyDesk"
    return folder / "ECFpyDesk" / "ECFpyDesk.exe"


def check_bundled_files(folder):
    names = [path.name for path in folder.rglob("*")]
    srm = "SRM.exe" if sys.platform == "win32" else "SRM"
    if srm not in names:
        sys.exit(f"{srm} is not in the package")
    if "mc.txt" in names:
        sys.exit("mc.txt must stay out of the package")


def is_mach_o(path):
    with open(path, "rb") as file:
        return file.read(4) in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe")


def check_macos_package(folder):
    app = folder / "ECFpyDesk.app"
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)

    needed = (0, 0)
    for path in app.rglob("*"):
        if path.is_symlink() or not path.is_file() or not is_mach_o(path):
            continue
        libraries = subprocess.run(["otool", "-L", str(path)], capture_output=True, text=True, check=True).stdout.splitlines()[1:]
        for library in (line.split()[0] for line in libraries):
            if not library.startswith(("@", *MACOS_SYSTEM_LIBRARIES)):
                sys.exit(f"{path.name} links {library}, which is outside the package and the system")
        load_commands = subprocess.run(["otool", "-l", str(path)], capture_output=True, text=True, check=True).stdout
        for version in MINIMUM_SYSTEM.findall(load_commands):
            needed = max(needed, tuple(int(part) for part in version if part))
    print(f"The package needs macOS {needed[0]}.{needed[1]}")
    return needed


def check_windows_package(folder):
    """A library finds what the app has already loaded. An .exe starts on its own, SRM as a
    process of its own, so its runtime must be linked in or sit right beside it."""
    import pefile  # comes with PyInstaller on Windows

    files = [path for path in folder.rglob("*") if path.suffix.lower() in (".exe", ".dll", ".pyd")]
    bundled = {path.name.lower() for path in files}
    missing = set()
    for path in files:
        image = pefile.PE(str(path), fast_load=True)
        image.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
        for entry in getattr(image, "DIRECTORY_ENTRY_IMPORT", []):
            name = entry.dll.decode().lower()
            if not VISUAL_CPP_RUNTIME.match(name):
                continue
            found = (path.parent / name).exists() if path.suffix.lower() == ".exe" else name in bundled
            if not found:
                missing.add(f"{path.name} needs {name}")
        image.close()
    if missing:
        sys.exit("The package lacks the Visual C++ runtime:\n" + "\n".join(sorted(missing)))
    print(f"{len(files)} binaries have the Visual C++ runtime they need")


def user_environment(home):
    """The new home directory leaves no settings or caches from this machine. Temporary files
    go there too, and with them the self-test's own data directory."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith(("PYTHON", "ECFPYDESK", "TCL_", "TK_", "MPL"))}
    temporary = home / "temporary"
    temporary.mkdir()
    environment.update(TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary))
    if sys.platform == "win32":
        system_root = os.environ["SYSTEMROOT"]
        environment["PATH"] = f"{system_root}\\System32;{system_root}"
        environment.update(USERPROFILE=str(home), LOCALAPPDATA=str(home / "AppData" / "Local"), APPDATA=str(home / "AppData" / "Roaming"))
    else:
        environment.update(PATH="/usr/bin:/bin", HOME=str(home))
    return environment


def run_self_test(executable, home, report_path):
    process = subprocess.Popen([str(executable), "--self-test", str(report_path)], cwd=home, env=user_environment(home))
    try:
        return process.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return "killed, it did not end"


def print_report(report):
    print(f"{report['system']}, {report['executable']}")
    for step in report["steps"]:
        print(f"  {step['seconds']:6.1f} s  {step['name']}" + (f": {step['detail']}" if step["detail"] else ""))
    if report["failure"]:
        print(report["failure"])
    for line in report["log"]:
        if not line.startswith(("INFO", "WARNING utils.publisher")):
            print(line)


def main(archive):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
        folder = Path(temporary) / FOLDER_NAME
        home = folder / "home"
        home.mkdir(parents=True)
        report_path = folder / "report.json"

        extract(archive, folder)
        check_bundled_files(folder)
        needed_macos = check_macos_package(folder) if sys.platform == "darwin" else None
        if sys.platform == "win32":
            check_windows_package(folder)

        exit_code = run_self_test(executable_in(folder), home, report_path)
        if not report_path.exists():
            sys.exit(f"The app wrote no report. Exit code: {exit_code}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print_report(report)

        if exit_code != 0 or not report["passed"]:
            sys.exit(f"The self-test failed. Exit code: {exit_code}")
        if not report["frozen"]:
            sys.exit("The self-test did not run in a package")
        if not Path(report["user_data"]).resolve().is_relative_to(home.resolve()):
            sys.exit(f"The app did not use the data directory of the test: {report['user_data']}")
        # Last, so that a local build, which needs the macOS of its Python, still gets the whole run
        declared = tuple(int(part) for part in MINIMUM_MACOS.split("."))
        if needed_macos and needed_macos > declared:
            sys.exit(f"The package needs macOS {needed_macos[0]}.{needed_macos[1]} but declares {MINIMUM_MACOS}")
    print(f"{Path(archive).name} passed")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # the paths have letters a Windows console cannot encode
    main(sys.argv[1])
