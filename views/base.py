import customtkinter as ctk
from tkinter import StringVar
from utils.publisher import Publisher

class BaseView(ctk.CTkFrame, Publisher):
    def __init__(self, parent):
        ctk.CTkFrame.__init__(self, parent)
        Publisher.__init__(self)

    def setup_dropdown(self, frame, variable_name, label_text, choices, row, column):
        label = ctk.CTkLabel(frame, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)
        display_var = StringVar()
        display_var.trace_add('write', lambda *args: self.invoke_callback('dropdown_option_change', variable_name, label_to_value_map[display_var.get()]))
        label_to_value_map = {label: value for label, value in choices}
        dropdown_labels = list(label_to_value_map.keys())
        display_var.set(dropdown_labels[0])
        dropdown = ctk.CTkOptionMenu(frame, variable=display_var, values=dropdown_labels)
        dropdown.grid(row=row, column=column, sticky="ew", padx=5, pady=5)