import customtkinter as ctk
from tkinter import filedialog

def browse_file(entry):
    filepath = filedialog.askopenfilename()
    entry.set(filepath)

def show_input():
    results_frame.grid_remove()
    input_frame.grid(row=1, column=1, sticky='nsew')
    input_button.configure(fg_color="#4CAF50")
    results_button.configure(fg_color="#f0f0f0")
    function_scroll_frame.update_idletasks()

def show_results():
    input_frame.grid_remove()
    results_frame.grid(row=1, column=1, sticky='nsew')
    input_button.configure(fg_color="#f0f0f0")
    results_button.configure(fg_color="#4CAF50")
    function_scroll_frame.update_idletasks()

# Set up the main window
root = ctk.CTk()
root.title("ECFpyDesk")
root.geometry("800x600")

# Create columns with weights and an empty column as buffer
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=10)  # Main content column should have more weight
root.columnconfigure(2, weight=1)

# Navigation buttons
nav_frame = ctk.CTkFrame(root)
nav_frame.grid(row=0, column=0, columnspan=3, sticky='ew')
nav_frame.columnconfigure(0, weight=1)
nav_frame.columnconfigure(1, weight=1)

input_button = ctk.CTkButton(nav_frame, text="Input", command=show_input, fg_color="#4CAF50")
input_button.grid(row=0, column=0, padx=10, pady=10, sticky='e')
results_button = ctk.CTkButton(nav_frame, text="Results", command=show_results, fg_color="#f0f0f0")
results_button.grid(row=0, column=1, padx=10, pady=10, sticky='w')

# INPUT TAB
input_frame = ctk.CTkFrame(root)
input_frame.grid(row=1, column=1, sticky='nsew', padx=20, pady=10)

# Part 1: Input Frame
data_frame = ctk.CTkFrame(input_frame)
data_frame.grid(row=0, column=1, sticky='ew', padx=20, pady=10)

# Input file widgets
ctk.CTkLabel(data_frame, text="Input file").grid(row=0, column=0, sticky='w', pady=5)
input_file_entry = ctk.CTkEntry(data_frame, width=40)
input_file_entry.grid(row=0, column=1, sticky='ew')
ctk.CTkButton(data_frame, text="Browse", command=lambda: browse_file(input_file_entry)).grid(row=0, column=2, padx=10)

# Error weights file widgets
ctk.CTkLabel(data_frame, text="Error weights file").grid(row=1, column=0, sticky='w', pady=5)
error_file_entry = ctk.CTkEntry(data_frame, width=40)
error_file_entry.grid(row=1, column=1, sticky='ew')
ctk.CTkButton(data_frame, text="Browse", command=lambda: browse_file(error_file_entry)).grid(row=1, column=2, padx=10)

# Part 2: Search Options Frame
search_frame = ctk.CTkFrame(input_frame)
search_frame.grid(row=2, column=1, sticky='ew', padx=20, pady=10)

# Search metric and other options setup similarly using customtkinter widgets
# Search Metric
ctk.CTkLabel(search_frame, text="Search metric").grid(row=0, column=0, sticky='w', pady=5)
metric_var = ctk.StringVar(value="Mean squared error (MSE)")  # Setting default value
metric_options = ["Mean squared error (MSE)", "Mean absolute error (MAE)", "Mean absolute percentage error (MAPE)"]
metric_dropdown = ctk.CTkOptionMenu(search_frame, variable=metric_var, values=metric_options)
metric_dropdown.grid(row=0, column=1, sticky='ew')

# Train/Test Split
ctk.CTkLabel(search_frame, text="Train/test split").grid(row=1, column=0, sticky='w', pady=5)
split_var = ctk.StringVar(value="50/50")  # Setting default value
split_options = ["50/50", "80/20", "100/0"]
split_dropdown = ctk.CTkOptionMenu(search_frame, variable=split_var, values=split_options)
split_dropdown.grid(row=1, column=1, sticky='ew')

# Test Sample Selection
ctk.CTkLabel(search_frame, text="Test sample").grid(row=2, column=0, sticky='w', pady=5)
sample_var = ctk.StringVar(value="Chosen randomly")  # Setting default value
sample_options = ["Chosen randomly", "Chosen sequentially"]
sample_dropdown = ctk.CTkOptionMenu(search_frame, variable=sample_var, values=sample_options)
sample_dropdown.grid(row=2, column=1, sticky='ew')

# A canvas for additional options might include functionality settings
# Create a scrollable frame for listing functions
function_scroll_frame = ctk.CTkScrollableFrame(search_frame, width=300, height=200, scrollbar_fg_color="#008000", fg_color="#f0f0f0")
function_scroll_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

# Access the inner frame where widgets can be placed
#inner_frame = function_scroll_frame.get_frame()

functions = [
    ("Addition", "+"), ("Multiplication", "*"), ("Division", "/"),
    ("sin(x)", "sin"), ("cos(x)", "cos")
]
checkbox_vars = {}
for i, (label, func) in enumerate(functions):
    label_widget = ctk.CTkLabel(function_scroll_frame, text=label)
    label_widget.grid(row=i, column=0, sticky='ew')
    checkbox_vars[func] = ctk.CTkCheckBox(function_scroll_frame)
    checkbox_vars[func].grid(row=i, column=1, sticky='e')

#function_scroll_frame.update_layout()  # This may vary; use update_idletasks if update_layout is not available
function_scroll_frame.update_idletasks()  # Update internal frame to adjust scroll region properly


# RESULTS TAB
results_frame = ctk.CTkFrame(root)
results_frame.grid(row=1, column=1, sticky='nsew', padx=20, pady=10)
ctk.CTkLabel(results_frame, text="Hello World").pack()

# Start with the input frame showing by default
results_frame.grid_remove()

root.mainloop()
