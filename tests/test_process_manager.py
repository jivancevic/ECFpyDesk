"""Every transition of a run, against a stand-in for SRM: a Python script that counts."""
import os
import sys
import textwrap
import threading
import time

import pytest

from controllers.process import IDLE, PAUSED, RUNNING, ProcessManager

COUNTER = """
import os, sys, time
folder = os.path.dirname(os.path.abspath(sys.argv[0]))
with open(os.path.join(folder, 'runs'), 'a') as file:
    file.write('run\\n')
count = 0
while count < {limit}:
    count += 1
    with open(os.path.join(folder, 'count.tmp'), 'w') as file:
        file.write(str(count))
    try:
        os.replace(os.path.join(folder, 'count.tmp'), os.path.join(folder, 'count'))
    except PermissionError:
        pass  # Windows, while the test is reading the file
    time.sleep(0.01)
"""


# On Windows a venv's python.exe is a launcher, and pausing it would not pause the real interpreter
PYTHON = getattr(sys, "_base_executable", sys.executable)


def wait_until(condition, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return False


class Run:
    def __init__(self, folder, limit=10**9, script=None):
        self.folder = folder
        folder.mkdir(exist_ok=True)
        self.script = folder / "fake_srm.py"
        self.script.write_text(textwrap.dedent(script or COUNTER.format(limit=limit)))
        self.manager = ProcessManager(PYTHON, str(folder))
        self.manager.set_parameters_paths([str(self.script)])

    def count(self):
        try:
            return int((self.folder / "count").read_text() or 0)
        except (FileNotFoundError, PermissionError, ValueError):
            return 0

    def runs(self):
        try:
            return len((self.folder / "runs").read_text().splitlines())
        except FileNotFoundError:
            return 0

    def evaluate(self):
        individual = self.folder / "individual.txt"
        individual.write_text("")
        return self.manager.run_test_process(0, str(self.script), str(individual), str(self.folder / "output.txt"))

    def is_counting(self):
        before = self.count()
        return wait_until(lambda: self.count() > before, timeout=3)


@pytest.fixture
def run(tmp_path):
    run = Run(tmp_path / "process")
    yield run
    run.manager.stop_all_processes()


def test_start_runs_a_process(run):
    run.manager.start_all_processes()

    assert run.manager.state == RUNNING
    assert run.is_counting()


def test_pause_suspends_and_continue_resumes_the_same_process(run):
    run.manager.start_all_processes()
    assert run.is_counting()

    run.manager.pause_all_processes()
    assert run.manager.state == PAUSED
    time.sleep(0.1)
    paused_at = run.count()
    time.sleep(0.5)
    assert run.count() == paused_at

    run.manager.continue_all_processes()
    assert run.manager.state == RUNNING
    assert run.is_counting()
    assert run.count() > paused_at
    assert run.runs() == 1


def test_pause_does_not_end_the_process_loop(run):
    run.manager.start_all_processes()
    assert run.is_counting()

    run.manager.pause_all_processes()
    time.sleep(0.3)

    assert run.manager.active_process_count() == 1


def test_repeated_pause_and_continue(run):
    run.manager.start_all_processes()
    for _ in range(3):
        assert run.is_counting()
        run.manager.pause_all_processes()
        run.manager.pause_all_processes()
        run.manager.continue_all_processes()
        run.manager.continue_all_processes()
    assert run.is_counting()


def test_stop_ends_a_running_process(run):
    run.manager.start_all_processes()
    assert run.is_counting()

    run.manager.stop_all_processes()

    assert run.manager.state == IDLE
    assert run.manager.active_process_count() == 0
    assert run.manager.processes == {}
    assert not run.is_counting()


def test_stop_ends_a_paused_process_at_once(run):
    run.manager.start_all_processes()
    assert run.is_counting()
    run.manager.pause_all_processes()

    started = time.monotonic()
    run.manager.stop_all_processes()

    assert time.monotonic() - started < 2
    assert run.manager.active_process_count() == 0


def test_stop_when_idle_does_nothing(run):
    run.manager.stop_all_processes()

    assert run.manager.state == IDLE


def test_pause_and_continue_when_idle_do_nothing(run):
    run.manager.pause_all_processes()
    assert run.manager.state == IDLE

    run.manager.continue_all_processes()
    assert run.manager.state == IDLE


def test_start_again_after_stop(run):
    run.manager.start_all_processes()
    assert run.is_counting()
    run.manager.stop_all_processes()

    run.manager.start_all_processes()

    assert run.is_counting()
    assert run.runs() == 2


def test_a_second_start_is_ignored(run):
    run.manager.start_all_processes()
    assert run.is_counting()

    run.manager.start_all_processes()
    time.sleep(0.2)

    assert run.runs() == 1


def test_a_finished_process_starts_again(tmp_path):
    run = Run(tmp_path / "process", limit=3)
    run.manager.start_all_processes()

    assert wait_until(lambda: run.runs() >= 3)

    run.manager.stop_all_processes()


def test_continue_after_the_process_ended_during_the_pause(tmp_path):
    """The process is gone when continue arrives: the run must start SRM again, not crash."""
    run = Run(tmp_path / "process", limit=30)
    run.manager.start_all_processes()
    assert wait_until(lambda: run.count() > 0)
    run.manager.pause_all_processes()

    process = next(iter(run.manager.processes.values()))
    process.kill()
    assert wait_until(lambda: not run.manager.processes)
    time.sleep(0.2)
    runs_during_pause = run.runs()
    assert runs_during_pause == 1

    run.manager.continue_all_processes()

    assert wait_until(lambda: run.runs() > runs_during_pause)
    run.manager.stop_all_processes()


def test_a_process_that_starts_during_a_pause_waits_for_continue(tmp_path):
    run = Run(tmp_path / "process", limit=10**9)
    entered = threading.Event()
    release = threading.Event()

    def hold(_id):
        entered.set()
        release.wait()

    run.manager.register_callback('pre_process_start', hold)
    run.manager.start_all_processes()
    assert entered.wait(5)
    run.manager.pause_all_processes()
    release.set()

    assert wait_until(lambda: run.manager.processes)
    time.sleep(0.5)
    assert run.count() <= 1

    run.manager.continue_all_processes()
    assert run.is_counting()
    run.manager.stop_all_processes()


def test_several_processes_pause_and_stop_together(tmp_path):
    runs = Run(tmp_path / "process")
    second_folder = tmp_path / "second"
    second = Run(second_folder)
    runs.manager.set_parameters_paths([str(runs.script), str(second.script)])

    runs.manager.start_all_processes()
    assert runs.is_counting() and second.is_counting()

    runs.manager.pause_all_processes()
    time.sleep(0.1)
    assert not runs.is_counting() and not second.is_counting()

    runs.manager.continue_all_processes()
    assert runs.is_counting() and second.is_counting()

    runs.manager.stop_all_processes()
    assert runs.manager.active_process_count() == 0


def test_more_output_than_a_pipe_holds_does_not_block_a_process(tmp_path):
    """The 'breaks after 1-2 mins' bug: SRM blocked on a full stdout pipe nobody was reading."""
    script = """
        import os, sys
        for _ in range(4000):
            print('x' * 100, flush=True)
        open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'done'), 'w').close()
    """
    run = Run(tmp_path / "process", script=script)
    run.manager.start_all_processes()

    assert wait_until(lambda: (run.folder / "done").exists())

    run.manager.stop_all_processes()


def test_an_evaluation_with_a_lot_of_output_finishes(tmp_path):
    script = """
        for _ in range(4000):
            print('x' * 100, flush=True)
    """
    run = Run(tmp_path / "process", script=script)

    assert run.evaluate()


def test_an_evaluation_that_hangs_is_given_up_on(tmp_path, monkeypatch):
    script = """
        import time
        time.sleep(60)
    """
    run = Run(tmp_path / "process", script=script)
    monkeypatch.setattr(ProcessManager, "EVALUATION_TIMEOUT", 0.2)

    assert not run.evaluate()
    assert run.manager.test_processes == {}


def test_a_failing_evaluation_reports_failure(tmp_path):
    script = """
        import sys
        sys.exit(3)
    """
    run = Run(tmp_path / "process", script=script)

    assert not run.evaluate()


def test_stop_ends_a_running_evaluation(tmp_path):
    script = """
        import time
        time.sleep(60)
    """
    run = Run(tmp_path / "process", script=script)
    results = []
    thread = threading.Thread(target=lambda: results.append(run.evaluate()))
    thread.start()
    assert wait_until(lambda: run.manager.test_processes)

    run.manager.stop_all_processes()
    thread.join(5)

    assert results == [False]


def test_a_process_marked_failed_is_not_started_again(tmp_path):
    run = Run(tmp_path / "process", limit=1)
    run.manager.register_callback('process_finished', lambda id, returncode: run.manager.mark_failed(id))
    run.manager.start_all_processes()

    assert wait_until(lambda: run.manager.active_process_count() == 0)
    assert run.runs() == 1


def test_a_missing_executable_is_reported(tmp_path):
    run = Run(tmp_path / "process")
    run.manager.executable_path = os.path.join(str(tmp_path), "no such file")
    failures = []
    run.manager.register_callback('process_failed', lambda id, reason: failures.append(id))

    run.manager.start_all_processes()

    assert wait_until(lambda: failures == [0])
    assert wait_until(lambda: run.manager.active_process_count() == 0)
    run.manager.stop_all_processes()
