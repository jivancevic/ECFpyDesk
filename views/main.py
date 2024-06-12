from .navigation import NavigationView
from .input import InputView
from .results import ResultsView
import customtkinter as ctk

class View(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ECFpyDesk")
        self.geometry("800x700")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=10)  # Main content column should have more weight
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0)
        self.grid_rowconfigure(1)

        # Initialize the navigation frame
        self.navigation_frame = NavigationView(self)
        self.navigation_frame.grid(row=0, column=0, columnspan=3, sticky='ew')

        # Initialize other frames
        self.input_frame = InputView(self)
        self.results_frame = ResultsView(self)

        # Start with the input frame showing by default
        self.results_frame.grid_remove()
        self.input_frame.grid(row=1, column=1, sticky='nsew', padx=20, pady=10)
    
    def set_controller(self, controller):
        self.controller = controller
        self.navigation_frame.set_controller(controller)
        self.input_frame.set_controller(controller)
        self.results_frame.set_controller(controller)

    def show_input(self):
        self.results_frame.grid_remove()
        self.input_frame.grid(row=1, column=1, sticky='nsew', padx=20, pady=10)
        self.navigation_frame.input_button.configure(fg_color="#4CAF50")
        self.navigation_frame.results_button.configure(fg_color="#f0f0f0")

    def show_results(self):
        self.input_frame.grid_remove()
        self.results_frame.grid(row=1, column=1, sticky='nsew', padx=20, pady=10)
        self.navigation_frame.input_button.configure(fg_color="#f0f0f0")
        self.navigation_frame.results_button.configure(fg_color="#4CAF50")

    def start(self):
        self.mainloop()