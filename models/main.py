class Model:
    def __init__(self):
        self.input_path = ""
        self.error_path = ""
        self.enabled_functions = set()

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
