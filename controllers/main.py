import subprocess
import os
import json
import shutil
import numpy as np
import xml.etree.ElementTree as ET
import itertools
from tkinter import filedialog, PhotoImage
from utils.plot import safe_dict
import threading
import pandas as pd
from sklearn.model_selection import train_test_split

class Controller:
    process = None
    running = False
    current_file_size = 0
    parameters_file_path = 'srm/parameters.txt'
    tree = None
    root = None
    REFRESH_RATE = 0.5

    def __init__(self, model, view, app_directory):
        with open('config.json', 'r') as file:
            self.config = json.load(file)

        self.model = model
        self.view = view
        self.view.set_controller(self)
        self.setup_callbacks()
        self.app_directory = app_directory
        self.best_functions_lock = threading.Lock()

    def get_config(self):
        return self.config
    
    def get_parameters_file_path(self):
        return self.parameters_file_path

    def setup_callbacks(self):
       # Setup button commands
        self.view.navigation_frame.input_button.configure(command=self.show_input)
        self.view.navigation_frame.results_button.configure(command=self.show_results)

    def register_callback(self, event_name, callback):
        if event_name in self.callbacks:
            self.callbacks[event_name] = callback

    def update_input_path(self, path):
        self.model.input_path = path
        print(f"Updated input path: {path}")

    def update_error_path(self, path):
        self.model.error_path = path
        print(f"Updated error path: {path}")

    def show_input(self):
        self.view.show_input()

    def show_results(self):
        self.view.show_results()

    def update_plot(self, x_index=None):
        x_data, y_data = self.get_plot_data(x_index)
        self.view.results_frame.update_plot(x_data, y_data)

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

    def update_solutions(self):
        with self.best_functions_lock:
            best_functions = self.model.parse_best_file(self.config["best_file_path"])
            pareto_functions = self.filter_best_functions(best_functions)
            self.model.set_best_functions(pareto_functions.copy())
            self.update_solutions_frame(pareto_functions.copy())

        # Restart the timer for the next update
        if self.running:
            self.start_update_timer()

    def update_solutions_frame(self, best_functions):
        self.view.results_frame.update_solutions_frame(best_functions)

    def get_input_data(self):
        return self.model.input_data

    def get_plot_data(self, x_index=None):
        if x_index is None:
            x_index = self.model.plot_x_index

        data = self.get_input_data()

        if x_index == -1:
            x_data = [i for i in range(0, len(data[0]))]
        else:
            x_data = data[x_index]
        y_data = data[len(data)-1]

        return x_data, y_data
    
    def parse_XML(self, file_path):
        with open(file_path) as f:
            it = itertools.chain('<root>', f.read(), '</root>')
            tree = ET.ElementTree(ET.fromstringlist(it))
    
        fake_root = tree.getroot()
        ecf_tag = tree.find(".//ECF")
        return tree, fake_root, ecf_tag
    
    def remove_root_tag(self, file_path):
        f = open(file_path,'r')
        a = ['<root>','</root>']
        lst = []
        for line in f:
            for word in a:
                if word in line:
                    line = line.replace(word,'')
            lst.append(line)
        f.close()
        f = open(file_path,'w')
        for line in lst:
            f.write(line)
        f.close()
    
    def write_config(self, tree, file_path):
        tree.write(file_path)
        self.remove_root_tag(file_path)

    def run_ECF(self, update_output):
        # Run the executable with subprocess
        self.process = subprocess.Popen([self.config["SRM_path"], self.config["SRM_parameters_path"]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        while True:
            output = self.process.stdout.readline()
            if output == '' and self.process.poll() is not None:
                break
            if output:
                update_output(output)
        self.process.poll()

        self.running = False
        print("self.running:", self.running)
        self.view.navigation_frame.set_toggle_icon("start")
        self.update_solutions()
        os.chdir(self.app_directory)  # Change back to the initial directory
        self.process = None

    def start_update_timer(self):
        """Starts a timer that updates the solutions frame every second."""
        self.update_timer = threading.Timer(self.REFRESH_RATE, self.update_solutions)
        self.update_timer.start()

    def toggle_process(self):
        if self.running:
            self.pause_process()
        elif self.process:
            self.continue_process()
        else:
            self.start_process()

    def start_process(self):
        if not self.running:
            self.running = True
            self.view.navigation_frame.set_toggle_icon("pause")
            self.view.results_frame.clear_frame()
            self.model.delete_best_function()
            # Start the process in a new thread
            self.process_thread = threading.Thread(target=self.run_ECF, args=(self.view.results_frame.append_output,))
            self.process_thread.start()
            self.start_update_timer()  # Start updating the solutions frame

    def pause_process(self):
        if self.running and self.process:
            self.process.send_signal(subprocess.signal.SIGSTOP)  # Send pause signal
            self.running = False
            self.view.navigation_frame.set_toggle_icon("start")
            if self.update_timer:
                self.update_timer.cancel()  # Stop the update timer

    def continue_process(self):
        if not self.running and self.process:
            self.process.send_signal(subprocess.signal.SIGCONT)  # Send continue signal
            self.running = True
            self.view.navigation_frame.set_toggle_icon("pause")
            self.start_update_timer()  # Start updating the solutions frame

    def stop_process(self):
        if self.process:
            try:
                # Attempt to terminate the process gracefully
                self.process.terminate()
                # Wait briefly for the process to terminate
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If the process does not terminate within the timeout, kill it
                print("Process did not terminate gracefully, killing it.")
                self.process.kill()
            except Exception as e:
                print(f"Error stopping the process: {e}")
            finally:
                # Ensure all internal flags and states are reset
                self.running = False
                self.process = None
                if self.process_thread and self.process_thread.is_alive():
                    # Optionally join the thread if it is still running
                    self.process_thread.join()
                self.process_thread = None

                if self.update_timer:
                    self.update_timer.cancel()  # Stop the update timer

                self.view.navigation_frame.set_toggle_icon("start")
                self.update_solutions()
                os.chdir(self.app_directory)  # Change back to the initial directory
    
    def get_best_functions(self):
        return self.model.best_functions
    
    def set_tree_and_root(self):
        self.tree, self.fake_root, self.root = self.parse_XML(self.config["SRM_parameters_path"])

    def update_tree(self, tree_string):
        tree = ET.ElementTree(ET.fromstringlist(tree_string))
        self.tree = ET.ElementTree(self.fake_root)
        self.fake_root = self.tree.getroot()
        self.root = self.tree.find(".//ECF")

    def update_config(self, input_path, error_path, terminal_set, search_metric, functions, other_params):
        if input_path is not None and input_path != "":
            self.set_param_element("ECF/Registry/Entry/input_file", input_path)
        
        if error_path is not None and error_path != "":
            self.set_param_element("ECF/Registry/Entry/error_weights.file", error_path)

        if terminal_set is not None and terminal_set.get() != "":
            self.set_param_element("ECF/Genotype/Entry/terminalset", terminal_set.get())

        if search_metric is not None and search_metric != "":
            self.set_param_element("ECF/Registry/Entry/error_metric", search_metric)

        # Update functionset
        functions_str = " ".join(functions)
        self.set_param_element("ECF/Genotype/Entry/functionset", functions_str)

        for path, value in other_params:
            value = value.get()
            self.set_param_element(path, value)

    def get_current_function_set(self):
        # Load the XML tree from a file or an existing in-memory object
        if self.tree is None or self.root is None:
            self.set_tree_and_root()

        function_set = self.root.find(f".//Entry[@key='functionset']")

        if function_set is not None:
            return function_set.text  # Return the text content of the element
        return None  # If the element with the key doesn't exist, return None
    
    def find_param_element(self, path):
        # Split the path by slashes to navigate through the nodes
        elements = path.split('/')
        current_element = self.root

        # Navigate through the tree to find the target element
        for element in elements[1:-2]:  # Ignore the last segment because it's the attribute key
            current_element = current_element.find(f".//{element}")
            if current_element is None:
                return None  # If the path is invalid at any point, return None

        # The last part of the path should be the key of the attribute you are looking for
        entry = elements[-2]
        key = elements[-1]
        target_element = current_element.find(f".//{entry}[@key='{key}']")  # Find the element with the specified key

        return target_element

    def add_param_element(self, path, value):
        # Complicated way of adding the element to the tree because of the parameters file not following the rules of the xml formatting

        tree_string = ET.tostring(self.fake_root, encoding='unicode')
        # Split the path and prepare the element and key to insert
        elements = path.split('/')
        entry = elements[-2]
        key = elements[-1]
        new_element = "\t" + f'<{entry} key="{key}">{value}</{entry}>' + '\n' + (len(elements)-3)*"\t" 

        # Construct the search path to find where to insert the new element
        nodes = elements[:-2]

        # Initialize a pointer to the root of the XML tree
        pointer = 0
        pointer_string = tree_string

        # Traverse the XML tree based on the given path
        for idx, node in enumerate(nodes):
            # Find the index of the opening tag of the current node
            start_tag_index = pointer_string.find(f'<{node}>')
            if start_tag_index == -1:
                print(f"Couldn't find tag <{node}> in the parameters file.")
                return False  # Node not found
            
            # Move the pointer to the end of the opening tag
            pointer += start_tag_index + len(node) + 2
            pointer_string = pointer_string[start_tag_index + len(node) + 2:]

            # Find the index of the closing tag of the current node
            end_tag_index = pointer_string.find(f'</{node}>')
            if end_tag_index == -1:
                print(f"Malformed XML: couldn't find closing tag for node <{node}> in the parameters file.")
                return False  # Malformed XML or node not closed
            
            if idx == len(nodes)-1:
                pointer += end_tag_index
            # Move the pointer to the end of the closing tag
            pointer_string = pointer_string[:end_tag_index]
        
        tree_string = tree_string[:pointer] + new_element + tree_string[pointer:]

        self.update_tree(tree_string)

        return True
    
    def set_param_element(self, path, value):
        target_element = self.find_param_element(path)
        if target_element is not None:
            target_element.text = value
        elif value is not None and value != "":
            self.add_param_element(path, value)

    def get_current_param_value(self, path):
        # Load the XML tree from a file or an existing in-memory object
        if self.tree is None or self.root is None:
            self.set_tree_and_root()

        target_element = self.find_param_element(path)

        if target_element is not None:
            return target_element.text  # Return the text content of the element
        return None  # If the element with the key doesn't exist, return None
    
    def get_terminal_set(self):
        return self.get_current_param_value("ECF/Genotype/Tree/Entry/terminalset")

    def on_toggle_process_click(self):
        self.on_run_button_click()

    def on_stop_process_click(self):
        stop_thread = threading.Thread(target=self.stop_process)
        stop_thread.start()

    def delete_file_if_exists(self, file_path):
        if os.path.exists(file_path):
            os.remove(file_path)

    def split_train_test(self, input_data_path, train_test_split_ratio, test_sample_choice):
        # Define output file paths
        train_output_path = input_data_path.replace('.txt', '_train.txt')
        test_output_path = input_data_path.replace('.txt', '_test.txt')

        self.delete_file_if_exists(train_output_path)
        self.delete_file_if_exists(test_output_path) 

        if (train_test_split_ratio == 1):
            try:
                shutil.copyfile(input_data_path, train_output_path)
            except FileNotFoundError:
                print(f"Source file '{input_data_path}' not found.")
            except Exception as e:
                print(f"Error occurred while copying file: {e}")
            return train_output_path, None

        # Load the data
        data = pd.read_csv(input_data_path, delimiter='\t')

        # Determine if the data should be shuffled
        shuffle = test_sample_choice == "random"

        # Split the data
        train_data, test_data = train_test_split(data, test_size=1-train_test_split_ratio, shuffle=shuffle)

        # Save the data to files
        train_data.to_csv(train_output_path, sep='\t', index=False)
        test_data.to_csv(test_output_path, sep='\t', index=False)

        return train_output_path, test_output_path
    
    def on_apply_button_click(self):
        configuration = self.prepare_configuration()
        self.apply_configuration(configuration)

    def on_run_button_click(self):
        self.prepare_for_results()
        self.start_simulation_process()
        self.post_process_setup()

    def prepare_for_results(self):
        """ Display results view and update any necessary UI components. """
        self.view.show_results()

    def prepare_configuration(self):
        """ Prepares and returns the configuration settings for the simulation. """
        self.set_tree_and_root()
        input_path = self.view.input_frame.input_file_path
        error_path = self.view.input_frame.error_file_path if self.view.input_frame.error_file_path else None
        terminal_set = self.view.input_frame.terminal_set
        search_metric = self.view.input_frame.search_metric
        functions = [func for func, checkbox in self.view.input_frame.checkbox_vars.items() if checkbox.get()]
        other_params = [(path, value) for path, value in self.view.input_frame.params_vars.items() if value != ""]

        train_output_path, test_output_path = self.split_train_test(
            input_path, 
            self.view.input_frame.train_test_split, 
            self.view.input_frame.test_sample
        )
        config = {
            'input_path': train_output_path,
            'error_path': error_path,
            'terminal_set': terminal_set,
            'search_metric': search_metric,
            'functions': functions,
            'other_params': other_params
        }
        return config

    def apply_configuration(self, config):
        print("Applying configurations...")
        """ Applies the prepared configuration to the system. """
        self.update_config(input_path=config['input_path'], error_path=config['error_path'], terminal_set=config['terminal_set'],
                           functions=config['functions'], search_metric=config['search_metric'], other_params=config['other_params'])
        self.write_config(self.tree, self.config["SRM_parameters_path"])

    def start_simulation_process(self):
        """ Starts the simulation process. """
        self.toggle_process()

    def post_process_setup(self):
        """ Load input data and update plot post process start. """
        input_path = self.view.input_frame.input_file_path
        self.model.plot_x_index = self.view.input_frame.plot_x_axis_var
        
        self.model.load_input_data(input_path)  # Load data
        self.update_plot()


    def evaluate_function(self, function_str, multivar=False, data=None):
        if data is None:
            data = self.model.get_input_data()
        
        x_values = None

        if not multivar:
            x_values = np.linspace(np.min(data[0]), np.max(data[0]), 400)
            safe_dict['x1'] = x_values
            # Evaluate the function string safely
            try:
                results = eval(function_str, {"__builtins__": None}, safe_dict)
            except Exception as e:
                print(f"Error evaluating univariate function: {e}")
                return None, None
        else:
            variable_dict = {f'x{i+1}': np.array(data[i]) for i in range(len(data)-1)}
            # Add these to the safe dict for evaluation
            safe_dict.update(variable_dict)
            try:
                # Evaluate the function string safely
                print(safe_dict)
                results = eval(function_str, {"__builtins__": None}, safe_dict)
                # Generate x_values as indices if multivariable function is plotted against an index range
                x_values = np.arange(len(results))
            except Exception as e:
                print(f"Error evaluating multivariable function: {e}")
                return None, None
            
        return x_values, results
    
    def is_multivar(self):
        return self.model.multivar

    def start(self):
        self.view.start()