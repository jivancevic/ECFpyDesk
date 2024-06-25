import customtkinter as ctk
from tkinter import StringVar, IntVar, Text, END
from utils.parameters import search_options, plot_options
from .base import BaseView

class InputView(BaseView):
    FG_COLOR = "#008000"

    def __init__(self, parent):
        super().__init__(parent)
        
        self.variable_checkboxes = None
        self.terminal_set = None
        self.search_metric = None
        self.train_test_split = None
        self.test_sample = None
        self.plot_y_axis_var = None
        self.plot_x_axis_var = None
        self.plot_scale_var = None
        self.edit_mode = False
        self.max_threads = 1
    
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
        self.setup_terminal_frame(self.data_frame)

    def setup_file_widgets(self, frame):
        self.input_file_button = self.create_file_button(frame, "Input file", 0)
        self.error_file_button = self.create_file_button(frame, "Error weights file", 1)

    def create_file_button(self, frame, text, row):
        ctk.CTkLabel(frame, text=text).grid(row=row, column=0, sticky='w', pady=5)
        button = ctk.CTkButton(frame, text="Select File", command=lambda bt=row: self.invoke_callback('browse_file', bt))
        button.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        return button
    
    def setup_terminal_frame(self, frame):
        ctk.CTkLabel(frame, text="Input variables").grid(row=2, column=0, sticky='w', pady=5)
        button = ctk.CTkButton(frame, text="All/None", command=self.toggle_variables)
        button.grid(row=3, column=0, sticky='ew', padx=5, pady=5)

        self.terminal_scroll_frame = ctk.CTkScrollableFrame(frame, width=180, height=70, scrollbar_fg_color=self.FG_COLOR, fg_color="#f0f0f0")
        self.terminal_scroll_frame._scrollbar.configure(height=0)
        self.terminal_scroll_frame.grid(row=2, column=1, rowspan=2, sticky="ew", pady=5)

        ctk.CTkLabel(frame, text="Terminal set").grid(row=4, column=0, sticky='w', pady=5)
        self.terminal_set = StringVar(value="")
        self.terminal_set.trace_add('write', lambda *args: self.invoke_callback("terminal_set_change", self.variable_checkboxes, self.terminal_set.get()))
        ctk.CTkEntry(frame, textvariable=self.terminal_set).grid(row=4, column=1, sticky='ew', padx=5, pady=5)

    def populate_terminal_scroll_frame(self, var_num, curr_terminal_set, terminal_set_without_vars):
        self.terminal_set.set(terminal_set_without_vars)
        self.variable_checkboxes = {}

        for i in range(var_num):
            checkbox_text = f"x{i+1}"
            checkbox = ctk.CTkCheckBox(self.terminal_scroll_frame, text=checkbox_text, command=lambda *args: self.invoke_callback("terminal_set_change", self.variable_checkboxes, self.terminal_set))
            checkbox.grid(row=i, column=0, sticky='ew', padx=5, pady=3)
            if checkbox_text in curr_terminal_set:
                checkbox.select()
            self.variable_checkboxes[i] = checkbox

    def setup_search_options(self):
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        self.add_search_options(self.search_frame)

    def add_search_options(self, frame):
        for idx, option in enumerate(search_options):
            variable_name, label, choices = option
            self.setup_dropdown(frame, variable_name, label, choices, idx, 1)

    def setup_parameters_scroll_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=300, height=150, scrollbar_fg_color=self.FG_COLOR, fg_color="#f0f0f0")
        self.scroll_frame.grid(row=0, column=1, rowspan=2, sticky="ew", pady=5)

    def populate_scroll_frame(self, options):
        row_counter = 0
        for section, items in options.items():
            section_label = ctk.CTkLabel(self.scroll_frame, text=section, font=('Arial', 12, 'bold'))
            section_label.grid(row=row_counter, column=0, columnspan=2, sticky='ew', pady=(10, 5), padx=5)
            row_counter += 1

            if section == "Functions":
                self.checkbox_vars = {}
                for label, func in items:
                    self.checkbox_vars[func] = ctk.CTkCheckBox(self.scroll_frame, text=label, command=lambda f=func: self.invoke_callback('function_toggle', f))
                    self.checkbox_vars[func].grid(row=row_counter, column=0, sticky='ew', padx=5, pady=3)
                    row_counter += 1
            else:
                self.params_vars = {}  # This will store the entry widgets, which is acceptable in view
                for label, path in items:
                    param_label = ctk.CTkLabel(self.scroll_frame, text=label)
                    param_label.grid(row=row_counter, column=0, sticky='w', padx=5, pady=3)

                    params_var = StringVar(value="")
                    params_var.trace_add('write', lambda var, index, mode, p=path, v=params_var: self.invoke_callback('other_parameter_change', p, v))
                    param_entry = ctk.CTkEntry(self.scroll_frame, textvariable=params_var)
                    param_entry.grid(row=row_counter, column=1, sticky='ew', padx=5, pady=3)
                    self.params_vars[path] = params_var  # Storing entry widget is an exception to avoid direct data handling
                    row_counter += 1

    def setup_other_options_frame(self):
        self.other_options_frame = ctk.CTkFrame(self)
        self.other_options_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
        self.other_options_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(self.other_options_frame, text="Other options")
        title_label.grid(row=0, column=0, columnspan=2, sticky="w")

        self.setup_number_of_threads(self.other_options_frame, row=1)

        for idx, option in enumerate(plot_options):
            variable_name, label, choices = option
            self.setup_dropdown(self.other_options_frame, variable_name, label, choices, idx+2, 1)

    def setup_number_of_threads(self, frame, row):
        label = ctk.CTkLabel(frame, text="Number of threads")
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

        # Thread count entry and buttons
        thread_frame = ctk.CTkFrame(frame)
        thread_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        for i, weight in enumerate([3,1,1]):
            thread_frame.grid_columnconfigure(i, weight=weight, uniform="Silent_Creme")

        thread_var = IntVar()
        thread_var.trace_add('write', lambda *args: self.invoke_callback('dropdown_option_change', 'thread_num', thread_var.get()))
        thread_var.set(1)
        entry = ctk.CTkEntry(thread_frame, textvariable=thread_var, width=120)
        entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        minus_button = ctk.CTkButton(thread_frame, text="-", command=lambda *args: self.change_number(thread_var, -1))
        minus_button.grid(row=0, column=1, padx=5)
        plus_button = ctk.CTkButton(thread_frame, text="+", command=lambda *args: self.change_number(thread_var, 1))
        plus_button.grid(row=0, column=2, padx=5)

    def change_number(self, var, delta):
        new_value = min(max(1, var.get() + delta), self.max_threads)   # Prevent going below 1
        var.set(new_value)

    def setup_action_buttons(self):
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=5)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        self.apply_button = ctk.CTkButton(action_frame, text="Apply", command=lambda: self.invoke_callback('apply_button_click'))
        self.apply_button.grid(row=0, column=0, sticky='ew', padx=5)

        self.change_button = ctk.CTkButton(action_frame, text="Change Manually", command=lambda: self.invoke_callback('change_button_click'))
        self.change_button.grid(row=0, column=1, sticky='ew', padx=5)

    def on_change_button_click(self):
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

    def display_config_editor(self, text):
        # Display the configuration file for editing
        if not hasattr(self, 'config_editor'):
            self.config_editor = Text(self, height=10, width=50)
            self.config_editor.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew')
        
        self.config_editor.insert(END, text)
        self.config_editor.lift()

    def close_config_editor(self):
        # Save the changes and remove the text widget
        if hasattr(self, 'config_editor'):
            self.config_editor.delete("1.0","end")
            self.config_editor.lower()
    
    def toggle_variables(self):
        all_selected = True
        for i, checkbox in self.variable_checkboxes.items():
            if not checkbox.get():
                all_selected = False
                break
        
        if all_selected:
            [checkbox.deselect() for i, checkbox in self.variable_checkboxes.items()]
        else:
            [checkbox.select() for i, checkbox in self.variable_checkboxes.items()]

        self.invoke_callback("terminal_set_change", self.variable_checkboxes, self.terminal_set)