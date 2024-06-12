import numpy as np
import os

class Model:
    def __init__(self):
        self.input_path = ""
        self.error_path = ""
        self.enabled_functions = set()
        self.input_data = None
        self.plot_x_index = None
        self.best_functions = []
        self.multivar = False
        self.functions_seen = set()
        self.current_file_size = 0

    def set_view(self, view):
        self.view = view

    def set_input_path(self, path):
        """Set the path for input data."""
        self.input_path = path
        print(f"Input path set to: {self.input_path}")

    def set_error_path(self, path):
        """Set the path for error weights file."""
        self.error_path = path
        print(f"Error path set to: {self.error_path}")

    def set_best_functions(self, best_functions):
        self.best_functions = best_functions

    def enable_function(self, function):
        """Enable a specific mathematical function."""
        self.enabled_functions.add(function)
        print(f"Function enabled: {function}")

    def disable_function(self, function):
        """Disable a specific mathematical function."""
        if function in self.enabled_functions:
            self.enabled_functions.remove(function)
            print(f"Function disabled: {function}")

    def get_enabled_functions(self):
        """Return a list of all enabled functions."""
        return list(self.enabled_functions)
    
    def load_input_data(self, file_path):
        try:
            input_data = np.loadtxt(file_path, delimiter='\t')
            self.input_data = self.convert_to_2d_array(input_data)
            if len(self.input_data) == 2:
                self.multivar = False
            else:
                self.multivar = True

        except Exception as e:
            print(f"Error loading data: {e}")
            self.input_data = None

        return self.input_data.copy(), self.multivar

    def convert_to_2d_array(self, data):
        converted_data = data.tolist()
        # Switch rows and columns (transpose)
        return np.transpose(converted_data).tolist()

    def get_input_data(self):
        return self.input_data
    
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
    
    def parse_best_file(self, file_path):
        generation_data = {}
        lines = []
        new_data, self.current_file_size = self.read_new_data(file_path, self.current_file_size)

        if new_data is None:
            return self.best_functions.copy()  # Return a copy of the list

        for line in new_data:
            line = line.strip()
            if line.isdigit():  # New generation
                if generation_data and generation_data['function'] not in self.functions_seen:
                    self.best_functions.append(generation_data.copy())
                    self.functions_seen.add(generation_data['function'])  # Mark this function as seen
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
        if generation_data and generation_data['function'] not in self.functions_seen:
            self.best_functions.append(generation_data)
            self.functions_seen.add(generation_data['function'])  # Mark this function as seen

        return self.best_functions.copy()

    def delete_best_function(self):
        self.functions_seen = set()
        self.best_functions = []
        self.current_file_size = 0
