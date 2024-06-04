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

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Solutions frame setup
        solutions_frame = ctk.CTkFrame(self)
        solutions_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        solutions_frame.columnconfigure(0, weight=1)
        solutions_frame.columnconfigure(1, weight=2)
        solutions_frame.columnconfigure(2, weight=8)

        # Dummy data for solutions
        self.dummy_data = [
            (1, 2.434, "-0.233"),
            (3, 1.2343, "x"),
            (4, 1.2233, "atan(x)"),
            (11, 0.3245, "(-1.92323+x)*(-0.023343-sin(x))")
        ]

        for i, (size, error, func) in enumerate(self.dummy_data):
            ctk.CTkLabel(solutions_frame, text=str(size)).grid(row=i, column=0, sticky='ew')
            ctk.CTkLabel(solutions_frame, text=f"{error:.4f}").grid(row=i, column=1, sticky='ew')
            btn = ctk.CTkButton(solutions_frame, text=func, command=lambda e=error, f=func: self.update_info(f, e))
            btn.grid(row=i, column=2, sticky='ew')

        # Solution info frame setup
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=1, column=0, sticky="nsew")
        labels = ["Function", "Mean error", "Mean error (relative)", "RMS error", "Classification accuracy"]
        self.info_vars = {label: ctk.StringVar(value="0") for label in labels}
        for i, label in enumerate(labels):
            ctk.CTkLabel(info_frame, text=label).grid(row=i, column=0, sticky='w')
            ctk.CTkLabel(info_frame, textvariable=self.info_vars[label]).grid(row=i, column=1, sticky='w')

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
        self.info_vars["Function"].set(function)
        self.info_vars["Mean error"].set(f"{float(error):.4f}")
        # Set other fields to zero as per the requirement
        for key in ["Mean error (relative)", "RMS error", "Classification accuracy"]:
            self.info_vars[key].set("0")
        # Assuming a function to update the plot
        self.update_plot(function=function)

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

    def show_results(self, results_data):
        # Method to update the entire results view with new data
        pass
