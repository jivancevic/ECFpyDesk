import logging
import math
import multiprocessing
import numpy as np
import os
import threading
from .best_file import parse_best_text
from .config import ConfigurationManager
from .parameters import param_paths
from utils import paths
from utils.helper import set_to_string, string_to_set
from utils.file import create_directory, delete_file_if_exists
from utils.publisher import Publisher

logger = logging.getLogger(__name__)

class Model(Publisher):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigurationManager()

        self.configs = {}
        self.process_states = {}

        # Input parameters
        self.params = {}
        self.train_test_split = 1
        self.test_sample = "random"
        self.plot_x_index = None
        self.plot_y_index = None
        self.plot_scale = None
        self.plot_type = None
        self.thread_num = 1

        temp_directory = paths.temp_dir()
        self.train_file_path = os.path.join(temp_directory, 'train.txt')
        self.test_file_path = os.path.join(temp_directory, 'test.txt')
        self.train_weights_path = os.path.join(temp_directory, 'train_weights.txt')
        self.test_weights_path = os.path.join(temp_directory, 'test_weights.txt')
        self.input_data = None
        self.train_input_data = None
        self.test_input_data = None
        self.data_type = 'input'
        self.function_solutions = {}
        self.multivar = False
        self.enabled_functions = set()
        self.best_functions = None
        self.run_has_test_set = False
        self.run_params = {}
        self.run_error_path = None

    def set_variable(self, name, value):
        if name in param_paths:
            self.params[param_paths[name]] = value
        else:
            setattr(self, name, value)

    def set_variable_with_path(self, path, value):
        self.params[path] = value

    def set_input_path(self, path):
        self.params[param_paths["input_path"]] = path
    
    def get_input_path(self):
        return self.params.get(param_paths["input_path"])
    
    def get_current_input_path(self):
        input_path = self.config_manager.get_current_param_value(param_paths["input_path"])
        return paths.resolve_resource(input_path) if input_path else None
    
    def get_current_variable(self, name):
        return self.config_manager.get_current_param_value(param_paths[name])

    def set_error_path(self, path):
        self.params[param_paths["error_path"]] = path

    def get_error_path(self):
        error_path = self.params.get(param_paths["error_path"]) or self.config_manager.get_current_param_value(param_paths["error_path"])
        return paths.resolve_resource(error_path) if error_path else None
    
    def set_terminal_set(self, terminal_set):
        self.params[param_paths["terminal_set"]] = terminal_set

    def get_terminal_set(self):
        return self.params[param_paths["terminal_set"]]
    
    def get_current_terminal_set(self):
        return self.config_manager.get_current_terminal_set()
    
    def set_search_metric(self, search_metric):
        self.params[param_paths["search_metric"]] = search_metric

    def get_search_metric(self):
        return self.params[param_paths["search_metric"]]
    
    def set_function_set(self, function_set):
        self.params[param_paths["function_set"]] = function_set
        self.enabled_functions = string_to_set(function_set)

    def get_function_set(self):
        return self.params[param_paths["function_set"]]
    
    def get_current_function_set(self):
        return self.config_manager.get_current_function_set()
    
    def set_other_parameters(self, other_params):
        self.params.update(other_params)

    def set_parameter(self, path, value):
        self.params[path] = value

    def get_parameter(self, path):
        return self.params.get(path)
    
    def set_thread_count(self, thread_count):
        self.thread_num = thread_count
    
    def get_input_data(self):
        return self.input_data
    
    def get_data(self, type='input'):
        if type == 'input':
            return self.input_data
        elif type == 'train':
            return self.train_input_data
        elif type == 'test':
            return self.test_input_data
        else:
            logger.warning("Invalid data type requested.")
            return None
        
    def get_data_type(self):
        return self.data_type
    
    def is_multivar(self):
        return self.multivar
    
    def get_run_setting(self, name):
        """The value a run would use: from the GUI if it was changed there, else the saved one."""
        path = param_paths[name]
        return self.params[path] if path in self.params else self.get_current_variable(name)

    def validate_run_settings(self):
        """Returns what stops a run from starting, or None."""
        if self.input_data is None:
            return f"The input file could not be read: {self.get_input_path()}"
        if not (self.get_run_setting("terminal_set") or "").split():
            return "The terminal set is empty. Select at least one variable or add a constant."
        functions = (self.get_run_setting("function_set") or "").split()
        if not functions:
            return "The function set is empty. Select at least one function."
        if self.get_run_setting("linear_scaling") == "true" and not {"+", "*"} <= set(functions):
            return "Linear scaling needs Addition and Multiplication. Select both, or turn linear scaling off."
        return None

    def prepare_run(self):
        self.thread_num = max(1, min(self.thread_num, multiprocessing.cpu_count()))
        self.run_has_test_set = self.train_test_split < 1
        # The input panel stays editable during a run, and evaluations must match the run
        self.run_params = dict(self.params)
        self.run_error_path = self.get_error_path()
        self.data_type = 'train'
        self.function_solutions = {}
        self.best_functions = None
        self.config_manager.configurations = {}
        self.config_manager.test_configurations = {}
        self.process_states = {}
        self.register_all_processes()

    def get_function_solutions(self, function, data_type):
        if function in self.function_solutions:
            if data_type in self.function_solutions[function]:
                return self.function_solutions[function][data_type]
        return None
    
    def update_function_solutions(self, function, solutions, data_type):
        if data_type != 'train' and data_type != 'test':
            logger.warning("Invalid data type. Cannot update function_solutions. Must be 'train' or 'test'")
            return
        
        if function not in self.function_solutions:
            self.function_solutions[function] = {}

        self.function_solutions[function][data_type] = solutions

    def update_best_functions(self):
        return self.update_aggregate_best_functions(self.data_type == 'test').copy()

    def get_best_functions(self, id=None, data_type=None, copy=True):
        if data_type is None:
            data_type = self.data_type if self.data_type is not None else 'train'
        if id is None:
            if self.best_functions is not None:
                return self.best_functions.copy() if copy else self.best_functions
            else:
                return None
        else:
            functions_key = 'best_test_functions' if data_type == 'test' else 'best_functions'

            return self.process_states[id][functions_key].copy() if copy else self.process_states[id][functions_key]
        
    def add_individuals(self, id, individuals):
        """Merges new Individuals into the Pareto fronts of a Process."""
        state = self.process_states[id]
        state['best_functions'] = self.filter_best_functions(state['best_functions'] + individuals)
        tested = [individual for individual in individuals if 'test_error' in individual]
        state['best_test_functions'] = self.filter_best_functions(state['best_test_functions'] + tested, 'test')

    def get_test_configurations(self, id):
        return self.config_manager.test_configurations[id]
    
    def get_evaluation_configurations(self, id):
        if id not in self.config_manager.eval_configurations:
            logger.warning(f"Configuration with id {id} not found")
        return self.config_manager.eval_configurations[id]
        
    def update_aggregate_best_functions(self, is_test=False):
        all_best_functions = []
        best_functions_key = 'best_test_functions' if is_test else 'best_functions'
        for value in list(self.process_states.values()):
            all_best_functions.extend(value[best_functions_key])

        best_functions = self.filter_best_functions(all_best_functions, 'test' if is_test else 'train')
        if is_test:
            best_functions = self.show_test_errors(best_functions)
        self.best_functions = best_functions

        return self.best_functions

    def show_test_errors(self, best_functions):
        return [{**func, 'error': func['test_error']} for func in best_functions]

    def enable_function(self, function):
        self.enabled_functions.add(function)
        self.set_function_set(set_to_string(self.enabled_functions))

    def disable_function(self, function):
        if function in self.enabled_functions:
            self.enabled_functions.remove(function)
        self.set_function_set(set_to_string(self.enabled_functions))

    def get_enabled_functions(self):
        return list(self.enabled_functions)
    
    def reset_file_reading(self, id):
        """Called before a Process starts SRM. SRM can finish right after writing its best
        Individual, so what is left in the file is read first. The file then goes, so that no
        read can pick up the previous run's file while SRM is still starting."""
        state = self.process_states[id]
        best_file_path = self.config_manager.configurations[id].best_file_path
        with state['lock']:
            state['unread_individuals'] += self.read_best_file(id)
            delete_file_if_exists(best_file_path)
            state['current_file_size'] = 0
            state['unparsed_text'] = ''

    def register_all_processes(self):
        for id in range(self.thread_num):
            self.register_process(id)

    def register_process(self, id):
        self.process_states[id] = {
            'best_functions': [],
            'best_test_functions': [],
            'functions_seen': set(),
            'current_file_size': 0,
            'unparsed_text': '',
            'unread_individuals': [],
            'lock': threading.Lock(),
        }

    def load_input_data(self):
        input_path = self.get_input_path()
        self.input_data = self.load_data(input_path)
        if self.input_data is None:
            logger.error(f"Error loading data: input path '{input_path}' invalid or unreadable")
            return None
        self.multivar = len(self.input_data) > 2
        return self.input_data.copy()

    def load_data(self, file_path):
        try:
            input_data = np.loadtxt(file_path, delimiter='\t', ndmin=2)
            converted_input_data = self.convert_to_2d_array(input_data)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None

        return converted_input_data

    def convert_to_2d_array(self, data):
        converted_data = data.tolist()
        # Switch rows and columns (transpose)
        return np.transpose(converted_data).tolist()

    def read_new_individuals(self, id):
        """Returns the Individuals a Process wrote since the last call, each one once."""
        state = self.process_states[id]

        with state['lock']:
            individuals = state['unread_individuals'] + self.read_best_file(id)
            state['unread_individuals'] = []

        new_individuals = []
        for individual in individuals:
            if individual['function'] not in state['functions_seen']:
                state['functions_seen'].add(individual['function'])
                new_individuals.append(individual)
        return new_individuals

    def read_best_file(self, id):
        """Moves the reading position to the end of the best file. Holds the state's lock."""
        state = self.process_states[id]
        best_file_path = self.config_manager.configurations[id].best_file_path
        new_text, state['current_file_size'] = self.read_new_data(best_file_path, state['current_file_size'])
        if new_text is None:
            return []
        individuals, state['unparsed_text'] = parse_best_text(state['unparsed_text'] + new_text)
        return individuals

    def has_best_output(self, id):
        best_file_path = self.config_manager.configurations[id].best_file_path
        return os.path.exists(best_file_path) and os.path.getsize(best_file_path) > 0

    def read_new_data(self, file_path, current_file_size):
        if not os.path.exists(file_path):
            return None, 0

        new_file_size = os.path.getsize(file_path)
        if new_file_size <= current_file_size:
            return None, new_file_size

        # Binary, because the size is in bytes and Windows line ends are two of them
        with open(file_path, 'rb') as file:
            file.seek(current_file_size)
            new_data = file.read(new_file_size - current_file_size)

        return new_data.decode('utf-8', errors='replace'), new_file_size

    def filter_best_functions(self, data, data_type='train'):
        error_name = 'test_error' if data_type == 'test' else 'error'

        # Sort the data by size first, then by error in ascending order
        finite_data = [function for function in data if math.isfinite(function[error_name])]
        sorted_data = sorted(finite_data, key=lambda x: (x['size'], x[error_name]))

        # Prepare the filtered list of best functions
        filtered_functions = []
        last_valid_error = float('inf')  # Set a high initial error to compare against

        for function in sorted_data:
            if function[error_name] < last_valid_error:
                filtered_functions.append(function)
                last_valid_error = function[error_name]  # Update the last valid error to the current one

        return filtered_functions

    def get_plot_data(self, type='input'):
        data = None

        if type == 'input':
            data = self.input_data
        elif type == 'train':
            data = self.train_input_data
        elif type == 'test':
            data = self.test_input_data

        if data is None:
            logger.warning("No data to plot")
            return None, None
        
        x_index = self.plot_x_index if self.plot_x_index is not None else -1

        # Another input file can have been chosen since this data was split
        if x_index == -1 or x_index >= len(data) - 1:
            x_data = list(range(len(data[0])))
        else:
            x_data = data[x_index]

        y_data = data[-1]

        return x_data, y_data
    
    def split_train_test(self):
        self.train_input_data = None
        self.test_input_data = None
        self.config_manager.split_train_test(
            self.get_input_path(),
            train_output_path=self.train_file_path,
            test_output_path=self.test_file_path,
            train_test_split_ratio=self.train_test_split,
            test_sample_choice=self.test_sample,
            error_weights_path=self.get_error_path(),
            train_weights_path=self.train_weights_path,
            test_weights_path=self.test_weights_path,
        )
        self.train_input_data = self.load_data(self.train_file_path)
        if self.train_test_split < 1:
            self.test_input_data = self.load_data(self.test_file_path)

    def update_default_parameters_file(self):
        self.config_manager.update_config(self.params)
        self.config_manager.set_tree_and_root()

    def process_directory(self, process_id):
        return os.path.join(paths.temp_dir(), str(process_id))

    def create_process_config(self, process_id, is_test=False, delete_logs=False):
        base_process_path = self.process_directory(process_id)
        create_directory(base_process_path)
        suffix = "_test" if is_test else ""
        parameters_path = os.path.join(base_process_path, f'parameters{suffix}.txt')
        best_file_path = os.path.join(base_process_path, f'best{suffix}.txt')
        log_file_path = os.path.join(base_process_path, f'log{suffix}.txt')
        input_file_path = self.test_file_path if is_test else self.train_file_path
        error_weights_path = None
        if self.run_error_path:
            error_weights_path = self.test_weights_path if is_test else self.train_weights_path
        self.config_manager.create_config(
            process_id=process_id, parameters_path=parameters_path, input_file_path=input_file_path, best_file_path=best_file_path, log_file_path=log_file_path, is_test=is_test or process_id=='eval', params=self.run_params, error_weights_path=error_weights_path
        )
        if delete_logs:
            delete_file_if_exists(best_file_path)
            delete_file_if_exists(log_file_path)

        return parameters_path

    def create_individual_file(self, file_path, error, size, prefix_function):
        return self.config_manager.create_individual_file(file_path, error, size, prefix_function)

    def read_evaluation(self, best_file_path, output_path):
        return self.config_manager.read_evaluation(best_file_path, output_path)
