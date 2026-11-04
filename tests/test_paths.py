import os
import subprocess
import sys

from utils import paths


def test_resources_resolve_from_the_app_not_the_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert os.path.exists(paths.resource_path("srm", "srmGP.txt"))
    assert os.path.exists(paths.resolve_resource("resources/start.png"))
    assert os.path.exists(paths.resource_path("config.json"))


def test_absolute_paths_stay_as_they_are(tmp_path):
    assert paths.resolve_resource(str(tmp_path)) == str(tmp_path)


def test_a_bundled_app_reads_from_the_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert paths.resource_path("srm", "srmGP.txt") == os.path.join(str(tmp_path), "srm", "srmGP.txt")


def test_srm_name_follows_the_platform(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert paths.srm_executable("srm/SRM").endswith("SRM.exe")

    monkeypatch.setattr(sys, "platform", "darwin")
    assert paths.srm_executable("srm/SRM").endswith("SRM")


def test_writable_files_stay_out_of_the_app_directory(data_dir):
    assert paths.temp_dir() == os.path.join(str(data_dir), "temp")
    assert paths.saved_parameters_dir() == os.path.join(str(data_dir), "parameters")
    assert os.path.isdir(paths.temp_dir())


def test_default_location_per_platform(tmp_path, monkeypatch):
    monkeypatch.delenv(paths.DATA_DIR_ENV)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)

    monkeypatch.setattr(sys, "platform", "darwin")
    assert paths.user_data_dir() == os.path.join(str(tmp_path), "Library", "Application Support", "ECFpyDesk")
    monkeypatch.setattr(sys, "platform", "win32")
    assert paths.user_data_dir() == os.path.join(str(tmp_path), "local", "ECFpyDesk")
    monkeypatch.setattr(sys, "platform", "linux")
    assert paths.user_data_dir() == os.path.join(str(tmp_path), ".local", "share", "ECFpyDesk")


def test_no_tracked_file_points_at_a_home_directory():
    tracked = subprocess.run(["git", "ls-files", "srm", "config.json"], cwd=paths.app_root(), capture_output=True, text=True).stdout.split()
    for name in tracked:
        with open(paths.resource_path(*name.split("/")), "rb") as file:
            content = file.read()
        assert b"/Users/" not in content or name.endswith("SRM"), name
