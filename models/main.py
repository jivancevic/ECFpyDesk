import numpy as np
import os
import json
from .config import ConfigurationManager
from .parameters import param_paths
from utils.helper import set_to_string, string_to_set
from utils.publisher import Publisher

class Model(Publisher):
    config_path = 'config.json'

    def __init__(self):
        super().__init__()
        with open(self.config_path, 'r') as file:
            self.config = json.load(file)

        self.config_manager = ConfigurationManager(self.config['SRM_parameters_path'])
        self.process_manager = None

        # Input parameters
        self.params = {}
        self.train_test_split = 1
        self.test_sample = None
        self.plot_x_index = None
        self.plot_y_index = None
        self.plot_scale = None
        self.best_file = self.config["best_file_path"]
        self.thread_num = 1

        self.train_file_path = None
        self.test_file_path = None
        self.input_data = None
        self.multivar = False
        self.enabled_functions = set()
        self.best_functions = []
        self.functions_seen = set()
        self.current_file_size = 0

    def set_process_manager(self, process_manager):
        self.process_manager = process_manager

    def set_variable(self, name, value):
        if name in param_paths:
            self.params[param_paths[name]] = value
        else:
            setattr(self, name, value)

    def set_input_path(self, path):
        self.params[param_paths["input_path"]] = path
    
    def get_input_path(self):
        return self.params[param_paths["input_path"]]
    
    def get_current_input_path(self):
        return self.config_manager.get_current_param_value(param_paths["input_path"])

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
    
    def is_multivar(self):
        return self.multivar

    def set_best_functions(self, best_functions):
        self.best_functions = best_functions

    def get_best_functions(self, copy=True):
        return self.best_functions.copy() if copy else self.best_functions

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

    def reset_file_reading(self):
        self.current_file_size = 0
    
    def load_input_data(self):
        try:
            input_data = np.loadtxt(self.get_input_path(), delimiter='\t')
            self.input_data = self.convert_to_2d_array(input_data)
            self.multivar = len(self.input_data) > 2

        except Exception as e:
            print(f"Error loading data: {e}")
            self.input_data = None

        return self.input_data.copy(), self.multivar

    def convert_to_2d_array(self, data):
        converted_data = data.tolist()
        # Switch rows and columns (transpose)
        return np.transpose(converted_data).tolist()
    
    def update_best_functions(self):
        best_functions = self.parse_best_file(self.best_file)
        pareto_functions = self.filter_best_functions(best_functions)
        self.best_functions = pareto_functions  # Update the model's state with new data
    
    def parse_best_file(self, file_path):
        generation_data = {}
        lines = []
        new_data, self.current_file_size = self.read_new_data(file_path, self.current_file_size)

        if new_data is None:
            return self.best_functions.copy()  # Return a copy of the list

        def process_generation_data():
            # Only append if not seen and data is valid
            if generation_data and 'prefix_function' in generation_data and generation_data['function'] not in self.functions_seen:
                if self.train_test_split != 1:
                    print(f"Processing generation {generation_data['generation']}")
                    best_individual_file_path = 'srm/temp/best_test.txt'
                    test_parameters_file_path = self.config_manager.create_test_parameters_file(self.config['SRM_parameters_path'], self.test_file_path, best_individual_file_path)
                    print(f"Test parameters file path: {test_parameters_file_path}")
                    individual_file_path = 'srm/temp/individual.txt'
                    self.create_individual_file(individual_file_path, generation_data)
                    print(f"Individual file path: {individual_file_path}")
                    self.process_manager.run_test_process(parameters_path=test_parameters_file_path, individual_path=individual_file_path)
                    error, solutions = self.parse_best_individual_file(best_individual_file_path)
                    print(f"Size: {generation_data['size']}, Error: {error}, Function: {generation_data['function'][:20]}, Solutions: {solutions[:3]}")
                    generation_data['error'] = error
                self.best_functions.append(generation_data.copy())
                self.functions_seen.add(generation_data['function'])  # Mark this function as seen

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

        return self.best_functions.copy()

    def read_new_data(self, file_path, current_file_size):
        # Get the current size of the file
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
    
    def parse_best_individual_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines() 
            error = float(lines[3].split('"')[1])
            solutions = []
            for i in range(7, len(lines)):
                if lines[i].strip() != "":
                    solutions.append(float(lines[i].strip())) 

        return error, solutions

    def get_plot_data(self):
        if self.input_data is None:
            return None, None
        
        x_index = self.plot_x_index if self.plot_x_index is not None else -1

        # Assuming self.input_data is structured appropriately
        if x_index == -1:
            x_data = list(range(len(self.input_data[0])))
        else:
            x_data = self.input_data[x_index]

        y_data = self.input_data[-1]  # Assuming the last list in self.input_data is y data

        return x_data, y_data
    
    def split_train_test(self):
        self.train_file_path, self.test_file_path = self.config_manager.split_train_test(self.get_input_path(), self.train_test_split, self.test_sample)
        print(f"Train file path: {self.train_file_path}, Test file path: {self.test_file_path}")

    def update_configuration(self):
        self.config_manager.update_config(self.params)

    def create_individual_file(self, file_path, generation_data):
        file_string = ""
        file_string += '<Individual size="1">\n'
        file_string += f'\t<FitnessMin value="{generation_data["error"]}"/>\n'
        file_string += f'\t<Tree size="{generation_data["size"]}">{generation_data["prefix_function"]} </Tree>\n'
        file_string += '</Individual>'

        with open(file_path, 'w') as file:
            file.write(file_string)
