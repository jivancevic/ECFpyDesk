import subprocess
import os
import json
import numpy as np
import xml.etree.ElementTree as ET
import itertools
from tkinter import filedialog
from utils.plot import safe_dict


class Controller:
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
        if plot_x_axis_var == "Row number":
            self.model.plot_x_index = -1
        else:
            x_index = int(plot_x_axis_var[1])-1

        self.model.plot_x_index = x_index

    def update_solutions(self):
        self.view.results_frame.update_solutions_frame()

    def get_input_data(self):
        return self.model.input_data

    def get_plot_data(self, x_index=None):
        if x_index is None:
            x_index = self.model.plot_x_index

        data = self.get_input_data()

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

    def run_ECF(self):
        # Run the executable
        #subprocess.call([self.config["SRM_path"], self.config["SRM_parameters_path"]])
        subprocess.call([self.config["SRM_path"], "srm/srm.txt"])

        # Change back to the current directory
        os.chdir(self.app_directory)

    def parse_best_file(self, file_path):
        data = []
        with open(file_path, 'r') as file:
            generation_data = {}
            lines = []
            for line in file:
                line = line.strip()
                if line.isdigit():  # New generation
                    if generation_data:
                        data.append(generation_data.copy())
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
        if generation_data:
            data.append(generation_data)
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

    def on_run_button_click(self):
        self.view.show_results()
        tree, root = self.parse_XML(self.config["SRM_parameters_path"])
        input_path = self.view.input_frame.input_file_path
        error_path = self.view.input_frame.error_file_path if self.view.input_frame.error_file_path else None
        functions = [func for func, checkbox in self.view.input_frame.checkbox_vars.items() if checkbox.get()]
        
        self.update_config(root, input_path, error_path, functions)
        self.write_config(tree, self.config["SRM_parameters_path"])
        self.run_ECF()

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

    def start(self):
        self.view.start()