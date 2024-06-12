import customtkinter as ctk
from tkinter import filedialog, StringVar, IntVar, Text, END
import multiprocessing
import os
from utils.parameters import options, search_options

class InputView(ctk.CTkFrame):
    FG_COLOR = "#008000"
    controller = None
    input_file_path = ""
    error_file_path = ""
    terminal_set = None
    search_metric = None
    train_test_split = None
    test_sample = None
    plot_y_axis_var = None
    plot_x_axis_var = None
    plot_scale_var = None
    edit_mode = False

    def __init__(self, parent):
        super().__init__(parent)
        self.max_threads = multiprocessing.cpu_count()

    def set_controller(self, controller):
        self.controller = controller
        self.initialize_ui()
    
    def initialize_ui(self):
        self.configure_grid()
        self.setup_file_section()
        self.setup_search_options()
        self.setup_parameters_scroll_area()
        self.setup_other_options_frame()
        self.setup_action_buttons()

    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1, uniform="Silent_Creme")
        self.grid_columnconfigure(1, weight=1, uniform="Silent_Creme")

    def setup_file_section(self):
        self.data_frame = ctk.CTkFrame(self)
        self.data_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        self.setup_file_widgets(self.data_frame)

    def setup_file_widgets(self, frame):
        self.input_file_button = self.create_file_button(frame, "Input file", 0)
        self.error_file_button = self.create_file_button(frame, "Error weights file", 1)

        ctk.CTkLabel(frame, text="Terminal set").grid(row=2, column=0, sticky='w', pady=5)
        curr_terminal_set = self.controller.get_terminal_set()
        self.terminal_set = StringVar(value=curr_terminal_set if curr_terminal_set is not None else "")
        ctk.CTkEntry(frame, textvariable=self.terminal_set).grid(row=2, column=1, sticky='ew', padx=5, pady=5)

    def create_file_button(self, frame, text, row):
        ctk.CTkLabel(frame, text=text).grid(row=row, column=0, sticky='w', pady=5)
        button = ctk.CTkButton(frame, text="Select File", command=lambda bt=row: self.browse_file(bt))
        button.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        return button

    def setup_search_options(self):
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        self.add_search_options(self.search_frame)

    def add_search_options(self, frame):
        for idx, option in enumerate(search_options):
            variable_name, label, choices = option
            self.setup_dropdown(frame, variable_name, label, choices, idx, self.on_option_change)

    def setup_parameters_scroll_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=300, height=150, scrollbar_fg_color=self.FG_COLOR, fg_color="#f0f0f0")
        self.scroll_frame.grid(row=0, column=1, rowspan=2, sticky="ew", pady=5)
        self.populate_parameters(self.scroll_frame, options)

    def populate_parameters(self, frame, options):
        row_counter = 0  # To manage layout dynamically based on the content

        for section, items in options.items():
            # Create a label for the section heading
            section_label = ctk.CTkLabel(frame, text=section, font=('Arial', 12, 'bold'))
            section_label.grid(row=row_counter, column=0, columnspan=2, sticky='ew', pady=(10, 5), padx=5)
            row_counter += 1

            # Depending on the section type, populate differently
            if section == "Functions":
                self.checkbox_vars = {}
                current_function_set = self.controller.get_current_function_set().strip().split(' ')
                for label, func in items:
                    self.checkbox_vars[func] = ctk.CTkCheckBox(frame, text=label)
                    self.checkbox_vars[func].grid(row=row_counter, column=0, sticky='ew', padx=5, pady=3)
                    if func in current_function_set:
                        self.checkbox_vars[func].select()  # Assuming you want all checkboxes selected by default
                    row_counter += 1
            else:
                self.params_vars = {}  # Store the StringVar instances to keep track of entry values
                for label, path in items:
                    # Label for the registry or any other parameter
                    param_label = ctk.CTkLabel(frame, text=label)
                    param_label.grid(row=row_counter, column=0, sticky='w', padx=5, pady=3)

                    # Create a StringVar and set it to the path
                    curr_value = self.controller.get_current_param_value(path=path)
                    params_var = StringVar(value=curr_value if curr_value is not None else "")
                    self.params_vars[path] = params_var  # Store the variable with label as key

                    # Entry for the registry or any other parameter value
                    param_entry = ctk.CTkEntry(frame, textvariable=params_var)
                    param_entry.grid(row=row_counter, column=1, sticky='ew', padx=5, pady=3)
                    row_counter += 1

    def setup_other_options_frame(self):
        # Create the frame for other options
        self.other_options_frame = ctk.CTkFrame(self)
        self.other_options_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
        self.other_options_frame.grid_columnconfigure(1, weight=1)

        # Title label
        title_label = ctk.CTkLabel(self.other_options_frame, text="Other options")
        title_label.grid(row=0, column=0, columnspan=2, sticky="w")

        # Row 1: Number of threads
        self.setup_number_of_threads(self.other_options_frame, row=1)

        # Row 2: Plot y axis
        self.setup_dropdown(self.other_options_frame, "plot_y_axis_var", "Plot y axis", [("Target variable", "0"), ("Xxx", "1")], 2, self.on_option_change)

        # Row 3: Plot x axis
        self.setup_dropdown(self.other_options_frame, "plot_x_axis_var", "Plot x axis", [("Row number", -1), ("x1", 0), ("x2", 1)], 3, self.on_option_change)

        # Row 4: Plot scale
        self.setup_dropdown(self.other_options_frame, "plot_scale_var", "Plot scale", [("Regular", 0), ("Xxx", 1)], 4, self.on_option_change)

    def setup_number_of_threads(self, frame, row):
        label = ctk.CTkLabel(frame, text="Number of threads")
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

        # Thread count entry and buttons
        thread_frame = ctk.CTkFrame(frame)
        thread_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        for i, weight in enumerate([3,1,1]):
            thread_frame.grid_columnconfigure(i, weight=weight, uniform="Silent_Creme")

        thread_var = IntVar(value=1)
        entry = ctk.CTkEntry(thread_frame, textvariable=thread_var, width=120)
        entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        minus_button = ctk.CTkButton(thread_frame, text="-", command=lambda: self.change_number(thread_var, -1))
        minus_button.grid(row=0, column=1, padx=5)
        plus_button = ctk.CTkButton(thread_frame, text="+", command=lambda: self.change_number(thread_var, 1))
        plus_button.grid(row=0, column=2, padx=5)


    def setup_dropdown(self, frame, variable_name, label_text, choices, row, callback):
        label = ctk.CTkLabel(frame, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

        # This is a StringVar that will get the actual choice label from the dropdown
        display_var = StringVar()

        # Convert choices to a label to value mapping and initialize the dropdown with labels
        label_to_value_map = {label: value for label, value in choices}
        dropdown_labels = list(label_to_value_map.keys())
        display_var.set(dropdown_labels[0])  # Set the display variable to show the first label
        callback(variable_name, label_to_value_map[dropdown_labels[0]])

        dropdown = ctk.CTkOptionMenu(frame, variable=display_var, values=dropdown_labels)
        dropdown.grid(row=row, column=1, sticky="ew", padx=5, pady=5)

        # Setup a trace on the display variable to update the actual variable when selection changes
        def on_selection_change(*args):
            label = display_var.get()
            value = label_to_value_map[label]
            # This assumes you have a method to update the actual variable in your controller or model
            callback(variable_name, value)

        display_var.trace_add('write', on_selection_change)

    def on_option_change(self, variable_name, value):
        # Assuming you have a method to handle the changes in actual values
        setattr(self, variable_name, value)

    def change_number(self, var, delta):
        new_value = min(max(1, var.get() + delta), self.max_threads)   # Prevent going below 1
        var.set(new_value)

    def setup_action_buttons(self):
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=5)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        self.apply_button = ctk.CTkButton(action_frame, text="Apply", command=self.toggle_save_button)
        self.apply_button.grid(row=0, column=0, sticky='ew', padx=5)

        self.change_button = ctk.CTkButton(action_frame, text="Change Manually", command=self.toggle_config_editing)
        self.change_button.grid(row=0, column=1, sticky='ew', padx=5)

    def toggle_config_editing(self):
        if not self.edit_mode:
            self.edit_mode = True
            self.change_button.configure(text="Back")
            self.apply_button.configure(text="Save")
            self.display_config_editor()
        else:
            self.edit_mode = False
            self.change_button.configure(text="Change Manually")
            self.apply_button.configure(text="Apply")
            self.close_config_editor()

    def display_config_editor(self):
        # Display the configuration file for editing
        if not hasattr(self, 'config_editor'):
            self.config_editor = Text(self, height=10, width=50)
            self.config_editor.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew')
        
        with open(self.controller.get_parameters_file_path(), 'r') as file:
            self.config_editor.insert(END, file.read())
        self.config_editor.lift()

    def close_config_editor(self):
        # Save the changes and remove the text widget
        if hasattr(self, 'config_editor'):
            self.config_editor.delete("1.0","end")
            self.config_editor.lower()

    def toggle_save_button(self):
        if not self.edit_mode:
            self.controller.on_apply_button_click()
        else:
            if hasattr(self, 'config_editor'):
                with open(self.controller.get_parameters_file_path(), 'w') as file:
                    file.write(self.config_editor.get("1.0", END))
    
    def browse_file(self, button_type):
        filepath = filedialog.askopenfilename()
        if filepath:
            button = self.input_file_button if button_type == 0 else self.error_file_button
            button.configure(text=filepath.split('/')[-1])
            setattr(self, 'input_file_path' if button_type == 0 else 'error_file_path', filepath)

    def on_run_button_click(self):
        if self.controller:
            self.controller.on_run_button_click()