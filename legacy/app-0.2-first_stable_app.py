import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
import json

from call_ECF import call_ECF

# Open the JSON file for reading
with open('config.json', 'r') as file:
    # Load its content and turn it into a Python dictionary
    config = json.load(file)

def run_call_ECF():
    # Fetching values from the GUI
    input_file_path = input_file_var.get()  # gets the input file path
    error_weights_file_path = error_file_var.get()  # gets the error weights file path
    error_metric = error_metric_var.get()  # gets the selected error metric
    terminal_entry = terminal_entry_var.get() # gets the terminal variables
    
    # Now call call_ECF with these parameters
    call_ECF(input_file_path=input_file_path, error_weights_file_path=error_weights_file_path, error_metric=error_metric, terminal_entry=terminal_entry)

def browse_file(entry):
    filename = filedialog.askopenfilename()
    entry.set(filename)

root = ctk.CTk()
root.title("Symbolic Regression Interface")
root.grid_columnconfigure(1, weight=1)  # Make the second column expandable

# Padding settings
padx, pady = 10, 5  # Padding for x and y dimensions

# Line 1: Function Set
ctk.CTkLabel(root, text="Function set").grid(row=0, column=0, sticky="w", padx=padx, pady=pady)
function_set = ["+", "-", "*", "/", "sin", "cos"]
chk_vars = [tk.BooleanVar() for _ in function_set]
for i, func in enumerate(function_set):
    ctk.CTkCheckBox(root, text=func, variable=chk_vars[i]).grid(row=0, column=i+1, sticky="w", padx=padx, pady=pady)

# Line 2: Terminal Set
ctk.CTkLabel(root, text="Terminal set").grid(row=1, column=0, sticky="w", padx=padx, pady=pady)
terminal_entry_var = tk.StringVar()
ctk.CTkEntry(root, textvariable=terminal_entry_var).grid(row=1, column=1, columnspan=6, sticky="w", padx=padx, pady=pady)

# Line 3: Input File
ctk.CTkLabel(root, text="Input file").grid(row=2, column=0, sticky="w", padx=padx, pady=pady)
input_file_var = tk.StringVar()
input_file_entry = ctk.CTkEntry(root, textvariable=input_file_var)
input_file_entry.grid(row=2, column=1, columnspan=5, sticky="w", padx=padx, pady=pady)
ctk.CTkButton(root, text="Browse", command=lambda: browse_file(input_file_var)).grid(row=2, column=6, padx=padx, pady=pady)

# Line 4: Error Weights File
ctk.CTkLabel(root, text="Error weights file").grid(row=3, column=0, sticky="w", padx=padx, pady=pady)
error_file_var = tk.StringVar()
error_file_entry = ctk.CTkEntry(root, textvariable=error_file_var)
error_file_entry.grid(row=3, column=1, columnspan=5, sticky="w", padx=padx, pady=pady)
ctk.CTkButton(root, text="Browse", command=lambda: browse_file(error_file_var)).grid(row=3, column=6, padx=padx, pady=pady)

# Line 5: Error Metric
ctk.CTkLabel(root, text="Error metric").grid(row=4, column=0, sticky="w", padx=padx, pady=pady)
error_metric_var = tk.StringVar()
error_metric_options = ["Mean squared error (MSE)", "Mean absolute error (MAE)", "Mean absolute percentage error (MAPE)"]
error_metric_dropdown = ctk.CTkOptionMenu(root, variable=error_metric_var, values=error_metric_options)
error_metric_dropdown.grid(row=4, column=1, columnspan=6, sticky="w", padx=padx, pady=pady)
error_metric_var.set(error_metric_options[0])  # default value

# Line 6: Run Button
ctk.CTkButton(root, text="Run", command=run_call_ECF).grid(row=5, column=0, columnspan=7, padx=padx, pady=pady)

root.mainloop()
