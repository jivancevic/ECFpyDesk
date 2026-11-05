import logging
import json
import numpy as np
import os
import threading

from utils import paths
from utils.file import delete_all_files_in_directory, delete_file_if_exists
from utils.helper import find_index_of_dict_with_value_in_array

from controllers.process import ProcessManager, IDLE, RUNNING, PAUSED
from controllers.navigation import NavigationController
from controllers.input import InputController
from controllers.results import ResultsController

logger = logging.getLogger(__name__)

class Controller:
    COLLECT_INTERVAL = 1  # seconds between reads of a Process's best file

    def __init__(self, model, view):
        with open(paths.resource_path('config.json'), 'r') as file:
            self.config = json.load(file)

        self.model = model
        self.view = view
        self.refresh_interval_ms = self.config["refresh_interval_ms"]

        self.config_manager = self.model.config_manager
        self.process_manager = ProcessManager(paths.srm_executable(self.config["SRM_path"]), paths.temp_dir())
        self.register_callbacks()

        self.update_timer = None
        self.collector_threads = {}
        self.collectors_stop = threading.Event()
        self.pending_errors = []
        delete_all_files_in_directory(paths.temp_dir())

        self.navigation_controller = NavigationController(model=model, controller=self, view=view)
        self.input_controller = InputController(model=model, controller=self, view=view)
        self.results_controller = ResultsController(model=model, controller=self, view=view)

        self.navigation_controller.initialize_frame()
        self.input_controller.initialize_frame()
        self.results_controller.initialize_frame()
        self.handle_input_data_change()

        self.view.protocol("WM_DELETE_WINDOW", self.handle_close)
        if self.view.tk.call("tk", "windowingsystem") == "aqua":
            # Cmd+Q and Quit in the macOS menu do not go through the window's close button
            self.view.createcommand("::tk::mac::Quit", self.handle_close)

    def register_callbacks(self):
        self.process_manager.register_callback('pre_process_start', self.pre_process_setup)
        self.process_manager.register_callback('process_finished', self.handle_process_finished)
        self.process_manager.register_callback('process_failed', self.handle_process_failed)

    def get_config(self):
        return self.config

    def handle_process_finished(self, id, returncode):
        """SRM reports most failures with exit code 0, so a run without output is a failure too.
        Starting such a Process again would only fail the same way."""
        if returncode == 0 and self.model.has_best_output(id):
            return
        self.process_manager.mark_failed(id)
        self.handle_process_failed(id, self.read_process_output(id) or f"Exit code {returncode}")

    def handle_process_failed(self, id, reason):
        self.pending_errors.append(f"SRM process {id} stopped.\n\n{reason}")

    def read_process_output(self, id):
        try:
            with open(os.path.join(self.model.process_directory(id), 'output.txt'), 'r', errors='replace') as file:
                lines = [line.strip() for line in file if line.strip()]
        except OSError:
            return None
        return "\n".join(lines[-3:])

    def collect_results(self, id, stop_event):
        """Reads the results of one Process until the run ends. An error in one pass must not
        end the collecting, so it is logged and the next pass goes on."""
        while True:
            stopped = stop_event.wait(self.COLLECT_INTERVAL)
            try:
                self.update_best_functions(id)
            except Exception:
                logger.exception(f"Error reading the results of process {id}")
            if stopped:
                return

    def update_best_functions(self, id):
        individuals = self.model.read_new_individuals(id)
        if not individuals:
            return
        if self.model.run_has_test_set:
            for individual in individuals:
                self.evaluate_on_test_set(id, individual)
        self.model.add_individuals(id, individuals)

    def evaluate_on_test_set(self, id, individual):
        # A failed evaluation costs this Individual its test error, not the rest of the batch
        try:
            result = self.run_evaluation(id, self.model.get_test_configurations(id), individual)
        except (OSError, ValueError) as e:
            logger.warning(f"Evaluating '{individual['function']}' failed: {e}")
            return
        if result is None:
            return
        error, solutions = result
        self.model.update_function_solutions(function=individual['function'], solutions=solutions, data_type='test')
        individual['test_error'] = error

    def run_evaluation(self, id, config, individual):
        """Has SRM evaluate an Individual. Returns the error and the values, or None if it failed."""
        directory = self.model.process_directory(id)
        individual_file_path = os.path.join(directory, 'individual.txt')
        output_path = os.path.join(directory, 'evaluation_output.txt')
        self.model.create_individual_file(individual_file_path, individual['error'], individual['size'], individual['prefix_function'])
        delete_file_if_exists(config.best_file_path)

        if not self.process_manager.run_test_process(id, config.parameters_path, individual_file_path, output_path):
            logger.warning(f"Evaluating '{individual['function']}' failed")
            return None
        return self.model.read_evaluation(config.best_file_path, output_path)

    def handle_frame_timer_finished(self):
        self.update_timer = None
        # One more refresh after the run ends, for what the collectors read last
        was_active = self.is_run_active()
        try:
            self.update_solutions_frame()
            self.show_pending_errors()
            if self.process_manager.state != IDLE and self.process_manager.active_process_count() == 0:
                self.stop_all_processes()
        finally:
            if was_active:
                self.start_update_timer()

    def is_run_active(self):
        return self.process_manager.state != IDLE or any(thread.is_alive() for thread in self.collector_threads.values())

    def show_pending_errors(self):
        while self.pending_errors:
            self.view.display_error(self.pending_errors.pop(0))

    def update_solutions_frame(self):
        best_functions = self.model.update_best_functions()
        self.results_controller.update_solutions_frame(best_functions)

    def handle_toggle_process(self):
        self.toggle_process()

    def handle_stop_process(self):
        self.stop_all_processes()

    def toggle_process(self):
        if self.process_manager.state == RUNNING:
            self.pause_all_processes()
        elif self.process_manager.state == PAUSED:
            self.continue_all_processes()
        else:
            self.start_all_processes()

    def start_all_processes(self):
        # The collectors of the last run may still be evaluating on the files about to change
        for thread in self.collector_threads.values():
            thread.join()

        problem = self.prepare_input_data()
        if problem:
            self.view.display_error(problem)
            return

        self.model.prepare_run()
        is_test = self.model.run_has_test_set

        parameters_paths = []
        for id in range(self.model.thread_num):
            parameters_paths.append(self.model.create_process_config(id, is_test=False, delete_logs=True))
            if is_test:
                self.model.create_process_config(id, is_test=True, delete_logs=True)

        self.process_manager.set_parameters_paths(parameters_paths)

        self.navigation_controller.set_toggle_process_button_icon("pause")
        self.navigation_controller.set_stop_process_button_icon(True)
        self.results_controller.clear_frame()
        self.results_controller.add_test_option(should_add=is_test)

        self.process_manager.start_all_processes()
        self.start_collectors()
        self.start_update_timer()

    def prepare_input_data(self):
        """Returns what stops a run from starting, or None."""
        if not os.path.exists(self.process_manager.executable_path):
            return f"SRM was not found at {self.process_manager.executable_path}. Build it first, see the developer guide."
        self.model.load_input_data()
        problem = self.model.validate_run_settings()
        if problem:
            return problem
        try:
            self.model.split_train_test()
        except (OSError, ValueError) as e:
            return f"The input data could not be prepared: {e}"
        if self.model.train_input_data is None:
            return "The input file has no usable rows."
        return None

    def start_collectors(self):
        self.collectors_stop = threading.Event()
        self.collector_threads = {}
        for id in range(self.model.thread_num):
            self.collector_threads[id] = threading.Thread(target=self.collect_results, args=(id, self.collectors_stop), daemon=True)
            self.collector_threads[id].start()

    def pause_all_processes(self):
        self.process_manager.pause_all_processes()
        self.navigation_controller.set_toggle_process_button_icon("start")

    def continue_all_processes(self):
        self.process_manager.continue_all_processes()
        self.navigation_controller.set_toggle_process_button_icon("pause")

    def stop_all_processes(self):
        self.process_manager.stop_all_processes()
        self.collectors_stop.set()
        self.navigation_controller.set_toggle_process_button_icon("start")
        self.navigation_controller.set_stop_process_button_icon(False)

    def handle_close(self):
        self.stop_all_processes()
        if self.update_timer is not None:
            self.view.after_cancel(self.update_timer)
            self.update_timer = None
        self.view.destroy()

    def apply_configurations(self):
        self.model.update_default_parameters_file()

    def pre_process_setup(self, id):
        self.model.reset_file_reading(id)
        self.config_manager.set_new_seed(id)

    def handle_input_data_change(self):
        data = self.model.load_input_data()
        if data is None:
            logger.warning("No input data loaded; skipping plot updates")
            return
        var_num = len(data)-1
        self.results_controller.update_plot_x_axis(var_num)
        self.results_controller.update_plot()

    def evaluate_function(self, function_str, multivar=False, data=None, data_type=None):
        if data is None:
            data = self.model.get_data(data_type)

        x_values = np.arange(len(data[0]))
        solutions = self.model.get_function_solutions(function_str, data_type)

        if solutions is None:
            solutions = self.calculate_solutions(function_str, data_type)
            if solutions is not None:
                self.model.update_function_solutions(function=function_str, solutions=solutions, data_type=data_type)

        return x_values, solutions

    def calculate_solutions(self, function_str, data_type='train'):
        id = 'eval'
        self.model.create_process_config(id, data_type == 'test')
        config = self.model.get_evaluation_configurations(id)

        best_functions = self.model.get_best_functions()
        individual_data_index = find_index_of_dict_with_value_in_array(best_functions, 'function', function_str)
        if individual_data_index == -1:
            logger.warning(f"Function '{function_str}' not found in best functions")
            return None

        result = self.run_evaluation(id, config, best_functions[individual_data_index])
        return None if result is None else result[1]

    def start_update_timer(self):
        if self.update_timer is not None:
            self.view.after_cancel(self.update_timer)
        # after() runs on the main thread, which is the only one allowed to touch the widgets
        self.update_timer = self.view.after(self.refresh_interval_ms, self.handle_frame_timer_finished)

    def start(self):
        self.view.start()
