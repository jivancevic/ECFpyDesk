"""The real Controller and Model against the real SRM. Only the widgets are stand-ins."""
import os
import subprocess
import time
from unittest.mock import MagicMock

import pytest

from conftest import requires_srm
from controllers.main import Controller
from controllers.process import IDLE, PAUSED, RUNNING
from models.best_file import parse_best_text
from models.main import Model
from utils import paths
from utils.helper import initial_label

pytestmark = requires_srm


class StubView:
    """Stands in for the Tk window. Timers run when the test pumps them, as the main loop would."""

    def __init__(self, windowing_system="x11"):
        self.tk = MagicMock(call=MagicMock(return_value=windowing_system))
        self.commands = {}
        self.timers = {}
        self.errors = []
        self.next_timer = 0
        checkboxes = {i: MagicMock(get=MagicMock(return_value=1)) for i in range(2)}
        input_frame = MagicMock(variable_checkboxes=checkboxes, checkbox_vars={}, params_vars={}, edit_mode=False)
        input_frame.terminal_set.get.return_value = "[-1 1]"
        results_frame = MagicMock(best_functions=[], current_active_row=None)
        results_frame.solutions_list_frame.winfo_children.return_value = []
        results_frame.clear_frame.side_effect = lambda: self.reset_results(results_frame)
        self.frames = {"navigation": MagicMock(), "input": input_frame, "results": results_frame}

    @staticmethod
    def reset_results(frame):
        frame.best_functions = []
        frame.current_active_row = None

    def after(self, _ms, callback):
        self.next_timer += 1
        self.timers[self.next_timer] = callback
        return self.next_timer

    def after_cancel(self, timer):
        self.timers.pop(timer, None)

    def pump(self):
        timers, self.timers = self.timers, {}
        for callback in timers.values():
            callback()

    def display_error(self, message):
        self.errors.append(message)

    def protocol(self, *_args):
        pass

    def createcommand(self, name, callback):
        self.commands[name] = callback

    def destroy(self):
        pass


class App:
    def __init__(self, generations=20, threads=2, split=1):
        self.view = StubView()
        self.model = Model()
        self.controller = Controller(self.model, self.view)
        self.controller.COLLECT_INTERVAL = 0.05
        self.model.set_variable_with_path("ECF/Registry/Entry/term.maxgen", str(generations))
        self.model.set_variable_with_path("ECF/Registry/Entry/log.frequency", "5")
        self.model.set_variable("thread_num", threads)
        self.model.set_variable("train_test_split", split)

    def pump_until(self, condition, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.view.pump()
            if condition():
                return True
            time.sleep(0.02)
        return False

    def front(self):
        return self.model.best_functions or []

    def finish(self):
        self.controller.stop_all_processes()
        self.pump_until(lambda: not self.controller.is_run_active())
        self.view.pump()


@pytest.fixture
def app():
    apps = []

    def create(**kwargs):
        apps.append(App(**kwargs))
        return apps[-1]

    yield create
    for instance in apps:
        instance.controller.handle_close()


def force_template(monkeypatch, index):
    monkeypatch.setattr("models.config.choose_random_element_with_probability", lambda choices: choices[index if len(choices) > 1 else 0][0])


def test_a_run_produces_a_pareto_front(app):
    run = app()
    run.controller.toggle_process()

    assert run.pump_until(lambda: len(run.front()) > 1)
    run.finish()

    assert run.view.errors == []
    sizes = [function["size"] for function in run.front()]
    errors = [function["error"] for function in run.front()]
    assert sizes == sorted(sizes)
    assert errors == sorted(errors, reverse=True)
    assert run.view.frames["results"].best_functions == run.front()


def test_results_keep_coming_when_srm_finishes_and_starts_again(app):
    run = app(generations=5, threads=1)
    run.controller.toggle_process()

    assert run.pump_until(lambda: len(run.model.process_states[0]['functions_seen']) > 8)
    run.finish()

    assert run.view.errors == []


@pytest.mark.parametrize("template_index,name", [(0, "GP"), (1, "GEP"), (2, "AP")])
def test_srm_evaluates_individuals_of_every_template(app, monkeypatch, template_index, name):
    force_template(monkeypatch, template_index)
    run = app(threads=1)
    run.controller.toggle_process()
    assert run.pump_until(lambda: run.front())
    run.finish()

    best = run.front()[-1]
    _, solutions = run.controller.evaluate_function(best["function"], data_type="train")

    rows = run.model.train_input_data
    assert len(solutions) == len(rows[0])
    mean_square_error = sum((y - f) ** 2 for y, f in zip(rows[-1], solutions)) / len(solutions)
    assert mean_square_error == pytest.approx(best["error"], rel=1e-3)


@pytest.mark.parametrize("metric,error_of", [
    ("mean_square_error", lambda y, f: (y - f) ** 2),
    ("mean_absolute_error", lambda y, f: abs(y - f)),
])
def test_individuals_are_ranked_by_test_error_with_a_test_set(app, metric, error_of):
    run = app(split=0.7)
    run.model.set_search_metric(metric)
    run.controller.toggle_process()
    assert run.pump_until(lambda: len(run.front()) > 1)
    run.finish()

    assert run.view.errors == []
    assert len(run.model.train_input_data[0]) == 70
    assert len(run.model.test_input_data[0]) == 30

    run.model.data_type = "test"
    run.controller.update_solutions_frame()
    front = run.front()
    assert front
    assert all(function["error"] == function["test_error"] for function in front)

    _, solutions = run.controller.evaluate_function(front[0]["function"], data_type="test")
    rows = run.model.test_input_data
    assert len(solutions) == 30
    test_error = sum(error_of(y, f) for y, f in zip(rows[-1], solutions)) / 30
    assert test_error == pytest.approx(front[0]["test_error"], rel=1e-3)
    train_errors = {function["function"]: function["error"] for function in run.model.process_states[0]["best_functions"]}
    assert front[0]["test_error"] != train_errors.get(front[0]["function"])


@pytest.mark.parametrize("data_file,terminal_set", [
    ("data_1var.txt", "x1 [-1 1]"),
    ("data_2var.txt", "x1 x2 [-1 1]"),
    ("data_2var_log.txt", "x1 x2 [-1 1]"),
])
def test_every_sample_file_runs(app, data_file, terminal_set):
    run = app(threads=1, split=0.7)
    run.model.set_input_path(paths.resource_path("srm", data_file))
    run.model.set_terminal_set(terminal_set)
    run.controller.toggle_process()

    assert run.pump_until(lambda: run.front())
    run.finish()

    assert run.view.errors == []
    assert len(run.controller.evaluate_function(run.front()[0]["function"], data_type="train")[1]) == len(run.model.train_input_data[0])


def test_error_weights_follow_their_rows_through_a_real_run(app, tmp_path):
    """All the weight is on the first row, so a Process can only fit that row, and the reported
    error is the weighted one."""
    rows = len(open(paths.resource_path("srm", "data_2var.txt")).readlines())
    weights = tmp_path / "weights.txt"
    weights.write_text("\n".join(["1000"] + ["0"] * (rows - 1)) + "\n")
    run = app(threads=1, split=0.7)
    run.model.set_variable("test_sample", "sequential")
    run.model.set_error_path(str(weights))
    run.controller.toggle_process()

    assert run.pump_until(lambda: run.front())
    run.finish()

    assert run.view.errors == []
    tested = run.model.process_states[0]["best_test_functions"]
    # The test set holds the last rows, whose weights are all zero
    assert tested and all(function["test_error"] == 0 for function in tested)


def test_an_evaluation_needs_no_function_from_the_users_set(app, monkeypatch):
    """GEP links genes with - even when the user turned - off."""
    force_template(monkeypatch, 1)
    run = app(threads=1)
    run.model.set_function_set("+ * /")
    run.controller.toggle_process()
    assert run.pump_until(lambda: run.front())
    run.finish()

    assert run.view.errors == []
    assert run.controller.evaluate_function(run.front()[0]["function"], data_type="train")[1]


def test_pause_stops_the_best_file_and_continue_picks_it_up(app):
    run = app(generations=100000, threads=1)
    run.model.set_variable_with_path("ECF/Registry/Entry/term.eval", "1000000000")
    run.model.set_variable_with_path("ECF/Registry/Entry/term.stagnation", "1000000")
    run.controller.toggle_process()
    best_file = run.model.config_manager.configurations[0].best_file_path
    assert run.pump_until(lambda: os.path.exists(best_file) and os.path.getsize(best_file) > 0)

    run.controller.toggle_process()
    assert run.controller.process_manager.state == PAUSED
    time.sleep(0.1)
    paused_size = os.path.getsize(best_file)
    time.sleep(1)
    assert os.path.getsize(best_file) == paused_size

    # A paused run still answers: selecting a row evaluates through SRM
    assert run.pump_until(lambda: run.front())
    assert run.controller.evaluate_function(run.front()[0]["function"], data_type="train")[1]

    run.controller.toggle_process()
    assert run.controller.process_manager.state == RUNNING
    assert run.pump_until(lambda: os.path.getsize(best_file) > paused_size)

    run.finish()
    assert run.controller.process_manager.state == IDLE


def test_stop_from_pause_then_a_new_run_starts_clean(app):
    run = app(generations=100000, threads=1)
    run.controller.toggle_process()
    assert run.pump_until(lambda: run.front())
    run.controller.toggle_process()
    run.finish()
    assert run.front()

    run.controller.toggle_process()
    assert run.controller.process_manager.state == RUNNING
    assert run.model.function_solutions == {}
    assert run.view.frames["results"].best_functions == []
    assert run.pump_until(lambda: run.front())
    run.finish()


def test_the_last_block_of_every_srm_run_reaches_the_results(app):
    """At the real collect interval: SRM ends and restarts faster than the app reads."""
    run = app(generations=10, threads=1)
    run.controller.COLLECT_INTERVAL = Controller.COLLECT_INTERVAL
    last_functions = []
    reset_file_reading = run.model.reset_file_reading

    def record_last_block(id):
        path = run.model.config_manager.configurations[id].best_file_path
        if os.path.exists(path):
            with open(path) as file:
                last_functions.append(parse_best_text(file.read())[0][-1]["function"])
        reset_file_reading(id)

    run.model.reset_file_reading = record_last_block
    run.controller.toggle_process()

    assert run.pump_until(lambda: len(last_functions) >= 5)
    run.finish()

    assert set(last_functions) <= run.model.process_states[0]["functions_seen"]


def test_a_failed_evaluation_costs_one_individual_not_the_batch(app, monkeypatch):
    run = app(threads=1, split=0.7)
    run.controller.toggle_process()
    run.controller.stop_all_processes()
    run.pump_until(lambda: not run.controller.is_run_active())
    run.model.prepare_run()
    run.model.create_process_config(0, is_test=False)
    run.model.create_process_config(0, is_test=True)

    def fail_on_first(_id, _config, individual):
        if individual["function"] == "first":
            raise ValueError("SRM wrote no evaluation result")
        return 0.5, [1.0]

    monkeypatch.setattr(run.controller, "run_evaluation", fail_on_first)
    individuals = [
        {"generation": 0, "function": "first", "error": 0.9, "size": 3, "prefix_function": "x1"},
        {"generation": 10, "function": "second", "error": 0.1, "size": 5, "prefix_function": "x2"},
    ]
    monkeypatch.setattr(run.model, "read_new_individuals", lambda _id: individuals)

    run.controller.update_best_functions(0)

    state = run.model.process_states[0]
    assert [function["function"] for function in state["best_functions"]] == ["first", "second"]
    assert [function["function"] for function in state["best_test_functions"]] == ["second"]


def test_a_new_run_waits_for_the_collectors_of_the_last_one(app, monkeypatch):
    run = app(threads=1)
    run.controller.toggle_process()
    assert run.pump_until(lambda: run.controller.collector_threads)
    collectors = list(run.controller.collector_threads.values())
    run.controller.process_manager.stop_all_processes()
    run.controller.collectors_stop.set()
    alive_during_prepare = []
    prepare_input_data = run.controller.prepare_input_data

    def check_collectors():
        alive_during_prepare.extend(thread for thread in collectors if thread.is_alive())
        return prepare_input_data()

    monkeypatch.setattr(run.controller, "prepare_input_data", check_collectors)
    run.controller.start_all_processes()

    assert alive_during_prepare == []
    run.finish()


def test_a_saved_error_metric_starts_the_dropdown(app):
    saved = Model().config_manager
    saved.save_manual_parameters(saved.read_manual_parameters().replace("mean_square_error", "mean_absolute_error"))

    run = app(threads=1)

    initial = run.view.frames["input"].initial_values["search_metric"]
    assert initial == "mean_absolute_error"
    assert initial_label([("MSE", "mean_square_error"), ("MAE", "mean_absolute_error")], initial) == "MAE"
    assert initial_label([("MSE", "mean_square_error")], "unknown") == "MSE"


def test_rebuilt_plot_dropdowns_keep_the_users_choice(app):
    run = app(threads=1)
    run.model.plot_scale = 3
    run.model.plot_type = "plot"

    run.controller.results_controller.add_test_option(should_add=True)

    assert run.view.frames["results"].initial_values["plot_scale"] == 3
    assert run.view.frames["results"].initial_values["plot_type"] == "plot"


@pytest.mark.parametrize("windowing_system,registered", [("aqua", True), ("x11", False), ("win32", False)])
def test_quit_from_the_macos_menu_goes_through_the_same_close(windowing_system, registered, monkeypatch):
    view = StubView(windowing_system)
    controller = Controller(Model(), view)

    assert ("::tk::mac::Quit" in view.commands) == registered
    if registered:
        assert view.commands["::tk::mac::Quit"] == controller.handle_close


def test_a_process_that_cannot_run_is_reported_once_and_not_restarted(app, monkeypatch):
    force_template(monkeypatch, 0)
    run = app(threads=1)
    run.controller.toggle_process()
    run.controller.stop_all_processes()
    run.pump_until(lambda: not run.controller.is_run_active())

    run.model.set_variable_with_path("ECF/Registry/Entry/population.size", "not a number")
    run.model.set_variable_with_path("ECF/Genotype/Entry/nosuchparameter", "1")
    run.controller.toggle_process()

    assert run.pump_until(lambda: run.controller.process_manager.state == IDLE)
    assert len(run.view.errors) == 1
    assert "SRM process 0 stopped" in run.view.errors[0]


def test_a_missing_input_file_is_an_error_and_starts_nothing(app, tmp_path):
    run = app()
    run.model.set_input_path(str(tmp_path / "missing.txt"))

    run.controller.toggle_process()

    assert run.controller.process_manager.state == IDLE
    assert len(run.view.errors) == 1


def test_a_missing_srm_is_an_error_and_starts_nothing(app, tmp_path):
    run = app()
    run.controller.process_manager.executable_path = str(tmp_path / "SRM")

    run.controller.toggle_process()

    assert run.controller.process_manager.state == IDLE
    assert "SRM was not found" in run.view.errors[0]


def test_a_run_writes_nothing_beside_the_app(app, data_dir):
    def status():
        return subprocess.run(["git", "status", "--porcelain", "--ignored", "srm", "config.json"], cwd=paths.app_root(), capture_output=True, text=True).stdout

    before = status()
    run = app()
    run.controller.toggle_process()
    assert run.pump_until(lambda: run.front())
    run.finish()

    assert status() == before
    assert os.path.exists(os.path.join(str(data_dir), "temp", "0", "best.txt"))


def test_the_app_can_start_from_another_directory(app, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run = app()
    run.controller.toggle_process()

    assert run.pump_until(lambda: run.front())
    run.finish()


def test_closing_the_window_ends_srm(app):
    run = app(generations=100000)
    run.controller.toggle_process()
    assert run.pump_until(lambda: run.controller.process_manager.processes)
    processes = list(run.controller.process_manager.processes.values())

    run.controller.handle_close()

    assert all(process.poll() is not None for process in processes)
