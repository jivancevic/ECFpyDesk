import customtkinter as ctk
from utils.image import resize_image
from .base import BaseView

class NavigationView(BaseView):
    def __init__(self, parent):
        super().__init__(parent)
        self.initialize_ui()

    def initialize_ui(self):
        self.configure_grid()
        self.setup_navigation_buttons_frame()
        self.setup_process_buttons()

    def configure_grid(self):
        weights = [10, 1, 1, 10]
        for i, weight in enumerate(weights):
            self.columnconfigure(i, weight=weight, uniform="Silent_Creme")

    def setup_navigation_buttons_frame(self):
        self.navigation_buttons_frame = ctk.CTkFrame(self)
        self.navigation_buttons_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=10)

        # Input button
        self.input_button = ctk.CTkButton(self.navigation_buttons_frame, text="Input", fg_color="#4CAF50")
        self.input_button.grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.input_button.configure(command=lambda *args: self.invoke_callback('input_button_click'))

        # Results button
        self.results_button = ctk.CTkButton(self.navigation_buttons_frame, text="Results", fg_color="#f0f0f0")
        self.results_button.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        self.results_button.configure(command=lambda *args: self.invoke_callback('results_button_click'))
        
    def setup_process_buttons(self):
        # Load icons or images for buttons
        icon_dimensions = 20
        self.start_icon = resize_image('resources/start.png', icon_dimensions)
        self.pause_icon = resize_image('resources/pause.png', icon_dimensions)
        self.stop_icon = resize_image('resources/stop.png', icon_dimensions)
        self.stop_grey_icon = resize_image('resources/stop_grey.png', icon_dimensions)

        # Toggle Button
        self.toggle_process_button = ctk.CTkButton(
            self, 
            text="", 
            width=icon_dimensions, 
            height=icon_dimensions, 
            image=self.start_icon, 
            command=lambda *args: self.invoke_callback('toggle_process_button_click'), 
            fg_color="transparent")
        
        self.toggle_process_button.grid(row=0, column=1)

        # Stop Button
        self.stop_process_button = ctk.CTkButton(
            self, 
            text="", 
            width=icon_dimensions, 
            height=icon_dimensions, 
            image=self.stop_grey_icon, 
            command=lambda *args: self.invoke_callback('stop_process_button_click'),
            state="disabled", 
            fg_color="transparent")
        
        self.stop_process_button.grid(row=0, column=2)

    def switch_toggle_process_button_icon(self):
        if self.toggle_process_button.cget("image") == self.start_icon:
            self.set_toggle_process_button_icon("pause")
        elif self.toggle_process_button.cget("image") == self.pause_icon:
            self.set_toggle_process_button_icon("pause")

    def switch_stop_process_button_icon(self):
        if self.stop_process_button.cget("image") == self.stop_icon:
            self.set_stop_process_button_icon(False)
        elif self.stop_process_button.cget("image") == self.stop_grey_icon:
            self.set_stop_process_button_icon(True)

    def set_toggle_process_button_icon(self, icon: str):
        if icon == "start":
            self.toggle_process_button.configure(image=self.start_icon)
        elif icon == "pause":
            self.toggle_process_button.configure(image=self.pause_icon)

    def set_stop_process_button_icon(self, enable: bool):
        if enable:
            self.stop_process_button.configure(image=self.stop_icon)
            self.stop_process_button.configure(state="normal")
        else:
            self.stop_process_button.configure(image=self.stop_grey_icon)
            self.stop_process_button.configure(state="disabled")
