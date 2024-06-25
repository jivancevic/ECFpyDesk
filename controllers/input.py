import multiprocessing
from tkinter import filedialog, END
from utils.parameters import options, search_options
from .base import BaseController

class InputController(BaseController):
    def __init__(self, model, controller, view):
        super().__init__(model, controller, view, view.frames["input"])
        self.register_callbacks()

    def register_callbacks(self):
        self.frame.register_callback('browse_file', self.handle_browse_file)
        self.frame.register_callback('apply_button_click', self.on_apply_button_click)
        self.frame.register_callback('change_button_click', self.on_change_button_click)
        self.frame.register_callback('terminal_set_change', self.handle_terminal_set_change)
        self.frame.register_callback('function_toggle', self.handle_function_toggle)
        self.frame.register_callback('other_parameter_change', self.handle_other_parameter_change)
        self.frame.register_callback('dropdown_option_change', self.handle_dropdown_option_change)

    def initialize_frame(self):
        super().initialize_frame()
        self.frame.max_threads = multiprocessing.cpu_count()
        self.frame.populate_scroll_frame(options)
        self.update_view_with_data()

    def update_view_with_data(self):
        input_path = self.model.get_current_input_path()
        if input_path is not None:
            self.model.set_input_path(input_path)
            self.frame.input_file_button.configure(text=input_path.split('/')[-1])
        
        self.populate_terminal_scroll_frame()
        self.controller.handle_input_data_change()
        
        function_set = self.model.get_current_function_set()
        self.model.set_function_set(function_set)
        for func, checkbox in self.frame.checkbox_vars.items():
            checkbox.select() if func in function_set else checkbox.deselect()

        for path, var in self.frame.params_vars.items():
            current_value = self.model.config_manager.get_current_param_value(path)
            var.set(current_value)

    def handle_browse_file(self, button_type):
        filepath = filedialog.askopenfilename()
        if filepath:
            if button_type == 0:
                button = self.frame.input_file_button
                self.model.set_input_path(filepath)
                self.populate_terminal_scroll_frame()
                self.controller.handle_input_data_change()
            else:
                button = self.frame.error_file_button
                self.model.set_error_path(filepath)
            button.configure(text=filepath.split('/')[-1])

    def populate_terminal_scroll_frame(self):
        curr_terminal_set = self.model.get_current_terminal_set()
        terminal_set_without_vars = self.get_terminal_set_without_variables(curr_terminal_set)
        data = self.model.load_input_data()
        var_num = len(data)-1
        self.frame.populate_terminal_scroll_frame(var_num, curr_terminal_set, terminal_set_without_vars)

    def get_terminal_set_without_variables(self, terminal_set):
        return " ".join(t for t in terminal_set.split(" ") if "x" not in t)

    def on_apply_button_click(self):
        if not self.frame.edit_mode:
            print("Applying configurations")
            self.controller.apply_configurations()
        else:
            if hasattr(self.frame, 'config_editor'):
                with open(self.controller.get_parameters_file_path(), 'w') as file:
                    file.write(self.frame.config_editor.get("1.0", END))
                self.initialize_frame()
                self.on_change_button_click()

    def on_change_button_click(self):
        if not self.frame.edit_mode:
            self.frame.edit_mode = True
            self.frame.change_button.configure(text="Back")
            self.frame.apply_button.configure(text="Save")
            with open(self.controller.get_parameters_file_path(), 'r') as file:
                self.frame.display_config_editor(file.read())
        else:
            self.frame.edit_mode = False
            self.frame.change_button.configure(text="Change Manually")
            self.frame.apply_button.configure(text="Apply")
            self.frame.close_config_editor()
    
    def handle_terminal_set_change(self, variable_checkboxes, terminal_set):
        if self.frame.variable_checkboxes is not None:
            terminal_set_string = self.generate_terminal_set_string(variable_checkboxes, terminal_set)
            self.model.terminal_set = terminal_set_string

    def generate_terminal_set_string(self, variable_checkboxes, terminal_text):
        selected_variables = [f"x{i+1}" for i, checkbox in variable_checkboxes.items() if checkbox.get()]
        selected_variables.append(terminal_text)
        return " ".join(selected_variables)

    def handle_function_toggle(self, func):
        # Update model based on the state of the function checkbox
        is_selected = self.frame.checkbox_vars[func].get()
        self.model.enable_function(func) if is_selected else self.model.disable_function(func)

    def handle_other_parameter_change(self, path, value):
        self.model.set_variable_with_path(path, value.get())

    def handle_dropdown_option_change(self, variable_name, value):
        self.model.set_variable(variable_name, value)

    def update_number_of_threads(self, new_value):
        # Validate and update the number of threads in the model
        validated_value = max(1, min(new_value, multiprocessing.cpu_count()))
        self.model.set_thread_count(validated_value)
        self.view.update_thread_display(validated_value)
    