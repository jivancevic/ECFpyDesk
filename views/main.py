import logging
from .navigation import NavigationView
from .input import InputView
from .results import ResultsView
import customtkinter as ctk
from tkinter import messagebox

logger = logging.getLogger(__name__)


class View(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")  # Modes: system (default), light, dark
        ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

        super().__init__()
        self.frames = {}
        self.initialize_ui()

    def initialize_ui(self):
        self.title("ECFpyDesk")
        self.geometry("1000x780")
        self.minsize(900, 740)

        self.grid_columnconfigure(0, weight=1)   # one column: the navigation bar and the screens share it
        self.grid_rowconfigure(0, weight=0)      # navigation bar keeps its height
        self.grid_rowconfigure(1, weight=1)      # the screen takes the rest

        # Initialize the navigation frame
        self.navigation_frame = NavigationView(self)
        self.frames['navigation'] = self.navigation_frame
        self.navigation_frame.grid(row=0, column=0, sticky='ew')

        # Initialize other frames
        self.input_frame = InputView(self)
        self.frames['input'] = self.input_frame
        self.results_frame = ResultsView(self)
        self.frames['results'] = self.results_frame

        # Start with the input frame showing by default
        self.results_frame.grid_remove()
        self.input_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 16))

    def switch(self, name):
        if name == "input":
            self.show_input()
        elif name == "results":
            self.show_results()
        self.update_idletasks()

    def show_input(self):
        self.results_frame.grid_remove()
        self.input_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 16))
        self.navigation_frame.set_active_tab("input")

    def show_results(self):
        self.input_frame.grid_remove()
        self.results_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 16))
        self.navigation_frame.set_active_tab("results")

    def display_error(self, message):
        # Show an error message dialog
        messagebox.showerror("Error", message)
        logger.error(f"Error: {message}")

    def start(self):
        self.mainloop()