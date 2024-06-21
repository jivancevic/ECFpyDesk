import json
import numpy as np
from utils.plot import safe_dict
import threading

from controllers.process import ProcessManager
from controllers.navigation import NavigationController
from controllers.input import InputController
from controllers.results import ResultsController

class Controller:
    def __init__(self, model, view, app_directory):
        with open('config.json', 'r') as file:
            self.config = json.load(file)

        self.model = model
        self.view = view

        self.navigation_controller = NavigationController(model=model, controller=self, view=view)
        self.input_controller = InputController(model=model, controller=self, view=view)
        self.results_controller = ResultsController(model=model, controller=self, view=view)
    
        self.navigation_controller.initialize_frame()
        self.input_controller.initialize_frame()
        self.results_controller.initialize_frame()

        self.process_manager = ProcessManager(self.config["SRM_path"], self.config["SRM_parameters_path"], self.handle_process_output)
        self.model.set_process_manager(self.process_manager)
        
        self.register_callbacks()

        self.app_directory = app_directory
        self.best_functions_lock = threading.Lock()

    def register_callbacks(self):
        self.process_manager.register_callback('pre_process_start', self.pre_process_setup)
        self.process_manager.register_callback('timer_finished', self.handle_timer_finished)

    def get_config(self):
        return self.config
    
    def get_parameters_file_path(self):
        return self.config["SRM_parameters_path"]
    
    def handle_timer_finished(self):
        self.update_solutions()
        # Restart the timer for the next update
        if self.process_manager.running:
            self.process_manager.start_update_timer()

    def update_solutions(self):
        with self.best_functions_lock:
            self.model.update_best_functions()
            self.results_controller.update_solutions_frame(self.model.get_best_functions())
    
    def handle_process_output(self, output):
        self.view.results_frame.append_output(output)

    def toggle_process(self):
        if self.process_manager.running:
            self.pause_process()
        elif self.process_manager.process:
            self.continue_process()
        else:
            self.start_process()

    def start_process(self):
        if not self.process_manager.running:
            self.navigation_controller.set_toggle_process_button_icon("pause")
            self.navigation_controller.set_stop_process_button_icon(True)
            self.results_controller.clear_frame()
            self.process_manager.start_process()

    def pause_process(self):
        self.process_manager.pause_process()
        self.navigation_controller.set_toggle_process_button_icon("start")

    def continue_process(self):
        self.process_manager.continue_process()
        self.navigation_controller.set_toggle_process_button_icon("pause")

    def stop_process(self):
        self.process_manager.stop_process()
        self.navigation_controller.set_toggle_process_button_icon("start")
        self.navigation_controller.set_stop_process_button_icon(False)
        self.update_solutions()

    def get_best_functions(self):
        return self.model.best_functions

    def handle_toggle_process(self):
        self.toggle_process()

    def handle_stop_process(self):
        stop_thread = threading.Thread(target=self.stop_process)
        stop_thread.start()
    
    def apply_configurations(self):
        self.model.split_train_test()
        self.model.update_configuration()
        self.results_controller.clear_frame()

    def pre_process_setup(self):
        self.view.results_frame.clear_output_display()
        self.model.reset_file_reading()

    def handle_input_data_change(self):
        self.load_input_data()
        self.results_controller.update_plot()

    def load_input_data(self):
        data, multivar = self.model.load_input_data()
        return data, multivar

    def evaluate_function(self, function_str, multivar=False, data=None):
        if data is None:
            data = self.model.get_input_data()
        
        x_values = None
    
        if not multivar:
            # Ensure x_values covers all possible data inputs
            x_values = np.linspace(np.min(data[0]), np.max(data[0]), 400)
            safe_dict['x1'] = x_values
        else:
            variable_dict = {f'x{i+1}': np.array(data[i]) for i in range(len(data))}
            safe_dict.update(variable_dict)
            x_values = np.arange(len(data[0]))  # Assumes the first dimension covers all data points
    
        # Try to evaluate the function string
        try:
            results = eval(function_str, {"__builtins__": None}, safe_dict)
            if np.isscalar(results):
                results = np.full_like(x_values, results)  # Fill the array with the scalar value
        except Exception as e:
            print(f"Error evaluating function '{function_str}': {e}")
            return None, None
        
        return x_values, results
    
    def load_config(self):
        self.model.load_configuration()

    def save_config(self):
        self.model.save_configuration()

    def update_config(self, updates):
        self.model.update_configuration(updates)

    def start(self):
        self.view.start()