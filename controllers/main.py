class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.set_controller(self)
        self.setup_callbacks()

    def setup_callbacks(self):
        # Instead of set_command, use StringVar tracing for entry widgets
        self.view.input_frame.input_file_entry_var.trace_add("write", lambda *args: self.update_input_path(self.view.input_frame.input_file_entry_var.get()))
        self.view.input_frame.error_file_entry_var.trace_add("write", lambda *args: self.update_error_path(self.view.input_frame.error_file_entry_var.get()))

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

    def start(self):
        self.view.start()