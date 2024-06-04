import customtkinter as ctk
from tkinter import filedialog

class InputView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None
        self.input_file_path = ""
        self.error_file_path = ""

        # Part 1: Input Frame for file handling
        self.data_frame = ctk.CTkFrame(self)
        self.data_frame.grid(row=0, column=1, sticky='ew', padx=20, pady=10)

        # Input file widgets
        ctk.CTkLabel(self.data_frame, text="Input file").grid(row=0, column=0, sticky='w', pady=5)
        self.input_file_button = ctk.CTkButton(self.data_frame, text="Select File", command=lambda: self.browse_file(self.input_file_button, 'input'))
        self.input_file_button.grid(row=0, column=1, sticky='ew', padx=10, pady=10)

        # Error weights file widgets
        ctk.CTkLabel(self.data_frame, text="Error weights file").grid(row=1, column=0, sticky='w', pady=5)
        self.error_file_button = ctk.CTkButton(self.data_frame, text="Select File", command=lambda: self.browse_file(self.error_file_button, 'error'))
        self.error_file_button.grid(row=1, column=1, sticky='ew', padx=10, pady=10)

        # Part 2: Search Options Frame
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=2, column=1, sticky='ew', padx=20, pady=10)

        # Search Metric
        ctk.CTkLabel(self.search_frame, text="Search metric").grid(row=0, column=0, sticky='w', pady=5)
        metric_var = ctk.StringVar(value="Mean squared error (MSE)")
        metric_options = ["Mean squared error (MSE)", "Mean absolute error (MAE)", "Mean absolute percentage error (MAPE)"]
        metric_dropdown = ctk.CTkOptionMenu(self.search_frame, variable=metric_var, values=metric_options)
        metric_dropdown.grid(row=0, column=1, sticky='ew')

        # Train/Test Split
        ctk.CTkLabel(self.search_frame, text="Train/test split").grid(row=1, column=0, sticky='w', pady=5)
        split_var = ctk.StringVar(value="50/50")
        split_options = ["50/50", "80/20", "100/0"]
        split_dropdown = ctk.CTkOptionMenu(self.search_frame, variable=split_var, values=split_options)
        split_dropdown.grid(row=1, column=1, sticky='ew')

        # Test Sample Selection
        ctk.CTkLabel(self.search_frame, text="Test sample").grid(row=2, column=0, sticky='w', pady=5)
        sample_var = ctk.StringVar(value="Chosen randomly")
        sample_options = ["Chosen randomly", "Chosen sequentially"]
        sample_dropdown = ctk.CTkOptionMenu(self.search_frame, variable=sample_var, values=sample_options)
        sample_dropdown.grid(row=2, column=1, sticky='ew')

        # Canvas for additional options
        function_scroll_frame = ctk.CTkScrollableFrame(self.search_frame, width=300, height=200, scrollbar_fg_color="#008000", fg_color="#f0f0f0")
        function_scroll_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        functions = [
            ("Addition", "+"), ("Multiplication", "*"), ("Division", "/"),
            ("sin(x)", "sin"), ("cos(x)", "cos")
        ]
        self.checkbox_vars = {}
        for i, (label, func) in enumerate(functions):
            #label_widget = ctk.CTkLabel(function_scroll_frame, text=label)
            #label_widget.grid(row=i, column=0, sticky='ew')
            self.checkbox_vars[func] = ctk.CTkCheckBox(function_scroll_frame, text=label)
            self.checkbox_vars[func].grid(row=i, column=0, sticky='ew', pady=3, padx=10)
        function_scroll_frame.update_idletasks()

        # Run button
        run_button = ctk.CTkButton(self.search_frame, text="Run", command=self.on_run_button_click)
        run_button.grid(row=4, column=0, columnspan=2, sticky='ew', pady=20)

    def set_controller(self, controller):
        self.controller = controller

    def browse_file(self, button, button_type):
        # Open file dialog and update button text and file path
        filepath = filedialog.askopenfilename()
        if filepath:  # Only update if a file was selected
            if button_type == 'input':
                self.input_file_path = filepath
                update_path = self.input_file_path
            elif button_type == 'error':
                self.error_file_path = filepath
                update_path = self.error_file_path

            button.configure(text=filepath.split('/')[-1])  # Display only the file name
            print(update_path, filepath.split('/')[-1])

    def on_run_button_click(self):
        if self.controller:
            self.controller.on_run_button_click()