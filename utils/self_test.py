"""The hidden self-test of a packaged build: ECFpyDesk --self-test REPORT_PATH

CI runs this on each package, and for Windows that is the only proof the app works. So it is
the app itself that runs: the real window, Controller and Model, and the bundled SRM. The test
presses the same buttons and calls the same handlers a user reaches. Only two things differ: an
error goes to the report instead of a dialog nobody could close, and the file dialog is
answered by the test.

A windowed app has no stdout, so the result is a JSON report, rewritten after each step: a
crash still shows how far the test got. The exit code is 0 only if every step passed.
"""
import json
import logging
import math
import os
import platform
import sys
import threading
import time
import traceback
from unittest import mock

import customtkinter
import psutil

import controllers.input
from controllers.main import Controller
from controllers.process import IDLE, PAUSED, RUNNING
from models.main import Model
from utils import paths
from views.main import View

OVERALL_TIMEOUT = 600  # seconds, the whole test normally takes under a minute
WAIT_TIMEOUT = 120
EXIT_FAILED = 1
EXIT_TIMED_OUT = 2

ECF_BANNER = "ECF, version 1.6.1"
TEMPLATES = ["srmGP.txt", "srmGEP.txt", "srmAP.txt"]
# File and variable count. The last one stays loaded for the rest of the test, and it is the
# one SRM cannot fit almost exactly, which would leave errors too small to compare.
SAMPLE_FILES = {"data_1var.txt": 1, "data_2var_log.txt": 2, "data_2var.txt": 2}
BUNDLED_FILES = [
    "config.json",
    "srm/srm_eval.txt",
    *(f"srm/{template}" for template in TEMPLATES),
    *(f"srm/{sample}" for sample in SAMPLE_FILES),
    *(f"resources/{icon}.png" for icon in ("start", "pause", "stop", "stop_grey")),
]
CUSTOMTKINTER_ASSETS = ["themes/dark-blue.json", "fonts/Roboto/Roboto-Regular.ttf", "fonts/CustomTkinter_shapes_font.otf"]

MAX_GENERATIONS = "ECF/Registry/Entry/term.maxgen"
MAX_EVALUATIONS = "ECF/Registry/Entry/term.eval"
STAGNATION = "ECF/Registry/Entry/term.stagnation"
LOG_FREQUENCY = "ECF/Registry/Entry/log.frequency"

PLOT_LABELS = {0: "Function", 1: "Residual Error", 2: "Residual Error %"}
PLOT_OPTIONS = [
    ("plot_y_index", [0, 1, 2]),
    ("plot_x_index", [-1, 0, 1]),
    ("plot_type", ["scatter", "plot"]),
    ("plot_scale", [0, 1, 2, 3]),
]


class SelfTestFailure(Exception):
    pass


def check(condition, message):
    if not condition:
        raise SelfTestFailure(message)


class ErrorLogHandler(logging.Handler):
    """Goes into the report. An error logged on a background thread fails the test."""

    def __init__(self, self_test):
        super().__init__(logging.INFO)
        self.self_test = self_test

    def emit(self, record):
        message = f"{record.levelname} {record.name}: {record.getMessage()}"
        self.self_test.report["log"].append(message)
        if record.levelno >= logging.ERROR:
            self.self_test.errors.append(message)


class SelfTest:
    def __init__(self, report_path):
        self.report_path = report_path
        self.report = {
            "passed": False,
            "frozen": bool(getattr(sys, "frozen", False)),
            "system": platform.platform(),
            "executable": sys.executable,
            "app_root": paths.app_root(),
            "user_data": paths.user_data_dir(),
            "steps": [],
            "log": [],
            "failure": None,
        }
        self.errors = []
        self.view = None
        self.model = None
        self.controller = None
        self.bundle_before = None
        self.running = []

    def write_report(self):
        # Replaced in one go, so that the watchdog never leaves half a report behind
        temporary_path = f"{self.report_path}.tmp"
        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump(self.report, file, indent=2)
        os.replace(temporary_path, self.report_path)

    def run(self):
        steps = [
            ("files are bundled", self.check_bundle),
            ("window opens", self.open_window),
            *[(f"{template} runs and SRM evaluates its Individuals", lambda index=index: self.run_template(index)) for index, template in enumerate(TEMPLATES)],
            *[(f"{sample} loads and runs", lambda sample=sample: self.run_sample_file(sample)) for sample in SAMPLE_FILES],
            ("Processes share a Pareto front", self.run_processes),
            ("pause suspends SRM", self.pause),
            ("a paused run still evaluates", self.evaluate_while_paused),
            ("continue resumes SRM", self.resume),
            ("stop ends SRM", self.stop),
            ("plot options draw", self.draw_plot_options),
            ("closing the window leaves nothing running", self.close_window),
            ("nothing was written into the app", self.check_bundle_unchanged),
        ]
        for name, step in steps:
            started = time.monotonic()
            detail = step()
            self.report["steps"].append({"name": name, "seconds": round(time.monotonic() - started, 1), "detail": detail})
            self.write_report()
        self.report["passed"] = True

    def pump_until(self, condition, what, timeout=WAIT_TIMEOUT):
        """Runs the window while waiting: update() fires the app's real timers and events."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.view.update()
            check(not self.errors, f"While waiting for {what}: {self.errors}")
            if condition():
                return
            time.sleep(0.02)
        raise SelfTestFailure(f"Timed out waiting for {what}")

    def pump_for(self, seconds):
        deadline = time.monotonic() + seconds
        self.pump_until(lambda: time.monotonic() >= deadline, f"{seconds} s to pass")

    def check_bundle(self):
        missing = [name for name in BUNDLED_FILES if not os.path.isfile(paths.resolve_resource(name))]
        check(not missing, f"Missing from the app: {missing}")

        assets = os.path.join(os.path.dirname(customtkinter.__file__), "assets")
        missing = [name for name in CUSTOMTKINTER_ASSETS if not os.path.isfile(os.path.join(assets, *name.split("/")))]
        check(not missing, f"Missing from customtkinter: {missing}")

        with open(paths.resource_path("config.json"), "r") as file:
            srm = paths.srm_executable(json.load(file)["SRM_path"])
        check(os.path.isfile(srm), f"SRM is not at {srm}")
        check(os.access(srm, os.X_OK), f"SRM at {srm} is not executable")

        if self.report["frozen"]:
            self.bundle_before = self.list_bundle()
        return srm

    def list_bundle(self):
        files = {}
        for directory, _, names in os.walk(paths.app_root()):
            for name in names:
                path = os.path.join(directory, name)
                status = os.stat(path)
                files[os.path.relpath(path, paths.app_root())] = (status.st_size, status.st_mtime_ns)
        return files

    def open_window(self):
        self.model = Model()
        self.view = View()
        self.view.display_error = self.errors.append
        self.view.report_callback_exception = lambda *error: self.errors.append("".join(traceback.format_exception(*error)))
        self.controller = Controller(self.model, self.view)
        self.pump_for(0.5)

        check(self.view.winfo_exists(), "The window does not exist")
        check(self.view.input_frame.input_file_button._full_name == "data_2var.txt", "The input screen does not show the sample data")
        check(len(self.view.input_frame.variable_checkboxes) == 2, "The input screen does not show two variables")
        return f"Tk {self.view.tk.call('info', 'patchlevel')}"

    def press(self, button):
        button.invoke()
        self.view.update()

    def press_start_or_pause(self):
        self.press(self.view.navigation_frame.toggle_process_button)

    def press_stop(self):
        self.press(self.view.navigation_frame.stop_process_button)
        self.pump_until(lambda: not self.controller.is_run_active(), "the run to end")

    def configure_run(self, threads, split, generations):
        self.model.set_variable_with_path(MAX_GENERATIONS, str(generations))
        self.model.set_variable_with_path(LOG_FREQUENCY, "5")
        self.model.set_variable("thread_num", threads)
        self.model.set_variable("train_test_split", split)

    def front(self):
        return self.model.best_functions or []

    def tested_front(self):
        """The Individuals of the front that SRM evaluated on the test set during the run."""
        return [function for function in self.front() if "test_error" in function]

    def short_run(self):
        self.configure_run(threads=1, split=0.7, generations=30)
        self.press_start_or_pause()
        check(self.controller.process_manager.state == RUNNING, "The run did not start")
        self.pump_until(lambda: self.front() and self.tested_front(), "a Pareto front")
        self.press_stop()

    def compare_with_reported_error(self, individual, data_type):
        """What SRM evaluates on the data must give the error SRM reported for the Individual."""
        function = individual["function"]
        reported = individual["error"] if data_type == "train" else individual["test_error"]
        _, solutions = self.controller.evaluate_function(function, data_type=data_type)
        rows = self.model.get_data(data_type)
        check(solutions is not None, f"SRM did not evaluate '{function}' on the {data_type} set")
        check(len(solutions) == len(rows[0]), f"SRM returned {len(solutions)} values for {len(rows[0])} {data_type} rows")
        error = sum((y - f) ** 2 for y, f in zip(rows[-1], solutions)) / len(solutions)
        check(math.isclose(error, reported, rel_tol=1e-3, abs_tol=1e-6), f"'{function}' has {data_type} error {reported}, its values give {error}")
        return error

    def run_template(self, index):
        def choose_template(choices):
            return choices[index if len(choices) > 1 else 0][0]

        with mock.patch("models.config.choose_random_element_with_probability", choose_template):
            self.short_run()
            template = os.path.basename(self.model.config_manager.configurations[0].template_path)
            check(template == TEMPLATES[index], f"Process ran {template}")
            best = self.tested_front()[-1]
            train_error = self.compare_with_reported_error(best, "train")
            test_error = self.compare_with_reported_error(best, "test")

        output_path = os.path.join(self.model.process_directory("eval"), "evaluation_output.txt")
        with open(output_path, "r", errors="replace") as file:
            check(ECF_BANNER in file.read(), f"'{ECF_BANNER}' is not in SRM's output")
        return f"{best['function']}: train error {train_error:.6g}, test error {test_error:.6g}"

    def run_sample_file(self, sample):
        frame = self.view.input_frame
        with mock.patch.object(controllers.input.filedialog, "askopenfilename", lambda: paths.resource_path("srm", sample)):
            self.press(frame.input_file_button.button)
        check(frame.input_file_button._full_name == sample, "The input screen does not show the file")
        check(len(frame.variable_checkboxes) == SAMPLE_FILES[sample], f"The input screen shows {len(frame.variable_checkboxes)} variables")

        self.short_run()
        return f"{len(self.model.train_input_data[0])} train rows, {len(self.model.test_input_data[0])} test rows, {len(self.front())} on the front"

    def run_processes(self):
        """A run with no end of its own, for pause and stop to act on."""
        self.configure_run(threads=3, split=0.7, generations=1000000)
        self.model.set_variable_with_path(MAX_EVALUATIONS, "1000000000")
        self.model.set_variable_with_path(STAGNATION, "1000000")
        self.press_start_or_pause()

        states = self.model.process_states
        self.pump_until(lambda: len(self.front()) > 1 and all(state["best_functions"] for state in states.values()), "results from every Process")
        manager = self.controller.process_manager
        check(len(manager.processes) == self.model.thread_num, f"{len(manager.processes)} Processes run, {self.model.thread_num} should")

        # What the screen lists is the front across all Processes
        self.pump_until(lambda: self.view.results_frame.best_functions == self.front(), "the results screen to refresh")
        sizes = [function["size"] for function in self.front()]
        errors = [function["error"] for function in self.front()]
        check(sizes == sorted(sizes) and errors == sorted(errors, reverse=True), f"Not a Pareto front: {sizes} {errors}")
        check(self.view.results_frame.winfo_ismapped(), "Start did not switch to the results screen")
        return f"{len(states)} Processes, {len(self.front())} on the front"

    def cpu_seconds(self, process):
        times = psutil.Process(process.pid).cpu_times()
        return times.user + times.system

    def total_cpu_seconds(self):
        return sum(self.cpu_seconds(process) for process in self.running)

    def pause(self):
        self.running = list(self.controller.process_manager.processes.values())
        self.press_start_or_pause()
        check(self.controller.process_manager.state == PAUSED, "The run did not pause")
        self.pump_for(0.5)

        before = self.total_cpu_seconds()
        self.pump_for(1.5)
        used = self.total_cpu_seconds() - before
        check(used < 0.05, f"SRM used {used:.2f} s of CPU while paused")
        check(all(process.poll() is None for process in self.running), "SRM ended on pause")
        return f"{len(self.running)} Processes used {used:.3f} s of CPU in 1.5 s"

    def evaluate_while_paused(self):
        self.view.results_frame.invoke_callback("select_row", len(self.front()) - 1)
        check(self.view.results_frame.current_active_row == len(self.front()) - 1, "The row was not selected")
        self.compare_with_reported_error(self.front()[-1], "train")

    def resume(self):
        before = self.total_cpu_seconds()
        self.press_start_or_pause()
        check(self.controller.process_manager.state == RUNNING, "The run did not continue")
        self.pump_until(lambda: self.total_cpu_seconds() - before > 0.2, "SRM to use the CPU again")
        return f"{self.total_cpu_seconds() - before:.2f} s of CPU after continue"

    def stop(self):
        self.press_stop()
        check(self.controller.process_manager.state == IDLE, "The run did not stop")
        check(all(process.poll() is not None for process in self.running), "SRM still runs after stop")

    def draw_plot_options(self):
        frame = self.view.results_frame
        drawn = 0
        for show_test_data in (0, 1):
            frame.invoke_callback("show_test_data", show_test_data)
            self.pump_until(lambda: frame.current_active_row is not None, "a selected row")
            for name, values in PLOT_OPTIONS:
                for value in values:
                    frame.invoke_callback("dropdown_option_change", name, value)
                    self.view.update()
                    labels = frame.ax.get_legend_handles_labels()[1]
                    expected = PLOT_LABELS[self.model.plot_y_index or 0]
                    check(expected in labels, f"{name}={value} drew {labels}, not {expected}")
                    drawn += 1
                frame.invoke_callback("dropdown_option_change", name, values[0])
        check(not self.errors, f"Drawing failed: {self.errors}")
        return f"{drawn} plots"

    def close_window(self):
        self.controller.handle_close()
        self.view = None
        left = psutil.Process().children(recursive=True)
        check(not left, f"Still running: {left}")

    def check_bundle_unchanged(self):
        if self.bundle_before is None:
            return "skipped outside a package"
        after = self.list_bundle()
        changed = [name for name in after.keys() | self.bundle_before.keys() if after.get(name) != self.bundle_before.get(name)]
        check(not changed, f"Changed inside the app: {changed[:20]}")
        return f"{len(after)} files"

    def abandon(self):
        """After a failure nothing may outlive the test."""
        for process in psutil.Process().children(recursive=True):
            process.kill()


def run(report_path):
    """Returns the exit code."""
    report_path = os.path.abspath(report_path)
    self_test = SelfTest(report_path)
    self_test.write_report()
    logging.getLogger().addHandler(ErrorLogHandler(self_test))

    def give_up():
        self_test.report["failure"] = f"Timed out after {OVERALL_TIMEOUT} s"
        self_test.write_report()
        self_test.abandon()
        os._exit(EXIT_TIMED_OUT)

    watchdog = threading.Timer(OVERALL_TIMEOUT, give_up)
    watchdog.daemon = True
    watchdog.start()

    try:
        self_test.run()
    except Exception:
        self_test.report["failure"] = traceback.format_exc()
        self_test.abandon()
    watchdog.cancel()
    self_test.write_report()
    return 0 if self_test.report["passed"] else EXIT_FAILED
