import subprocess
import os
import json
import numpy as np
import xml.etree.ElementTree as ET
import itertools
from tkinter import filedialog, PhotoImage
from utils.plot import safe_dict
import threading


class Controller:
    process = None
    running = False

    def __init__(self, model, view, app_directory):
        with open('config.json', 'r') as file:
            self.config = json.load(file)

        self.model = model
        self.view = view
        self.view.set_controller(self)
        self.setup_callbacks()
        self.app_directory = app_directory

    def get_config(self):
        return self.config

    def setup_callbacks(self):
       # Setup button commands
        self.view.navigation_frame.input_button.configure(command=self.show_input)
        self.view.navigation_frame.results_button.configure(command=self.show_results)

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

    def set_plot_x_index(self, plot_x_axis_var):
        print("plot_x_axis_var:", plot_x_axis_var)
        if plot_x_axis_var == "Row number":
            self.model.plot_x_index = -1
        else:
            self.model.plot_x_index = int(plot_x_axis_var[1])-1

    def update_solutions(self):
        self.view.results_frame.update_solutions_frame()

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
        ecf_tag = tree.find(".//ECF")
        print("tree:", tree)
        print("ecf_tag:", ecf_tag)
        return tree, ecf_tag
    
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
        #self.process = subprocess.Popen([self.config["SRM_path"], self.config["SRM_parameters_path"]])
        self.process = subprocess.Popen([self.config["SRM_path"], "srm/srm.txt"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        while True:
            output = self.process.stdout.readline()
            if output == '' and self.process.poll() is not None:
                break
            if output:
                update_output(output)
        self.process.poll()

        self.running = False
        self.view.navigation_frame.set_toggle_icon("start")
        os.chdir(self.app_directory)  # Change back to the initial directory
        self.process = None

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
            # Start the process in a new thread
            self.process_thread = threading.Thread(target=self.run_ECF, args=(self.view.results_frame.append_output,))
            self.process_thread.start()

    def pause_process(self):
        if self.running and self.process:
            self.process.send_signal(subprocess.signal.SIGSTOP)  # Send pause signal
            self.running = False
            self.view.navigation_frame.set_toggle_icon("start")

    def continue_process(self):
        if not self.running and self.process:
            self.process.send_signal(subprocess.signal.SIGCONT)  # Send continue signal
            self.running = True
            self.view.navigation_frame.set_toggle_icon("pause")

    def parse_best_file(self, file_path):
        data = []
        functions_seen = set()  # This set will store the functions we've seen so far
        with open(file_path, 'r') as file:
            generation_data = {}
            lines = []
            for line in file:
                line = line.strip()
                if line.isdigit():  # New generation
                    if generation_data and generation_data['function'] not in functions_seen:
                        data.append(generation_data.copy())
                        functions_seen.add(generation_data['function'])  # Mark this function as seen
                    generation_data.clear()
                    generation_data['generation'] = int(line)
                elif line != "":
                    lines.append(line)
                    if len(lines) == 5:
                        function_line = lines[0]
                        fitness_line = lines[2]
                        tree_line = lines[3]

                        function = function_line
                        fitness_min = float(fitness_line.split('"')[1])
                        tree_size = int(tree_line.split('"')[1])
                        infix_function = tree_line.split(">")[1].split("<")[0]

                        generation_data['function'] = function
                        generation_data['error'] = fitness_min
                        generation_data['size'] = tree_size
                        generation_data['infix_function'] = infix_function
                        lines = []
            # Check once more after the last line has been read
            if generation_data and generation_data['function'] not in functions_seen:
                data.append(generation_data)
                functions_seen.add(generation_data['function'])  # Mark this function as seen
        return data
    
    def get_best_functions(self):
        return self.model.best_functions

    def update_config(self, root, input_path, error_path, functions):
        genotype = root.find(".//Genotype")
        registry = root.find(".//Registry")
        # Update input_file
        root.find(".//Entry[@key='input_file']").text = input_path

        # Update or add error_weights.file
        error_entry = root.find(".//Entry[@key='error_weights.file']")
        if error_entry is not None:
            error_entry.text = error_path
        elif error_path is not None:
            ET.SubElement(registry, 'Entry', key='error_weights.file').text = error_path

        # Update functionset
        functions_str = " ".join(functions)
        genotype.find(".//Entry[@key='functionset']").text = functions_str

    def on_toggle_process_click(self):
        self.on_run_button_click()

    def on_run_button_click(self):
        self.view.show_results()
        tree, root = self.parse_XML(self.config["SRM_parameters_path"])
        input_path = self.view.input_frame.input_file_path
        error_path = self.view.input_frame.error_file_path if self.view.input_frame.error_file_path else None
        functions = [func for func, checkbox in self.view.input_frame.checkbox_vars.items() if checkbox.get()]
        
        self.update_config(root, input_path, error_path, functions)
        self.write_config(tree, self.config["SRM_parameters_path"])
        self.toggle_process()

        self.set_plot_x_index(self.view.input_frame.plot_x_axis_var)

        data_best = self.parse_best_file("srm/best.txt")
        self.model.set_best_functions(data_best)

        self.update_solutions()
        self.model.load_input_data(input_path)  # Load data
        self.update_plot(0)

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
            variable_dict = {f'x{i+1}': np.array(data[i]) for i in range(len(data))}
            # Add these to the safe dict for evaluation
            safe_dict.update(variable_dict)
            try:
                # Evaluate the function string safely
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