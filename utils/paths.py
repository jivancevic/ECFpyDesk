"""Where the app finds its files.

Read-only resources (templates, sample data, icons, the SRM binary) resolve from the app's
own location, so the current directory does not matter and a packaged build can bundle them.
Everything the app writes goes to a per-user directory, because a packaged app cannot write
beside itself.
"""
import os
import sys

APP_NAME = "ECFpyDesk"
DATA_DIR_ENV = "ECFPYDESK_DATA_DIR"


def app_root():
    # PyInstaller unpacks bundled files to sys._MEIPASS
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return bundle_root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*parts):
    return os.path.join(app_root(), *parts)


def resolve_resource(path):
    """Absolute paths stay as they are, relative ones are relative to the app."""
    if os.path.isabs(path):
        return path
    return resource_path(*path.split("/"))


def portable_path(path):
    """A path to keep in saved settings. Inside the app it is stored relative, because the
    app's location can change between launches: a packaged app unpacks to a new place each time."""
    root = app_root()
    try:
        inside = os.path.commonpath([os.path.abspath(path), root]) == root
    except ValueError:  # another drive on Windows
        inside = False
    return os.path.relpath(path, root).replace(os.sep, "/") if inside else path


def srm_executable(configured_path="srm/SRM"):
    path = resolve_resource(configured_path)
    if sys.platform == "win32" and not path.lower().endswith(".exe"):
        path += ".exe"
    return path


def user_data_dir():
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        path = override
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
        path = os.path.join(base, APP_NAME)
    elif sys.platform == "darwin":
        path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
        path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def temp_dir():
    """Working directory of the SRM processes: their parameter files, best files and logs."""
    path = os.path.join(user_data_dir(), "temp")
    os.makedirs(path, exist_ok=True)
    return path


def saved_parameters_dir():
    """The user's saved copies of the parameter templates."""
    path = os.path.join(user_data_dir(), "parameters")
    os.makedirs(path, exist_ok=True)
    return path
