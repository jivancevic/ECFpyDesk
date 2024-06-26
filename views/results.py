import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from utils.parameters import plot_options
from .base import BaseView

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']

class ResultsView(BaseView):
    DEFAULT_BG = "#f0f0f0"  # Default background color
    ACTIVE_BG = "#d0e0f0"  # Active background color when clicked
    
    def __init__(self, parent):
        super().__init__(parent)

        self.best_functions = []
        self.current_active_row = None

        self.initialize_ui()

    def initialize_ui(self):
        """Setup the initial UI elements and frame configurations."""
        self.configure_grid()
        self.setup_solutions_frame()
        self.setup_info_frame()
        self.setup_plot_area()
        self.setup_keyboard_bindings()

    def configure_grid(self):
        """Configure row and column settings for the grid. Silent_Creme uniform makes grid be equal no matter the size."""
        self.rowconfigure(list(range(6)), weight = 1, uniform="Silent_Creme")
        self.columnconfigure(list(range(6)), weight = 1, uniform="Silent_Creme")

    def setup_solutions_frame(self):
        """Setup solutions frame with a separate header and list section."""
        self.solutions_master_frame = ctk.CTkFrame(self)
        self.solutions_master_frame.grid(row=0, column=0, columnspan=6, rowspan=3, sticky="nsew")
        
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

    def setup_info_frame(self, test_option=False):
        """Setup the information display frame."""
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=3, column=0, columnspan=3, rowspan=3, sticky="nsew")
        start_row = 1 if test_option else 0

        self.info_frame.rowconfigure(start_row, weight=1)  # Allow dynamic expansion for text box
        self.info_frame.columnconfigure(1, weight=1)  # Allow dynamic expansion for text box

        if test_option:
            checkbox_text = "Show Test Data"
            checkbox = ctk.CTkCheckBox(self.info_frame, text=checkbox_text, command=lambda *args: self.invoke_callback("show_test_data", checkbox.get()))
            checkbox.grid(row=0, column=0, columnspan=2, sticky='e', padx=5, pady=3)

        labels = ["Function", "Error"]
        self.setup_labels(self.info_frame, labels, start_row=start_row)
        self.setup_plot_options(self.info_frame, start_row=start_row+2)

    def setup_labels(self, frame, labels, start_row=0):
        """Create labels and variable displays for information."""
        self.info_vars = {label: ctk.StringVar(value="0") for label in labels if label != "Function"}
        self.function_display = self.create_textbox(frame, start_row)
        for i, label in enumerate(labels):
            ctk.CTkLabel(frame, text=label).grid(row=i+start_row, column=0, sticky='w', padx=5, pady=5)
            if label != "Function":
                ctk.CTkLabel(frame, textvariable=self.info_vars[label]).grid(row=i+start_row, column=1, sticky='ew', padx=(0, 20), pady=5)

    def create_textbox(self, parent, row):
        """Create a textbox for function display."""
        textbox = ctk.CTkTextbox(parent, state='disabled', wrap='word', fg_color='transparent', height=100)
        textbox.grid(row=row, column=1, sticky='ew', pady=5)
        return textbox
    
    def setup_plot_options(self, frame, start_row=2):
        for idx, option in enumerate(plot_options):
            variable_name, label, choices = option
            self.setup_dropdown(frame, variable_name, label, choices, idx+start_row, 1)

    def setup_plot_area(self):
        """Setup the plotting area."""
        self.figure = plt.Figure(figsize=(3, 3))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=3, column=3, columnspan=3, rowspan=3, sticky='nsew')
    
    def setup_keyboard_bindings(self):
        # Ensure the frame can receive focus
        self.solutions_list_frame.focus_set()
        # Bind the up and down arrow keys
        self.solutions_list_frame.bind("<Up>", lambda event: self.invoke_callback('move_selection', 'up'))
        self.solutions_list_frame.bind("<Down>", lambda event: self.invoke_callback('move_selection', 'down'))

    def reset_row_colors(self):
        # Reset colors for all rows to default
        for widget in self.solutions_list_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(fg_color=self.DEFAULT_BG)

    def set_active_row_color(self, row):
        # Set the active row color
        for index, widget in enumerate(self.solutions_list_frame.winfo_children()):
            if index // 3 == row:  # Assuming 3 widgets per row
                widget.configure(fg_color=self.ACTIVE_BG)
                self.current_active_row = row
    
    def update_info(self, function, error):
        # Enable the textbox to modify its contents
        self.function_display.configure(state='normal')
        self.function_display.delete(1.0, "end")
        self.function_display.insert("end", function)

        # Update other information variables
        self.info_vars["Error"].set(f"{float(error):.6f}")

    def update_plot(self, x_data, y_data, x_values=None, function_results=None, multivar=False, plot_type="scatter", plot_scale=0, plot_y_index=0):
        self.ax.clear()  # Clear the previous plot
        
        x_data = np.array(x_data)
        y_data = np.array(y_data)

        if plot_y_index == 0:
            self.ax.scatter(x_data, y_data, color='blue', label='Data')  # Scatter plot of original data

        if function_results is not None:
            function_results = np.array(function_results)
            residuals = np.subtract(y_data, function_results)

            if plot_y_index == 1:
                self.add_to_plot(x_data, residuals, 'black', 'Residual Error', plot_type)
                #self.ax.plot(x_data, residuals, 'r-', label='Residual Error')
            elif plot_y_index == 2:
                with np.errstate(divide='ignore', invalid='ignore'):
                    residual_percent = np.abs(residuals / y_data) * 100
                    valid_mask = np.isfinite(residual_percent)
                    print(f"valid_mask: {valid_mask}")
                    print(f"Residual percent: {residual_percent}")
                    self.add_to_plot(x_data[valid_mask], residual_percent[valid_mask], 'magenta', 'Residual Error %', plot_type)
                    #self.ax.plot(x_data[valid_mask], residual_percent[valid_mask], 'm-', label='Residual Error %')
            else:
                self.add_to_plot(x_data, function_results, 'red', 'Target variable', plot_type)
                #self.ax.plot(x_data, function_results, color='red', label='Function')  # Scatter plot of function evaluation

        if plot_scale == 1:  # Log scale for y-axis
            self.ax.set_yscale('log')
        elif plot_scale == 2:  # Log scale for x-axis
            self.ax.set_xscale('log')
        elif plot_scale == 3:  # Log scale for both axes
            self.ax.set_yscale('log')
            self.ax.set_xscale('log')

        self.ax.legend()  # Add a legend to distinguish plotted lines
        self.canvas.draw()  # Update the canvas

    def add_to_plot(self, x, y, color, label, type):
        if type == "plot":
            self.ax.plot(x, y, color=color, label=label)
        elif type == "bar":
            self.ax.bar(x, y, color=color, label=label)
        else:
            self.ax.scatter(x, y, color=color, label=label)

    def create_solution_row(self, func, row_index):
        size_label = ctk.CTkLabel(self.solutions_list_frame, text=str(func["size"]), justify="center")
        size_label.grid(row=row_index, column=0, sticky='ew')

        error_label = ctk.CTkLabel(self.solutions_list_frame, text=f'{func["error"]:.4f}', justify="center")
        error_label.grid(row=row_index, column=1, sticky='ew')

        function_text = func["function"] if len(func["function"]) <= 70 else func["function"][:67] + "..."
        function_label = ctk.CTkLabel(self.solutions_list_frame, text=function_text, justify="left")
        function_label.grid(row=row_index, column=2, sticky='ew')

        # Bind the click event to the entire row
        for label in [size_label, error_label, function_label]:
            label.bind("<Button-1>", lambda event, row=row_index: self.invoke_callback('select_row', row))

    def update_solution_row(self, func, row_index):
        # Iterate over all children widgets in the solutions list frame
        for widget in self.solutions_list_frame.winfo_children():
            # Grid_info returns dictionary with details about the grid configuration of the widget
            info = widget.grid_info()
            # Check if the widget is in the row we want to destroy
            if info['row'] == row_index:
                if info['column'] == 0:
                    widget.configure(text=str(func["size"]))
                if info['column'] == 1:
                    widget.configure(text=f'{func["error"]:.4f}')
                if info['column'] == 2:
                    function_text = func["function"] if len(func["function"]) <= 70 else func["function"][:67] + "..."
                    widget.configure(text=function_text)
                widget.unbind("<Button-1>")
                widget.bind("<Button-1>", lambda event, row=row_index: self.invoke_callback('select_row', row))
    
    def destroy_solution_row(self, row_index):
        # Iterate over all children widgets in the solutions list frame
        for widget in self.solutions_list_frame.winfo_children():
            # Grid_info returns dictionary with details about the grid configuration of the widget
            info = widget.grid_info()
            # Check if the widget is in the row we want to destroy
            if info['row'] == row_index and widget.winfo_exists():
                widget.destroy()

    def clear_function_display(self):
        self.function_display.configure(state='normal')
        self.function_display.delete(1.0, "end")
        self.function_display.configure(state='disabled')

    def clear_frame(self):
        # Clear the solutions frame
        for widget in self.solutions_list_frame.winfo_children():
            widget.destroy()

        # Reset all information variables to default values
        for key in self.info_vars:
            self.info_vars[key].set("0")

        # Clear the plot
        self.ax.clear()
        
        # Check if there are any artists with labels in the plot
        if self.ax.get_legend_handles_labels()[0]:
            self.ax.legend().remove()  # Remove the legend if it exists

        self.canvas.draw()
        self.reset_row_colors() 

        self.best_functions = []
        self.current_active_row = None