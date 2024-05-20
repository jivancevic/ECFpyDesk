import customtkinter as ctk
from tkinter import filedialog

class InputView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None
        self.input_file_entry_var = ctk.StringVar()
        self.error_file_entry_var = ctk.StringVar()

        # Part 1: Input Frame for file handling
        data_frame = ctk.CTkFrame(self)
        data_frame.grid(row=0, column=1, sticky='ew', padx=20, pady=10)

        # Input file widgets
        ctk.CTkLabel(data_frame, text="Input file").grid(row=0, column=0, sticky='w', pady=5)
        self.input_file_entry = ctk.CTkEntry(data_frame, textvariable=self.input_file_entry_var, width=40)
        self.input_file_entry.grid(row=0, column=1, sticky='ew')
        ctk.CTkButton(data_frame, text="Browse", command=lambda: self.browse_file(self.input_file_entry)).grid(row=0, column=2, padx=10)

        # Error weights file widgets
        ctk.CTkLabel(data_frame, text="Error weights file").grid(row=1, column=0, sticky='w', pady=5)
        self.error_file_entry = ctk.CTkEntry(data_frame, textvariable=self.error_file_entry_var, width=40)
        self.error_file_entry.grid(row=1, column=1, sticky='ew')
        ctk.CTkButton(data_frame, text="Browse", command=lambda: self.browse_file(self.error_file_entry)).grid(row=1, column=2, padx=10)

        # Part 2: Search Options Frame
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=2, column=1, sticky='ew', padx=20, pady=10)

        # Search Metric
        ctk.CTkLabel(search_frame, text="Search metric").grid(row=0, column=0, sticky='w', pady=5)
        metric_var = ctk.StringVar(value="Mean squared error (MSE)")
        metric_options = ["Mean squared error (MSE)", "Mean absolute error (MAE)", "Mean absolute percentage error (MAPE)"]
        metric_dropdown = ctk.CTkOptionMenu(search_frame, variable=metric_var, values=metric_options)
        metric_dropdown.grid(row=0, column=1, sticky='ew')

        # Train/Test Split
        ctk.CTkLabel(search_frame, text="Train/test split").grid(row=1, column=0, sticky='w', pady=5)
        split_var = ctk.StringVar(value="50/50")
        split_options = ["50/50", "80/20", "100/0"]
        split_dropdown = ctk.CTkOptionMenu(search_frame, variable=split_var, values=split_options)
        split_dropdown.grid(row=1, column=1, sticky='ew')

        # Test Sample Selection
        ctk.CTkLabel(search_frame, text="Test sample").grid(row=2, column=0, sticky='w', pady=5)
        sample_var = ctk.StringVar(value="Chosen randomly")
        sample_options = ["Chosen randomly", "Chosen sequentially"]
        sample_dropdown = ctk.CTkOptionMenu(search_frame, variable=sample_var, values=sample_options)
        sample_dropdown.grid(row=2, column=1, sticky='ew')

        # Canvas for additional options
        function_scroll_frame = ctk.CTkScrollableFrame(search_frame, width=300, height=200, scrollbar_fg_color="#008000", fg_color="#f0f0f0")
        function_scroll_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        functions = [
            ("Addition", "+"), ("Multiplication", "*"), ("Division", "/"),
            ("sin(x)", "sin"), ("cos(x)", "cos")
        ]
        checkbox_vars = {}
        for i, (label, func) in enumerate(functions):
            label_widget = ctk.CTkLabel(function_scroll_frame, text=label)
            label_widget.grid(row=i, column=0, sticky='ew')
            checkbox_vars[func] = ctk.CTkCheckBox(function_scroll_frame)
            checkbox_vars[func].grid(row=i, column=1, sticky='e')

        function_scroll_frame.update_idletasks()

        

    def set_controller(self, controller):
        self.controller = controller

    def browse_file(self, entry=None):
        entry = entry if entry else self.input_file_entry
        filepath = filedialog.askopenfilename()
        entry.set(filepath)
