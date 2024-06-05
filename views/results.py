import customtkinter as ctk
import tkinter as tk
from tkinter import font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from utils.plot import safe_dict, set_x_range

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']

class ResultsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.controller = None
        self.default_bg = "#f0f0f0"  # Default background color
        self.active_bg = "#d0e0f0"  # Active background color when clicked
        self.current_active_row = None  # Track the currently active row

        self.initialize_ui()

    def initialize_ui(self):
        """Setup the initial UI elements and frame configurations."""
        self.configure_grid()
        self.setup_solutions_frame()
        self.setup_info_frame()
        self.setup_plot_area()

    def configure_grid(self):
        """Configure row and column settings for the grid. Silent_Creme uniform makes grid be equal no matter the size."""
        self.rowconfigure(list(range(2)), weight = 1, uniform="Silent_Creme")
        self.columnconfigure(list(range(2)), weight = 1, uniform="Silent_Creme")

    def setup_solutions_frame(self):
        """Setup solutions frame with a separate header and list section."""
        self.solutions_master_frame = ctk.CTkFrame(self)
        self.solutions_master_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        # Setup header frame for column titles
        self.header_frame = ctk.CTkFrame(self.solutions_master_frame)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        headers = ["Size", "Error", "Function"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(self.header_frame, text=header).grid(row=0, column=i)
            self.header_frame.columnconfigure(i, weight=[1, 2, 8][i])

        # Setup scrollable list frame for displaying solutions
        self.solutions_list_frame = ctk.CTkScrollableFrame(self.solutions_master_frame, width=300, height=200, scrollbar_fg_color="#008000", fg_color="#f0f0f0")
        self.solutions_list_frame.grid(row=1, column=0, sticky="nsew")
        self.solutions_list_frame.grid_columnconfigure(0, weight=1, uniform="Silent_Creme")
        self.solutions_list_frame.grid_columnconfigure(1, weight=2, uniform="Silent_Creme")
        self.solutions_list_frame.grid_columnconfigure(2, weight=8, uniform="Silent_Creme")
        self.solutions_master_frame.grid_rowconfigure(1, weight=1)  # Allocate most space to the list frame
        self.solutions_master_frame.grid_columnconfigure(0, weight=1)  # Allocate most space to the list frame

    def setup_info_frame(self):
        """Setup the information display frame."""
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=1, column=0, sticky="nsew")
        info_frame.rowconfigure(0, weight=1)  # Allow dynamic expansion for text box
        labels = ["Function", "Mean error", "Mean error (relative)", "RMS error", "Classification accuracy"]
        self.setup_labels(info_frame, labels)

    def setup_labels(self, info_frame, labels):
        """Create labels and variable displays for information."""
        self.info_vars = {label: ctk.StringVar(value="0") for label in labels if label != "Function"}
        self.function_display = self.create_textbox(info_frame)
        for i, label in enumerate(labels):
            ctk.CTkLabel(info_frame, text=label).grid(row=i, column=0, sticky='w', padx=(10, 0), pady=5)
            if label != "Function":
                ctk.CTkLabel(info_frame, textvariable=self.info_vars[label]).grid(row=i, column=1, sticky='ew', padx=(0, 20), pady=5)

    def create_textbox(self, parent):
        """Create a textbox for function display."""
        textbox = ctk.CTkTextbox(parent, state='disabled', wrap='word', fg_color='transparent', height=100)
        textbox.grid(row=0, column=1, sticky='ew', pady=5)
        return textbox

    def setup_plot_area(self):
        """Setup the plotting area."""
        self.figure = plt.Figure(figsize=(2, 2))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=1, sticky='nsew')
        self.canvas.draw()

    def set_controller(self, controller):
        self.controller = controller

    def update_info(self, function, error):
        # Enable the textbox to modify its contents
        self.function_display.configure(state='normal')
        self.function_display.delete(1.0, "end")
        self.function_display.insert("end", function)

        # Update other information variables
        self.info_vars["Mean error"].set(f"{float(error):.4f}")
        for key in ["Mean error (relative)", "RMS error", "Classification accuracy"]:
            self.info_vars[key].set("0")

        # Update the plot if required
        self.update_plot(function=function)

    def handle_row_click(self, event, row, function, error):
        # Update all rows to default color
        self.reset_row_colors()
        # Set the active row color
        self.set_active_row_color(row)
        # Update information based on the function and error
        self.update_info(function, error)

    def reset_row_colors(self):
        # Reset colors for all rows to default
        for widget in self.solutions_list_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(fg_color=self.default_bg)

    def set_active_row_color(self, row):
        # Set the active row color
        for index, widget in enumerate(self.solutions_list_frame.winfo_children()):
            if index // 3 == row:  # Assuming 3 widgets per row
                widget.configure(fg_color=self.active_bg)
                self.current_active_row = row

    def get_plot_data(self):
        return self.controller.get_plot_data()

    def update_plot(self, x_data=None, y_data=None, function=None):
        if x_data is None or y_data is None:
            x_data, y_data = self.get_plot_data()

        self.ax.clear()  # Clear the previous plot
        self.ax.scatter(x_data, y_data)  # Create scatter plot

        # Set x range for plotting functions
        set_x_range(x_data)

        # Plotting custom function if provided
        if function:
            try:
                # Generate x values for plotting the function
                x_values = safe_dict['x']
                # Evaluate the function string safely
                y_values = eval(function, {"__builtins__": {}}, safe_dict)
                self.ax.plot(x_values, y_values, 'g-', label=function)  # Plot the custom function
                self.ax.legend()  # Add a legend to distinguish plotted lines
            except Exception as e:
                print(f"Error evaluating function '{function}': {e}")

        self.canvas.draw()  # Update the canvas

    def update_solutions_frame(self):
        best_functions = self.controller.get_best_functions()

        for i in range(5):
            print()
        print("functions:", best_functions)

        if (best_functions):
            for i, func in enumerate(best_functions):
                if i == 0:
                    print()
                    print()
                    print()
                    print(func)

                size = func["size"]
                error = func["error"]
                function = func["function"]
                print("size:", size)
                print("error:", error)
                print("function:", function)

                # Use labels and truncate text if necessary
                size_label = ctk.CTkLabel(self.solutions_list_frame, text=str(size), justify="center", fg_color="red")
                size_label.grid(row=i, column=0, sticky='ew')

                error_label = ctk.CTkLabel(self.solutions_list_frame, text=f"{error:.4f}", justify="center", fg_color="blue")
                error_label.grid(row=i, column=1, sticky='ew')

                function_text = function if len(function) <= 60 else function[:57] + "..."
                function_label = ctk.CTkLabel(self.solutions_list_frame, text=function_text, justify="center", fg_color="green")
                function_label.grid(row=i, column=2, sticky='ew')

                # Bind the click event to the entire row
                for label in [size_label, error_label, function_label]:
                    label.bind("<Button-1>", lambda event, row=i, e=error, f=function: self.handle_row_click(event, row, f, e))

    def show_results(self, results_data):
        # Method to update the entire results view with new data
        pass
