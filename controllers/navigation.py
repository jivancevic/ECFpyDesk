from .base import BaseController

class NavigationController(BaseController):
    def __init__(self, model, controller, view):
        super().__init__(model, controller, view, view.frames["navigation"])
        self.register_callbacks()

    def register_callbacks(self):
        self.frame.register_callback('input_button_click', self.on_input_button_click)
        self.frame.register_callback('results_button_click', self.on_results_button_click)
        self.frame.register_callback('toggle_process_button_click', self.on_toggle_process_button_click)
        self.frame.register_callback('stop_process_button_click', self.on_stop_process_button_click)

    def on_input_button_click(self):
        self.view.switch("input")

    def on_results_button_click(self):
        self.view.switch("results")

    def on_toggle_process_button_click(self):
        self.view.switch("results")
        self.frame.switch_toggle_process_button_icon()
        self.controller.handle_toggle_process()

    def on_stop_process_button_click(self):
        self.frame.switch_stop_process_button_icon()
        self.controller.handle_stop_process()

    def set_toggle_process_button_icon(self, icon: str):
        self.frame.set_toggle_process_button_icon(icon)

    def set_stop_process_button_icon(self, enable: bool): 
        self.frame.set_stop_process_button_icon(enable)