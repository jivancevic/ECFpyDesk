import numpy as np
import os
import json
from .config import ConfigurationManager
from .parameters import param_paths
from utils.helper import set_to_string, string_to_set
from utils.file import create_directory
from utils.publisher import Publisher

class Model(Publisher):
    config_path = 'config.json'

    def __init__(self):
        super().__init__()
        with open(self.config_path, 'r') as file:
            self.config = json.load(file)

        self.config_manager = ConfigurationManager()

        self.configs = {}
        self.process_states = {}

        # Input parameters
        self.params = {}
        self.train_test_split = 1
        self.test_sample = None
        self.plot_x_index = None
        self.plot_y_index = None
        self.plot_scale = None
        self.best_file = self.config["best_file_path"]
        self.thread_num = 1

        self.train_file_path = 'srm/temp/train.txt'
        self.test_file_path = 'srm/temp/test.txt'
        self.input_data = None
        self.train_input_data = None
        self.test_input_data = None
        self.data_type = 'input'
        self.function_solutions = {}
        self.multivar = False
        self.enabled_functions = set()
        self.best_functions = None

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
        return self.params[param_paths["input_path"]]
    
    def get_current_input_path(self):
        return self.config_manager.get_current_param_value(param_paths["input_path"])
    
    def get_current_variable(self, name):
        return self.config_manager.get_current_param_value(param_paths[name])

    def set_error_path(self, path):
        self.params[param_paths["error_path"]] = path

    def get_error_path(self):
        return self.params[param_paths["error_path"]]
    
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
            print("Invalid data type requested.")
            return None
        
    def get_data_type(self):
        return self.data_type
    
    def is_multivar(self):
        return self.multivar
    
    def is_test(self):
        return self.train_test_split < 1
    
    def get_function_solutions(self, function, data_type):
        if function in self.function_solutions:
            if data_type in self.function_solutions[function]:
                return self.function_solutions[function][data_type]
        return None
    
    def update_function_solutions(self, function, solutions, data_type):
        if data_type != 'train' and data_type != 'test':
            print("Invalid data type. Cannot update function_solutions. Must be 'train' or 'test'")
            return
        
        if function not in self.function_solutions:
            self.function_solutions[function] = {}

        self.function_solutions[function][data_type] = solutions

    def update_best_functions(self, copy=True):
        return self.update_aggregate_best_functions().copy() if copy else self.update_aggregate_best_functions()
        
    def get_best_functions(self, id=None, copy=True):
        if id is None:
            if self.best_functions is not None:
                return self.best_functions.copy() if copy else self.best_functions
            else:
                return None
        else:
            return self.process_states[id]['best_functions'].copy() if copy else self.process_states[id]['best_functions']
        
    def set_best_functions(self, id, best_functions):
        self.process_states[id]['best_functions'] = best_functions

    def get_test_configurations(self, id):
        return self.config_manager.test_configurations[id]
    
    def get_evaluation_configurations(self, id):
        if id not in self.config_manager.eval_configurations:
            print(f"Configuration with id {id} not found")
        return self.config_manager.eval_configurations[id]
        
    def update_aggregate_best_functions(self):
        all_best_functions = []
        for id, value in self.process_states.items():

            #print(f"\n\nvalue['best_functions'] for process {id}: {value['best_functions']}")

            all_best_functions.extend(value['best_functions'])
        
        self.best_functions = self.filter_best_functions(all_best_functions)
        #print(f"\nFiltered best_functions: {self.best_functions}\n")

        return self.best_functions

    def enable_function(self, function):
        self.enabled_functions.add(function)
        self.set_function_set(set_to_string(self.enabled_functions))

    def disable_function(self, function):
        if function in self.enabled_functions:
            self.enabled_functions.remove(function)
        self.set_function_set(set_to_string(self.enabled_functions))

    def get_enabled_functions(self):
        return list(self.enabled_functions)
    
    def delete_best_functions(self):
        self.functions_seen = set()
        self.best_functions = []
        self.current_file_size = 0

    def reset_file_reading(self, id):
        self.process_states[id]['current_file_size'] = 0

    def register_all_processes(self):
        for id in range(self.thread_num):
            self.register_process(id)

    def register_process(self, id):
        self.process_states[id] = {
            'best_functions': [],
            'functions_seen': set(),
            'current_file_size': 0,
        }

    def load_input_data(self):
        self.input_data = self.load_data(self.get_input_path())
        self.multivar = len(self.input_data) > 2
        return self.input_data.copy()

    def load_data(self, file_path):
        try:
            input_data = np.loadtxt(file_path, delimiter='\t')
            converted_input_data = self.convert_to_2d_array(input_data)
        except Exception as e:
            print(f"Error loading data: {e}")
            return None

        return converted_input_data

    def convert_to_2d_array(self, data):
        converted_data = data.tolist()
        # Switch rows and columns (transpose)
        return np.transpose(converted_data).tolist()

    def parse_best_functions(self, id):
        best_file_path = self.config_manager.configurations[id].best_file_path
        best_functions = self.parse_best_file(id, best_file_path)
        return best_functions
    
    def parse_best_file(self, id, file_path):
        state = self.process_states[id]

        generation_data = {}
        lines = []
        new_data, state['current_file_size'] = self.read_new_data(file_path, state['current_file_size'])
        if id == 0:
            print(f"Current file size: {state['current_file_size']}")

        if new_data is None:
            return state['best_functions'].copy()

        def process_generation_data():
            # Only append if not seen and data is valid
            if generation_data and 'prefix_function' in generation_data and generation_data['function'] not in state['functions_seen']:
                state['best_functions'].append(generation_data.copy())
                state['functions_seen'].add(generation_data['function'])  # Add to seen to prevent reprocessing

        for line in new_data:
            line = line.strip()
            if line.isdigit():  # New generation
                process_generation_data()
                generation_data = {'generation': int(line)}  # reset with new generation
            elif line:
                lines.append(line)
                if len(lines) == 5:
                    self.process_line_block(lines, generation_data)
                    lines = []

        process_generation_data()  # Check after the last line has been processed

        return state['best_functions'].copy()
    
    def has_new_data(self, id):
        file_path = self.config_manager.configurations[id].best_file_path
        state = self.process_states[id]
        old_file_size = state['current_file_size']

        new_data, current_file_size = self.read_new_data(file_path, old_file_size)

        return old_file_size != current_file_size

    def read_new_data(self, file_path, current_file_size):
        # Get the current size of the file
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist")
            return None, 0
        
        new_file_size = os.path.getsize(file_path)
        new_data = None

        # Read new data if the file size has increased
        if new_file_size > current_file_size:
            with open(file_path, 'r') as file:
                # Seek to the last read position
                file.seek(current_file_size)

                # Read new data
                new_data = file.read(new_file_size - current_file_size).split("\n")

            # Update the last read size
            current_file_size = new_file_size

        return new_data, current_file_size

    def process_line_block(self, lines, generation_data):
        # Parsing lines for required information
        function_line, _, fitness_line, tree_line, _ = lines
        generation_data.update({
            'function': function_line,
            'error': float(fitness_line.split('"')[1]),
            'size': int(tree_line.split('"')[1]),
            'prefix_function': tree_line.split(">")[1].split("<")[0]
        })

    def filter_best_functions(self, data):
        if len(data) == 0:
            return data
        # Sort the data by size first, then by error in ascending order
        sorted_data = sorted(data, key=lambda x: (x['size'], x['error']))

        # Prepare the filtered list of best functions
        filtered_functions = []
        last_valid_error = float('inf')  # Set a high initial error to compare against

        for function in sorted_data:
            if function['error'] < last_valid_error:
                filtered_functions.append(function)
                last_valid_error = function['error']  # Update the last valid error to the current one

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
            print("No data to plot")
            return None, None
        
        x_index = self.plot_x_index if self.plot_x_index is not None else -1

        if x_index == -1:
            x_data = list(range(len(data[0])))
        else:
            x_data = data[x_index]

        y_data = data[-1]

        return x_data, y_data
    
    def split_train_test(self):
        self.config_manager.split_train_test(self.get_input_path(), train_output_path=self.train_file_path, test_output_path=self.test_file_path, train_test_split_ratio=self.train_test_split, test_sample_choice=self.test_sample)
        self.train_input_data = self.load_data(self.train_file_path)
        self.test_input_data = self.load_data(self.test_file_path)
        print(f"Train file path: {self.train_file_path}, Test file path: {self.test_file_path}")

    def update_default_parameters_file(self):
        self.config_manager.update_config(self.params)

    def get_parameters_paths(self):
        return [self.config_manager.configurations[id]['parameters_path'] for id in range(self.thread_num)]
    
    def create_process_config(self, process_id, is_test=False):
        base_process_path = f'srm/temp/{process_id}'
        create_directory(base_process_path)
        parameters_path = f'{base_process_path}/parameters{"_test" if is_test else ""}.txt'
        input_file_path = self.test_file_path if is_test else self.train_file_path
        best_file_path = f'{base_process_path}/best{"_test" if is_test else ""}.txt'
        log_file_path = f'{base_process_path}/log{"_test" if is_test else ""}.txt'
        self.config_manager.create_config(
            process_id=process_id, parameters_path=parameters_path, input_file_path=input_file_path, best_file_path=best_file_path, log_file_path=log_file_path, is_test=is_test or process_id=='eval'
        )

        return parameters_path

    def create_individual_file(self, file_path, error, size, prefix_function):
        return self.config_manager.create_individual_file(file_path, error, size, prefix_function)

    def parse_best_individual_file(self, file_path):
        return self.config_manager.parse_best_individual_file(file_path)