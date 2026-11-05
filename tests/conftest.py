import os

import pytest

from utils import paths


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    """Every test gets its own per-user directory, with a space in it as on macOS and Windows."""
    directory = tmp_path / "user data"
    monkeypatch.setenv(paths.DATA_DIR_ENV, str(directory))
    return directory


requires_srm = pytest.mark.skipif(not os.path.exists(paths.srm_executable()), reason="SRM is not built")
