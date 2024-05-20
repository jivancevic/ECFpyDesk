import customtkinter as ctk

class NavigationView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Input button
        self.input_button = ctk.CTkButton(self, text="Input", fg_color="#4CAF50")
        self.input_button.grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.input_button.configure(command=self.on_input_click)

        # Results button
        self.results_button = ctk.CTkButton(self, text="Results", fg_color="#f0f0f0")
        self.results_button.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        self.results_button.configure(command=self.on_results_click)

    def set_controller(self, controller):
        self.controller = controller

    def on_input_click(self):
        if self.controller:
            self.controller.show_input()

    def on_results_click(self):
        if self.controller:
            self.controller.show_results()
