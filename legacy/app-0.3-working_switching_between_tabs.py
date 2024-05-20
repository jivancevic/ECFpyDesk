import tkinter as tk
from tkinter import ttk, filedialog

def browse_file(entry):
    filepath = filedialog.askopenfilename()
    entry.delete(0, tk.END)
    entry.insert(0, filepath)


def show_input():
    results_frame.grid_remove()  # Hide the results frame
    input_frame.grid(row=1, column=0, sticky='ew')  # Show the input frame

def show_results():
    input_frame.grid_remove()  # Hide the input frame
    results_frame.grid(row=1, column=0, sticky='ew')  # Show the input frame

# Set up the main window
root = tk.Tk()
root.title("Symbolic Regression Interface")
root.geometry("800x600")

# Create columns with weights and an empty column as buffer
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=10)  # Main content column should have more weight
root.columnconfigure(2, weight=1)


# Navigation buttons
nav_frame = ttk.Frame(root)
nav_frame.grid(row=0, column=0, columnspan=3, sticky='ew')  # Ensure the frame expands with the window
nav_frame.columnconfigure(0, weight=1)  # Input Button column
nav_frame.columnconfigure(1, weight=1)  # Results Button column

input_button = ttk.Button(nav_frame, text="Input", command=show_input)
input_button.grid(row=0, column=0, padx=10, pady=10, sticky='e')
results_button = ttk.Button(nav_frame, text="Results", command=show_results)
results_button.grid(row=0, column=1, padx=10, pady=10, sticky='w')


# INPUT TAB
input_frame = ttk.Frame(root)
input_frame.grid(row=1, column=0, sticky='ewns', padx=20, pady=10)

# Create columns with weights and an empty column as buffer
input_frame.columnconfigure(0, weight=1)
input_frame.columnconfigure(1, weight=3)
input_frame.columnconfigure(2, weight=3)
input_frame.columnconfigure(3, weight=1)

# Part 1: Input Frame
data_frame = ttk.Frame(input_frame)
data_frame.grid(row=0, column=1, sticky='ew', padx=20, pady=10)

# Input file widgets
ttk.Label(data_frame, text="Input file").grid(row=0, column=0, sticky='w', pady=5)
input_file_entry = ttk.Entry(data_frame, width=40)
input_file_entry.grid(row=0, column=1, sticky='ew')
ttk.Button(data_frame, text="Browse", command=lambda: browse_file(input_file_entry)).grid(row=0, column=2, padx=10)

# Error weights file widgets
ttk.Label(data_frame, text="Error weights file").grid(row=1, column=0, sticky='w', pady=5)
error_file_entry = ttk.Entry(data_frame, width=40)
error_file_entry.grid(row=1, column=1, sticky='ew')
ttk.Button(data_frame, text="Browse", command=lambda: browse_file(error_file_entry)).grid(row=1, column=2, padx=10)
    
# Input variables
ttk.Label(data_frame, text="Input variables").grid(row=2, column=0, sticky='w', pady=5)
variable_frame = ttk.Frame(data_frame)
variable_frame.grid(row=2, column=1, sticky='ew')

# Variables with checkboxes
vars = ["x1", "x2"]
checkbox_vars = {}  # To keep track of the checkbox states
for i, var in enumerate(vars):
    tk.Label(variable_frame, text=var).grid(row=0, column=2*i, sticky='w')
    checkbox_vars[var] = tk.BooleanVar()  # Create a variable to track the state of the checkbox
    tk.Checkbutton(variable_frame, variable=checkbox_vars[var]).grid(row=0, column=1+2*i, sticky='w')

# Additional terminals
tk.Label(variable_frame, text="Additional terminals").grid(row=1, column=0, columnspan=2, sticky='w', pady=(10, 0))
additional_terminals_entry = ttk.Entry(variable_frame)
additional_terminals_entry.grid(row=1, column=2, columnspan=4, sticky='ew', padx=(5, 0))


# Part 2: Search Options Frame
search_frame = ttk.Frame(input_frame)
search_frame.grid(row=1, column=1, sticky='ew', padx=20, pady=10)

# Search metric
ttk.Label(search_frame, text="Search metric").grid(row=0, column=0, sticky='w', pady=5)
metric_var = tk.StringVar()
metric_dropdown = ttk.OptionMenu(search_frame, metric_var, "Mean squared error (MSE)", "Mean squared error (MSE)", "Mean absolute error (MAE)", "Mean absolute percentage error (MAPE)")
metric_dropdown.grid(row=0, column=1, sticky='ew')

# Train/test split
ttk.Label(search_frame, text="Train/test split").grid(row=1, column=0, sticky='w', pady=5)
split_var = tk.StringVar()
split_dropdown = ttk.OptionMenu(search_frame, split_var, "50/50", "50/50", "80/20", "100/0")
split_dropdown.grid(row=1, column=1, sticky='ew')

# Test sample
ttk.Label(search_frame, text="Test sample").grid(row=2, column=0, sticky='w', pady=5)
sample_var = tk.StringVar()
sample_dropdown = ttk.OptionMenu(search_frame, sample_var, "Chosen randomly", "Chosen randomly", "Chosen sequentially")
sample_dropdown.grid(row=2, column=1, sticky='ew')


# Create a canvas and scrollbar
function_canvas = tk.Canvas(search_frame, borderwidth=0, background="#ffffff")
function_canvas.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

vsb = tk.Scrollbar(search_frame, orient="vertical", command=function_canvas.yview)
vsb.grid(row=3, column=2, sticky='ns')
function_canvas.configure(yscrollcommand=vsb.set)
function_canvas.configure(width=300, height=200)

# Frame within the canvas
function_frame = ttk.Frame(function_canvas)
function_canvas.create_window((0, 0), window=function_frame, anchor="nw")

functions = [
    ("Addition", "+"), ("Multiplication", "*"), ("Division", "/"),
    ("sin(x)", "sin"), ("cos(x)", "cos")
]
checkbox_vars = {}
for i, (label, func) in enumerate(functions):
    ttk.Label(function_frame, text=label).grid(row=i, column=0, sticky='w')
    checkbox_vars[func] = tk.BooleanVar()
    ttk.Checkbutton(function_frame, variable=checkbox_vars[func]).grid(row=i, column=1)

function_frame.update_idletasks()
function_canvas.config(scrollregion=function_canvas.bbox("all"))




# RESULTS TAB
results_frame = ttk.Frame(root)
results_frame.grid(row=1, column=0, sticky='ewns', padx=20, pady=10)
ttk.Label(results_frame, text="Hello World").pack()




# Start with the input frame showing by default
results_frame.grid_remove()

root.mainloop()


