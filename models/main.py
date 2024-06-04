import numpy as np

class Model:
    def __init__(self):
        self.input_path = ""
        self.error_path = ""
        self.enabled_functions = set()
        self.data = None
        self.plot_x_index = None

    def set_input_path(self, path):
        """Set the path for input data."""
        self.input_path = path
        print(f"Input path set to: {self.input_path}")

    def set_error_path(self, path):
        """Set the path for error weights file."""
        self.error_path = path
        print(f"Error path set to: {self.error_path}")

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
    
    def load_data(self, file_path):
        try:
            self.data = np.loadtxt(file_path, delimiter='\t')
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = None

    def get_plot_data(self, x_index=None):
        if x_index is not None:
            self.plot_x_index = x_index
        elif self.plot_x_index is None:
            return [], []
        
        if self.data is not None:
            self.x_data = self.data[:, self.plot_x_index]  # Data from the first column
            self.y_data = self.data[:, self.data.shape[1]-1]  # Data from the third column
            return self.x_data, self.y_data
        
        return [], []  # Return empty lists if no data
    

