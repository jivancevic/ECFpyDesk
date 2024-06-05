import customtkinter as ctk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from utils.plot import safe_dict, set_x_range

# Simplify font settings
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']

class ResultsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None

        self.default_bg = "#f0f0f0"  # Default background color
        self.active_bg = "#d0e0f0"  # Active background color when clicked
        self.current_active_row = None  # Track the currently active row

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Solutions frame setup
        self.solutions_frame = ctk.CTkScrollableFrame(self,  width=300, height=200, scrollbar_fg_color="#008000", fg_color="#f0f0f0")
        self.solutions_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.solutions_frame.columnconfigure(0, weight=1)
        self.solutions_frame.columnconfigure(1, weight=2)
        self.solutions_frame.columnconfigure(2, weight=8)

        # Column headers for the solutions frame
        ctk.CTkLabel(self.solutions_frame, text="Size").grid(row=0, column=0)
        ctk.CTkLabel(self.solutions_frame, text="Error").grid(row=0, column=1)
        ctk.CTkLabel(self.solutions_frame, text="Function").grid(row=0, column=2)

        # Solution info frame setup
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=1, column=0, sticky="nsew")
        #info_frame.grid_rowconfigure(0, weight=1)  # Allow the textbox row to expand
        #info_frame.grid_columnconfigure(1, weight=1)  # Allow the column to expand
        
        labels = ["Function", "Mean error", "Mean error (relative)", "RMS error", "Classification accuracy"]
        self.info_vars = {label: ctk.StringVar(value="0") for label in labels[1:]}  # Except 'Function' which will use a Textbox
        self.function_display = ctk.CTkTextbox(info_frame, state='disabled', wrap='word', fg_color='transparent')
        self.function_display.grid(row=0, column=1, sticky='nsew', padx=(0, 20), pady=10)  # Fill the cell
        for i, label in enumerate(labels):
            ctk.CTkLabel(info_frame, text=label).grid(row=i, column=0, sticky='w', padx=(10, 0), pady=5)
            if label in self.info_vars:
                ctk.CTkLabel(info_frame, textvariable=self.info_vars[label]).grid(row=i, column=1, sticky='ew', padx=(0, 20), pady=5)

        # Plotting area - resizing to fit into 25% of the space in the bottom right
        self.figure = plt.Figure(figsize=(2, 2))  # Adjust figsize to scale with the parent frame
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, self)  # Parent is self to manage layout with grid
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=1, sticky='nsew')  # Place at bottom right
        self.canvas.draw()

    def set_controller(self, controller):
        self.controller = controller

    def update_info(self, function, error):
        self.function_display.configure(state='normal')  # Enable editing temporarily
        self.function_display.delete(1.0, "end")  # Clear previous content
        self.function_display.insert("end", function)  # Insert new function text
        self.function_display.configure(state='disabled')  # Disable editing

        self.info_vars["Mean error"].set(f"{float(error):.4f}")
        # Reset other fields
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
        for widget in self.solutions_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(fg_color=self.default_bg)

    def set_active_row_color(self, row):
        # Set the active row color
        for index, widget in enumerate(self.solutions_frame.winfo_children()):
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
                size_label = ctk.CTkLabel(self.solutions_frame, text=str(size))
                size_label.grid(row=i+1, column=0, sticky='ew')

                error_label = ctk.CTkLabel(self.solutions_frame, text=f"{error:.4f}")
                error_label.grid(row=i+1, column=1, sticky='ew')

                function_text = function if len(function) <= 60 else function[:57] + "..."
                function_label = ctk.CTkLabel(self.solutions_frame, text=function_text)
                function_label.grid(row=i+1, column=2, sticky='ew')

                # Bind the click event to the entire row
                for label in [size_label, error_label, function_label]:
                    label.bind("<Button-1>", lambda event, row=i+1, e=error, f=function: self.handle_row_click(event, row, f, e))

    def show_results(self, results_data):
        # Method to update the entire results view with new data
        pass
