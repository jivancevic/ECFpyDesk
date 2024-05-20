import customtkinter as ctk

class ResultsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None

        # Results frame setup
        ctk.CTkLabel(self, text="Hello World").pack(pady=20)

    def set_controller(self, controller):
        self.controller = controller