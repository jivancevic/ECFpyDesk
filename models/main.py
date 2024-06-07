import numpy as np

class Model:
    def __init__(self):
        self.input_path = ""
        self.error_path = ""
        self.enabled_functions = set()
        self.input_data = None
        self.plot_x_index = None
        self.best_individuals = None
        self.multivar = False

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
            self.data = None

    def convert_to_2d_array(self, data):
        converted_data = data.tolist()
        # Switch rows and columns (transpose)
        return np.transpose(converted_data).tolist()

    def get_input_data(self):
        return self.input_data
    

