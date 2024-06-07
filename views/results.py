import customtkinter as ctk
import tkinter as tk
from tkinter import font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from utils.plot import safe_dict

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
        self.setup_terminal_frame()
        self.setup_solutions_frame()
        self.setup_info_frame()
        self.setup_plot_area()
        self.setup_keyboard_bindings()

    def configure_grid(self):
        """Configure row and column settings for the grid. Silent_Creme uniform makes grid be equal no matter the size."""
        self.rowconfigure(list(range(6)), weight = 1, uniform="Silent_Creme")
        self.columnconfigure(list(range(6)), weight = 1, uniform="Silent_Creme")

    def setup_terminal_frame(self):
        # Terminal output frame
        self.terminal_frame = ctk.CTkFrame(self)
        self.terminal_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_frame.grid_rowconfigure(0, weight=1)

        # Create a scrolled text widget for terminal output
        self.output_display = ctk.CTkTextbox(self.terminal_frame, state='normal', wrap='word')
        self.output_display.grid(row=0, column=0, sticky="nsew")

    def append_output(self, text):
        """Append text to the output display."""
        self.output_display.configure(state='normal')
        self.output_display.insert('end', text)
        self.output_display.configure(state='disabled')
        self.output_display.yview('end')  # Auto-scroll to the end

    def setup_solutions_frame(self):
        """Setup solutions frame with a separate header and list section."""
        self.solutions_master_frame = ctk.CTkFrame(self)
        self.solutions_master_frame.grid(row=0, column=2, columnspan=4, sticky="nsew")
        
        # Setup header frame for column titles
        self.header_frame = ctk.CTkFrame(self.solutions_master_frame)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        headers = ["Size", "Error", "Function"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(self.header_frame, text=header).grid(row=0, column=i)
            self.header_frame.columnconfigure(i, weight=[1, 2, 8][i], uniform="Silent_Creme")

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
        info_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
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
        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=3, columnspan=3, sticky='nsew')

    def set_controller(self, controller):
        self.controller = controller

    def get_plot_data(self):
        return self.controller.get_plot_data()
    
    def setup_keyboard_bindings(self):
        # Ensure the frame can receive focus
        self.solutions_list_frame.focus_set()
        # Bind the up and down arrow keys
        self.solutions_list_frame.bind("<Up>", self.move_selection_up)
        self.solutions_list_frame.bind("<Down>", self.move_selection_down)

    def move_selection_up(self, event):
        if self.current_active_row is not None and self.current_active_row > 0:
            # Move selection up if not the first row
            self.select_row(self.current_active_row - 1)
    
    def move_selection_down(self, event):
        if self.current_active_row is not None and self.current_active_row < len(self.solutions_list_frame.winfo_children()) // 3 - 1:
            # Move selection down if not the last row
            self.select_row(self.current_active_row + 1)

    def select_row(self, row, event=None):
        # Check if the row is valid and avoid any processing if it's the currently active row
        if row == self.current_active_row or row < 0 or row >= len(self.solutions_list_frame.winfo_children()) // 3:
            return
        
        function = self.best_functions[row]["function"]
        error = self.best_functions[row]["error"]

        # Update UI as if the row was clicked
        self.update_info(function, error)
        self.reset_row_colors()
        self.set_active_row_color(row)
        self.current_active_row = row  # Update the currently active row

    '''
    def handle_row_click(self, event, row, function, error):
        self.select_row(row)  # Select the row as part of the click event handling
        # Update all rows to default color
        self.reset_row_colors()
        # Set the active row color
        self.set_active_row_color(row)
        # Update information based on the function and error
        self.update_info(function, error)
    '''

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

    def update_plot(self, x_data=None, y_data=None, function=None):
        if x_data is None or y_data is None:
            x_data, y_data = self.get_plot_data()

        multivar = self.controller.is_multivar()

        self.ax.clear()  # Clear the previous plot
        self.ax.scatter(x_data, y_data, color='blue', label='Data')  # Scatter plot of original data

        # Plotting custom function if provided
        if function:
            # Evaluate the function using the controller
            x_values, function_results = self.controller.evaluate_function(function, multivar)
            try: 
                if not multivar:
                    self.ax.plot(x_values, function_results, 'g-', label='Function')  # Plot the custom function
                else:
                    self.ax.scatter(x_data, function_results, color='red', label='Function')  # Scatter plot of function evaluation
            except Exception as e:
                print(f"Error evaluating function '{function}': {e}")

        self.ax.legend()  # Add a legend to distinguish plotted lines
        self.canvas.draw()  # Update the canvas

    def update_solutions_frame(self):
        self.best_functions = self.controller.get_best_functions()

        if (self.best_functions):
            for i, func in enumerate(self.best_functions):
                size = func["size"]
                error = func["error"]
                function = func["function"]

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
                    label.bind("<Button-1>", lambda event, row=i: self.select_row(row, event))

    def clear_frame(self):
        # Clear the textbox
        self.function_display.configure(state='normal')
        self.function_display.delete(1.0, "end")
        self.function_display.configure(state='disabled')

        # Clear the solutions frame
        for widget in self.solutions_list_frame.winfo_children():
            widget.destroy()

        # Reset all information variables to default values
        for key in self.info_vars:
            self.info_vars[key].set("0")

        # Clear the plot
        self.ax.clear()
        self.ax.legend().remove()  # Remove the legend if it exists
        self.canvas.draw()

        # Optionally, reset any selections or highlighted rows
        self.current_active_row = None
        self.reset_row_colors()  # Reset colors for all rows to default if needed