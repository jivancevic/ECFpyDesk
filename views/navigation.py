import customtkinter as ctk
from customtkinter import CTkImage
import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk

class NavigationView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None

        self.columnconfigure(0, weight=5, uniform="Silent_Creme")
        self.columnconfigure(1, weight=1, uniform="Silent_Creme")
        self.columnconfigure(2, weight=5, uniform="Silent_Creme")

        self.navigation_buttons_frame = ctk.CTkFrame(self)
        self.navigation_buttons_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=10)

        # Input button
        self.input_button = ctk.CTkButton(self.navigation_buttons_frame, text="Input", fg_color="#4CAF50")
        self.input_button.grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.input_button.configure(command=self.on_input_click)

        # Results button
        self.results_button = ctk.CTkButton(self.navigation_buttons_frame, text="Results", fg_color="#f0f0f0")
        self.results_button.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        self.results_button.configure(command=self.on_results_click)
        
        # Load icons or images for buttons
        icon_dimensions = 20
        self.start_icon = self.resize_image('resources/start.png', icon_dimensions)
        self.pause_icon = self.resize_image('resources/pause.png', icon_dimensions)

        # Toggle Button
        self.toggle_button = ctk.CTkButton(
            self, 
            text="", 
            width=icon_dimensions, 
            height=icon_dimensions, 
            image=self.start_icon, 
            command=self.on_toggle_process, 
            fg_color="transparent")
        
        self.toggle_button.grid(row=0, column=1)

    def set_controller(self, controller):
        self.controller = controller

    def on_input_click(self):
        if self.controller:
            self.controller.show_input()

    def on_results_click(self):
        if self.controller:
            self.controller.show_results()

    def on_toggle_process(self):
        if self.controller:
            self.controller.on_toggle_process_click()

    def set_toggle_icon(self, icon):
        if icon == "start":
            self.toggle_button.configure(image=self.start_icon)
        elif icon == "pause":
            self.toggle_button.configure(image=self.pause_icon)

    def resize_image(self, image_path, new_height):
        # Open an image file
        with Image.open(image_path) as img:
            # Calculate the new width maintaining the aspect ratio
            aspect_ratio = img.width / img.height
            new_width = int(new_height * aspect_ratio)

            # Resize the image
            img = img.resize((new_width, new_height), Image.ANTIALIAS)

            # Return a PhotoImage object
            return CTkImage(img)
