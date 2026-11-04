import customtkinter as ctk
from tkinter import StringVar, IntVar, Text, END
from utils.parameters import search_options
from utils.tooltips import add_tooltip, tooltip_text
from .base import BaseView, FilePicker

class InputView(BaseView):
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
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)   # the parameters list takes the spare width
        self.grid_rowconfigure(3, weight=1)      # and the spare height
        # The cards sit in a scrollable column so the screen stays usable in a small window
        self.left_column = ctk.CTkScrollableFrame(self, width=470, height=200, fg_color="transparent",
                                                  scrollbar_button_color=self.SCROLLBAR_COLOR)
        self.left_column.grid(row=0, column=0, rowspan=4, sticky="ns", padx=(0, self.PAD), pady=(0, self.PAD))
        self.left_column.grid_columnconfigure(0, weight=1)

    def configure_frame_grid(self, frame):
        frame.grid_columnconfigure(0, weight=0, minsize=130)
        frame.grid_columnconfigure(1, weight=1)

    def create_card(self, row, title):
        """A titled card in the left column; returns the frame."""
        card = ctk.CTkFrame(self.left_column, fg_color=self.CARD_COLOR)
        card.grid(row=row, column=0, sticky='ew', padx=(0, self.PAD), pady=(0, self.PAD))
        self.configure_frame_grid(card)
        ctk.CTkLabel(card, text=title, font=self.font).grid(row=0, column=0, columnspan=2, sticky="w", padx=self.PAD, pady=(self.PAD, 2))
        return card

    def setup_file_section(self):
        self.data_frame = self.create_card(0, "Input options")
        self.setup_file_widgets(self.data_frame, 1)
        self.setup_terminal_frame(self.data_frame, 3)

    def setup_file_widgets(self, frame, start_row=1):
        self.input_file_button = self.create_file_button(frame, "Input file", start_row, 0)
        self.error_file_button = self.create_file_button(frame, "Error weights file", start_row, 1)

    def create_file_button(self, frame, text, start_row, add_row):
        label = ctk.CTkLabel(frame, text=text)
        label.grid(row=start_row+add_row, column=0, sticky='w', padx=self.PAD, pady=self.PAD // 2)
        tip = "input_file" if add_row == 0 else "error_file"
        button = FilePicker(frame, lambda bt=add_row: self.invoke_callback('browse_file', bt), tip,
                            side_pad=self.BUTTON_SIDE_PAD, height=self.BUTTON_HEIGHT, font=self.button_font)
        button.grid(row=start_row+add_row, column=1, sticky='w', padx=self.PAD, pady=self.PAD // 2)
        add_tooltip(label, tip)
        return button
    
    def setup_terminal_frame(self, frame, start_row=3):
        variables_label = ctk.CTkLabel(frame, text="Input variables")
        variables_label.grid(row=start_row, column=0, sticky='nw', padx=self.PAD, pady=self.PAD)
        button = self.create_button(frame, "All/None", self.toggle_variables, tooltip="all_none")
        button.grid(row=start_row+1, column=0, sticky='nw', padx=self.PAD, pady=self.PAD // 2)

        self.terminal_scroll_frame = ctk.CTkScrollableFrame(frame, width=self.DROPDOWN_WIDTH - 20, height=70, scrollbar_fg_color=self.SCROLLBAR_COLOR, fg_color=self.LIST_COLOR)
        self.terminal_scroll_frame._scrollbar.configure(height=0)
        self.terminal_scroll_frame.grid(row=start_row, column=1, rowspan=2, sticky="w", padx=self.PAD, pady=self.PAD // 2)
        add_tooltip(variables_label, "variables")
        add_tooltip(self.terminal_scroll_frame, "variables")

        terminal_label = ctk.CTkLabel(frame, text="Terminal set")
        terminal_label.grid(row=start_row+2, column=0, sticky='w', padx=self.PAD, pady=self.PAD // 2)
        self.terminal_set = StringVar(value="")
        self.terminal_set.trace_add('write', lambda *args: self.invoke_callback("terminal_set_change", self.variable_checkboxes, self.terminal_set.get()))
        terminal_entry = ctk.CTkEntry(frame, textvariable=self.terminal_set, width=self.DROPDOWN_WIDTH, height=self.FIELD_HEIGHT)
        terminal_entry.grid(row=start_row+2, column=1, sticky='w', padx=self.PAD, pady=(self.PAD // 2, self.PAD))
        add_tooltip(terminal_label, "terminal_set")
        add_tooltip(terminal_entry, "terminal_set")

    def populate_terminal_scroll_frame(self, var_num, curr_terminal_set, terminal_set_without_vars):
        self.terminal_set.set(terminal_set_without_vars)
        self.variable_checkboxes = {}

        for i in range(var_num):
            checkbox_text = f"x{i+1}"
            checkbox = ctk.CTkCheckBox(self.terminal_scroll_frame, text=checkbox_text, command=lambda *args: self.invoke_callback("terminal_set_change", self.variable_checkboxes, self.terminal_set.get()))
            checkbox.grid(row=i, column=0, sticky='w', padx=5, pady=3)
            if checkbox_text in curr_terminal_set:
                checkbox.select()
            add_tooltip(checkbox, "variables")
            self.variable_checkboxes[i] = checkbox

    def setup_search_options(self):
        self.search_frame = self.create_card(1, "Search options")
        self.add_search_options(self.search_frame)

    def add_search_options(self, frame):
        for idx, option in enumerate(search_options):
            variable_name, label, choices = option
            self.setup_dropdown(frame, variable_name, label, choices, idx+1, 1)

    def setup_parameters_scroll_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=300, height=300, scrollbar_fg_color=self.SCROLLBAR_COLOR, fg_color=self.LIST_COLOR)
        self.scroll_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", pady=(0, self.PAD))
        self.scroll_frame.grid_columnconfigure(0, weight=0)
        self.scroll_frame.grid_columnconfigure(1, weight=1)

    def populate_scroll_frame(self, options):
        row_counter = 0
        for section, items in options.items():
            section_label = ctk.CTkLabel(self.scroll_frame, text=section, font=self.font)
            section_label.grid(row=row_counter, column=0, columnspan=2, sticky='w', pady=(10 if row_counter else 2, 5), padx=5)
            row_counter += 1

            if section == "Functions":
                self.checkbox_vars = {}
                for label, func in items:
                    self.checkbox_vars[func] = ctk.CTkCheckBox(self.scroll_frame, text=label, command=lambda f=func: self.invoke_callback('function_toggle', f))
                    self.checkbox_vars[func].grid(row=row_counter, column=0, columnspan=2, sticky='w', padx=5, pady=3)
                    add_tooltip(self.checkbox_vars[func], func)
                    row_counter += 1
            else:
                self.params_vars = {}  # This will store the entry widgets, which is acceptable in view
                for label, path in items:
                    param_label = ctk.CTkLabel(self.scroll_frame, text=label)
                    param_label.grid(row=row_counter, column=0, sticky='w', padx=5, pady=3)
                    add_tooltip(param_label, path)

                    params_var = StringVar(value="")
                    params_var.trace_add('write', lambda var, index, mode, p=path, v=params_var: self.invoke_callback('other_parameter_change', p, v))
                    param_entry = ctk.CTkEntry(self.scroll_frame, textvariable=params_var, width=self.ENTRY_WIDTH, height=self.FIELD_HEIGHT)
                    param_entry.grid(row=row_counter, column=1, sticky='w', padx=5, pady=3)
                    add_tooltip(param_entry, path)
                    self.params_vars[path] = params_var  # Storing entry widget is an exception to avoid direct data handling
                    row_counter += 1

    def setup_other_options_frame(self):
        self.other_options_frame = self.create_card(2, "Other options")

        self.setup_number_of_threads(self.other_options_frame, row=1)

        label = ctk.CTkLabel(self.other_options_frame, text="Linear scaling")
        label.grid(row=2, column=0, sticky="w", padx=self.PAD, pady=(self.PAD // 2, self.PAD))

        self.linear_scaling_checkbox = ctk.CTkCheckBox(self.other_options_frame, text="", width=28, command=lambda: self.invoke_callback('linear_scaling_toggle'))
        self.linear_scaling_checkbox.grid(row=2, column=1, sticky='w', padx=self.PAD, pady=(self.PAD // 2, self.PAD))
        add_tooltip(label, "linear_scaling")
        add_tooltip(self.linear_scaling_checkbox, "linear_scaling")

    def setup_number_of_threads(self, frame, row):
        label = ctk.CTkLabel(frame, text="Number of threads")
        label.grid(row=row, column=0, sticky="w", padx=self.PAD, pady=self.PAD // 2)

        # Thread count entry and buttons
        thread_frame = ctk.CTkFrame(frame, fg_color="transparent")
        thread_frame.grid(row=row, column=1, sticky="w", padx=self.PAD, pady=self.PAD // 2)

        thread_var = IntVar()
        thread_var.trace_add('write', lambda *args: self.invoke_callback('dropdown_option_change', 'thread_num', thread_var.get()))
        thread_var.set(1)
        entry = ctk.CTkEntry(thread_frame, textvariable=thread_var, width=self.ENTRY_WIDTH, height=self.FIELD_HEIGHT)
        entry.grid(row=0, column=0, padx=(0, self.PAD))
        minus_button = ctk.CTkButton(thread_frame, text="-", width=self.BUTTON_HEIGHT, height=self.BUTTON_HEIGHT, corner_radius=self.BUTTON_HEIGHT // 2, command=lambda *args: self.change_number(thread_var, -1))
        minus_button.grid(row=0, column=1, padx=(0, self.PAD))
        plus_button = ctk.CTkButton(thread_frame, text="+", width=self.BUTTON_HEIGHT, height=self.BUTTON_HEIGHT, corner_radius=self.BUTTON_HEIGHT // 2, command=lambda *args: self.change_number(thread_var, 1))
        plus_button.grid(row=0, column=2)
        for widget in (label, entry, minus_button, plus_button):
            add_tooltip(widget, "thread_num")

    def change_number(self, var, delta):
        new_value = min(max(1, var.get() + delta), self.max_threads)   # Prevent going below 1
        var.set(new_value)

    def setup_action_buttons(self):
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=4, column=0, columnspan=2, pady=(self.PAD, 0))

        self.apply_button = self.create_button(action_frame, "Apply", lambda: self.invoke_callback('apply_button_click'),
                                               min_width=144, tooltip=lambda: tooltip_text("apply_edit" if self.edit_mode else "apply"))
        self.apply_button.grid(row=0, column=0, padx=self.PAD)

        self.change_button = self.create_button(action_frame, "Change Manually", lambda: self.invoke_callback('change_button_click'),
                                                min_width=144, tooltip=lambda: tooltip_text("change_back" if self.edit_mode else "change"))
        self.change_button.grid(row=0, column=1, padx=self.PAD)

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
            self.config_editor = Text(self, height=10, width=50, font=("Menlo", 12), padx=8, pady=8,
                                      relief="flat", highlightthickness=1, highlightbackground="#c8c8c8")
            self.config_editor.grid(row=0, column=0, rowspan=4, columnspan=2, sticky='nsew', pady=(0, self.PAD))
            add_tooltip(self.config_editor, "config_editor")
        
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

        self.invoke_callback("terminal_set_change", self.variable_checkboxes, self.terminal_set.get())

    def clear_terminal_scroll_frame(self):
        for child in self.terminal_scroll_frame.winfo_children():
            child.destroy()