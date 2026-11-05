"""The self-test is what stands behind a package, so it has to fail when the app is broken.
The packaged run itself is in packaging/smoke_test.py."""
import json
import os
import subprocess
import sys

import pytest

from conftest import requires_srm
from utils import paths

pytestmark = [
    requires_srm,
    pytest.mark.skipif(sys.platform == "linux" and not os.environ.get("DISPLAY"), reason="The self-test opens the real window"),
]

SCRIPT = """
import sys
from controllers.process import ProcessManager
from utils import paths
from utils.self_test import run
{breakage}
sys.exit(run(sys.argv[1]))
"""


def run_self_test(tmp_path, breakage):
    report_path = tmp_path / "report.json"
    result = subprocess.run([sys.executable, "-c", SCRIPT.format(breakage=breakage), str(report_path)], cwd=paths.app_root(), capture_output=True, timeout=300)
    return result.returncode, json.loads(report_path.read_text(encoding="utf-8"))


def test_it_fails_when_pause_does_not_suspend_srm(tmp_path):
    """Everything before pause has to pass for this to fail where it should."""
    exit_code, report = run_self_test(tmp_path, "ProcessManager.suspend_process = lambda self, process: None")

    assert exit_code == 1
    assert not report["passed"]
    assert "of CPU while paused" in report["failure"]
    assert [step["name"] for step in report["steps"]][-1] == "Processes share a Pareto front"


def test_it_passes_when_one_formula_dominates_the_front(tmp_path):
    """AP on every Process ends with a front of one, which is a valid result."""
    every_process_on_ap = "import models.config; models.config.choose_random_element_with_probability = lambda choices: choices[2 if len(choices) > 1 else 0][0]"
    exit_code, report = run_self_test(tmp_path, every_process_on_ap)

    assert report["failure"] is None
    assert exit_code == 0


def test_it_fails_when_srm_is_missing(tmp_path):
    exit_code, report = run_self_test(tmp_path, "paths.srm_executable = lambda _path: 'missing'")

    assert exit_code == 1
    assert "SRM is not at missing" in report["failure"]
