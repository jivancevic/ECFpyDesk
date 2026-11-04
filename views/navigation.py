import customtkinter as ctk
from utils.image import resize_image
from utils.tooltips import add_tooltip, tooltip_text
from .base import BaseView

class NavigationView(BaseView):
    def __init__(self, parent):
        super().__init__(parent)
        self.initialize_ui()

    def initialize_ui(self):
        self.configure_grid()
        self.setup_navigation_buttons_frame()
        self.setup_process_buttons()

    ACTIVE_COLOR = "#4CAF50"
    INACTIVE_COLOR = "#d6d6d6"
    ACTIVE_TEXT = "#ffffff"
    INACTIVE_TEXT = "#222222"
    TAB_WIDTH = 140

    def configure_grid(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)   # spacer: tabs on the left, run controls on the right

    def setup_navigation_buttons_frame(self):
        self.navigation_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.navigation_buttons_frame.grid(row=0, column=0, sticky='w', padx=(20, 0), pady=self.PAD)

        # Input button
        self.input_button = self.create_button(
            self.navigation_buttons_frame, "Input", lambda *args: self.invoke_callback('input_button_click'),
            min_width=self.TAB_WIDTH, tooltip="nav_input")
        self.input_button.grid(row=0, column=0, padx=(0, self.PAD))

        # Results button
        self.results_button = self.create_button(
            self.navigation_buttons_frame, "Results", lambda *args: self.invoke_callback('results_button_click'),
            min_width=self.TAB_WIDTH, tooltip="nav_results")
        self.results_button.grid(row=0, column=1)

        self.set_active_tab("input")

    def set_active_tab(self, name):
        """Colour the tab of the visible screen ('input' or 'results')."""
        for tab, button in (("input", self.input_button), ("results", self.results_button)):
            active = tab == name
            button.configure(fg_color=self.ACTIVE_COLOR if active else self.INACTIVE_COLOR,
                             text_color=self.ACTIVE_TEXT if active else self.INACTIVE_TEXT,
                             hover_color="#3e8e41" if active else "#c4c4c4")

    def setup_process_buttons(self):
        # Load icons or images for buttons
        icon_dimensions = 24
        self.start_icon = resize_image('resources/start.png', icon_dimensions)
        self.pause_icon = resize_image('resources/pause.png', icon_dimensions)
        self.stop_icon = resize_image('resources/stop.png', icon_dimensions)
        self.stop_grey_icon = resize_image('resources/stop_grey.png', icon_dimensions)

        process_frame = ctk.CTkFrame(self, fg_color="transparent")
        process_frame.grid(row=0, column=2, sticky='e', padx=(0, 20), pady=self.PAD)

        # Toggle Button
        self.toggle_process_button = ctk.CTkButton(
            process_frame,
            text="",
            width=self.BUTTON_HEIGHT,
            height=self.BUTTON_HEIGHT,
            image=self.start_icon,
            command=lambda *args: self.invoke_callback('toggle_process_button_click'),
            fg_color="transparent",
            hover_color="#d6d6d6")
        self.toggle_process_button.grid(row=0, column=0, padx=(0, self.PAD))
        add_tooltip(self.toggle_process_button,
                    lambda: tooltip_text("toggle_pause" if self.toggle_process_button.cget("image") == self.pause_icon else "toggle_start"))

        # Stop Button
        self.stop_process_button = ctk.CTkButton(
            process_frame,
            text="",
            width=self.BUTTON_HEIGHT,
            height=self.BUTTON_HEIGHT,
            image=self.stop_grey_icon,
            command=lambda *args: self.invoke_callback('stop_process_button_click'),
            state="disabled",
            fg_color="transparent",
            hover_color="#d6d6d6")
        self.stop_process_button.grid(row=0, column=1)
        add_tooltip(self.stop_process_button, "stop")

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
