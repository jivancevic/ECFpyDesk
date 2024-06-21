from .navigation import NavigationView
from .input import InputView
from .results import ResultsView
import customtkinter as ctk
from tkinter import messagebox


class View(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")  # Modes: system (default), light, dark
        ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

        super().__init__()
        self.frames = {}
        self.initialize_ui()

    def initialize_ui(self):
        self.title("ECFpyDesk")
        self.geometry("800x700")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=10)  # Main content column should have more weight
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0)
        self.grid_rowconfigure(1)

        # Initialize the navigation frame
        self.navigation_frame = NavigationView(self)
        self.frames['navigation'] = self.navigation_frame
        self.navigation_frame.grid(row=0, column=0, columnspan=3, sticky='ew')

        # Initialize other frames
        self.input_frame = InputView(self)
        self.frames['input'] = self.input_frame
        self.results_frame = ResultsView(self)
        self.frames['results'] = self.results_frame

        # Start with the input frame showing by default
        self.results_frame.grid_remove()
        self.input_frame.grid(row=1, column=1, sticky='nsew', padx=20, pady=10)

    def switch(self, name):
        if name == "input":
            self.show_input()
        elif name == "results":
            self.show_results()
        self.update_idletasks()

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

    def display_error(self, message):
        # Show an error message dialog
        messagebox.showerror("Error", message)
        print(f"Error: {message}")

    def start(self):
        self.mainloop()