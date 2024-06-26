import json
import numpy as np
from utils.plot import safe_dict
import threading

from utils.file import delete_all_files_in_directory
from controllers.process import ProcessManager
from controllers.navigation import NavigationController
from controllers.input import InputController
from controllers.results import ResultsController

class Controller:
    REFRESH_RATE = 1

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

        self.process_manager = ProcessManager(self.config["SRM_path"])
        self.config_manager = self.model.config_manager
        
        self.register_callbacks()

        self.update_timer = None
        self.process_threads = {}
        self.app_directory = app_directory
        delete_all_files_in_directory('srm/temp')

    def register_callbacks(self):
        self.process_manager.register_callback('pre_process_start', self.pre_process_setup)
        self.process_manager.register_callback('timer_finished', self.handle_timer_finished)

    def get_config(self):
        return self.config
    
    def get_parameters_file_path(self):
        return self.config["SRM_parameters_path"]
    
    def handle_timer_finished(self, id):
        print(f"\nTimer finished for id: {id}\n")
        self.update_solutions(id)

    def update_solutions(self, id=None):
        if id is not None:
            if id in self.process_threads and self.process_threads[id].is_alive():
                print(f"Update already in progress for process ID: {id}")
            else:
                # Start or restart the thread for specific process ID
                self.process_threads[id] = threading.Thread(target=self.update_best_functions, args=(id,))
                self.process_threads[id].start()
                print(f"Started test thread for process ID: {id}, and thread_id: {self.process_threads[id].native_id}")
        else:
            # Update all processes
            for id in self.process_manager.processes.keys():
                self.update_solutions(id)

    def update_best_functions(self, id):
        # Your existing logic here to update best functions, handle testing, etc.
        old_best_functions = self.model.get_best_functions(id=id, copy=False)
        best_functions = self.model.parse_best_functions(id)

        if self.model.is_test():
            for generation_data in best_functions:
                if generation_data not in old_best_functions:
                    config = self.model.get_test_configurations(id)
                    individual_file_path = f'srm/temp/{id}/individual.txt'
                    self.model.config_manager.create_individual_file(individual_file_path, generation_data['error'], generation_data['size'], generation_data['prefix_function'])

                    self.process_manager.run_test_process(id=id, individual_path=individual_file_path)

                    error, solutions = self.model.config_manager.parse_best_individual_file(config.best_file_path)
                    generation_data['error'] = error  # Update error after test process execution
        
        pareto_functions = self.model.filter_best_functions(best_functions)
        self.model.set_best_functions(best_functions=pareto_functions, id=id)
        
        # Recursively update if new data is present
        if self.model.has_new_data(id):
            print(f"Has new data for process {id}")
            self.update_best_functions(id)
        else:
            print(f"No new data found for process {id}: last generation {best_functions[-1]['generation']}")
            self.process_manager.running[id] = True

    def handle_frame_timer_finished(self):
        self.update_solutions_frame()
        if self.process_manager.global_running:
            self.start_update_timer()

    def update_solutions_frame(self):
        best_functions = self.model.update_best_functions()
        self.results_controller.update_solutions_frame(best_functions)
    
    def handle_process_output(self, output):
        self.view.results_frame.append_output(output)

    def handle_toggle_process(self):
        self.toggle_process()

    def handle_stop_process(self):
        stop_thread = threading.Thread(target=self.stop_all_processes)
        stop_thread.start()

    def toggle_process(self):
        if self.process_manager.global_running:
            self.pause_all_processes()
        elif len(self.process_manager.processes)>0:
            self.continue_all_processes()
        else:
            self.start_all_processes()

    def start_all_processes(self):
        print("Starting all processes")
        if self.model.input_data is None:
            self.model.load_input_data()
        self.model.split_train_test()

        is_test = self.model.train_test_split < 1
        self.results_controller.add_test_option(should_add=is_test)

        parameters_paths = []
        test_parameters_paths = []
        for id in range(self.model.thread_num):
            path = self.model.create_process_config(id, False)
            parameters_paths.append(path)
            if is_test:
                path = self.model.create_process_config(id, True)
                print(f"Test parameters path: {path}")
                test_parameters_paths.append(path)
        
        self.process_manager.set_thread_num(self.model.thread_num)
        self.process_manager.set_parameters_paths(parameters_paths)
        self.process_manager.set_test_parameters_paths(test_parameters_paths)
        self.model.register_all_processes()
        self.model.data_type = 'train'
        
        self.navigation_controller.set_toggle_process_button_icon("pause")
        self.navigation_controller.set_stop_process_button_icon(True)
        self.results_controller.clear_frame()
        
        self.process_manager.start_all_processes()
        self.start_update_timer()

    def pause_all_processes(self):
        self.process_manager.pause_all_processes()
        if self.update_timer:
            self.update_timer.cancel()
        self.navigation_controller.set_toggle_process_button_icon("start")

    def continue_all_processes(self):
        self.process_manager.continue_all_processes()
        self.start_update_timer()
        self.navigation_controller.set_toggle_process_button_icon("pause")

    def stop_all_processes(self):
        self.process_manager.stop_all_processes()
        self.navigation_controller.set_toggle_process_button_icon("start")
        self.navigation_controller.set_stop_process_button_icon(False)
        self.update_solutions_frame()
    
    def apply_configurations(self):
        self.model.update_default_parameters_file()

    def pre_process_setup(self, id):
        #self.view.results_frame.clear_output_display()
        print(f"Starting process {id}")
        self.model.reset_file_reading(id)

    def handle_input_data_change(self):
        self.model.load_input_data()
        self.results_controller.update_plot()

    def evaluate_function(self, function_str, multivar=False, data=None, data_type=None):
        if data is None:
            data = self.model.get_data(data_type)
        
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
    
    def start_update_timer(self):
        print("\nStarting global update timer\n")
        if 0 in self.process_manager.processes and self.process_manager.processes[0].poll() is None:
            print("Process 0 is still running")
        self.update_timer = threading.Timer(self.REFRESH_RATE, self.handle_frame_timer_finished)    
        self.update_timer.start()

    def start(self):
        self.view.start()