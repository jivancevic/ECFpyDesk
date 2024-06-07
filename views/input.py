import customtkinter as ctk
from tkinter import filedialog, StringVar, IntVar
import multiprocessing

class InputView(ctk.CTkFrame):
    FG_COLOR = "#008000"
    controller = None
    input_file_path = ""
    error_file_path = ""

    def __init__(self, parent):
        super().__init__(parent)
        self.max_threads = multiprocessing.cpu_count()
        self.search_metric = StringVar()
        self.train_test_split = StringVar()
        self.test_sample = StringVar()
        self.plot_y_axis_var = StringVar()
        self.plot_x_axis_var = StringVar()
        self.plot_scale_var = StringVar()

        self.initialize_ui()
    
    def initialize_ui(self):
        self.configure_grid()
        self.setup_file_section()
        self.setup_search_options()
        self.setup_function_scroll_area()
        self.setup_other_options_frame()
        self.setup_run_button()

    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1, uniform="Silent_Creme")
        self.grid_columnconfigure(1, weight=1, uniform="Silent_Creme")

    def setup_file_section(self):
        self.data_frame = ctk.CTkFrame(self)
        self.data_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        self.setup_file_widgets(self.data_frame)

    def setup_file_widgets(self, frame):
        self.input_file_button = self.create_file_button(frame, "Input file", 0)
        self.error_file_button = self.create_file_button(frame, "Error weights file", 1)

    def create_file_button(self, frame, text, row):
        ctk.CTkLabel(frame, text=text).grid(row=row, column=0, sticky='w', pady=5)
        button = ctk.CTkButton(frame, text="Select File", command=lambda bt=row: self.browse_file(bt))
        button.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        return button

    def setup_search_options(self):
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        self.add_search_options(self.search_frame)

    def add_search_options(self, frame):
        options = [
            ("search_metric", "Search metric", ["Mean squared error (MSE)", "Mean absolute error (MAE)", "Mean absolute percentage error (MAPE)"]),
            ("train_test_split", "Train/test split", ["No cross-validation", "50/50", "60/40", "70/30", "75/25", "80/20"]),
            ("test_sample", "Test sample", ["Chosen randomly", "Chosen sequentially"])
        ]
        for idx, option in enumerate(options):
            variable_name, label, choices = option
            self.setup_dropdown(frame, variable_name, label, choices, idx, self.on_option_change)

    def setup_function_scroll_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=300, height=150, scrollbar_fg_color=self.FG_COLOR, fg_color="#f0f0f0")
        self.scroll_frame.grid(row=2, column=1, sticky="ew", pady=5)
        self.populate_functions(self.scroll_frame)

    def populate_functions(self, frame):
        functions = [
            ("Addition", "+"), ("Subtraction", "-"), ("Multiplication", "*"), ("Division", "/"),
            ("Average", "avg"), ("Logarithm", "log"), ("Square root", "sqrt"), ("Minimum", "min"), ("Maximum", "max"), ("Position", "pos"),
            ("sin(x)", "sin"), ("cos(x)", "cos")
        ]

        self.checkbox_vars = {}
        for i, (label, func) in enumerate(functions):
            self.checkbox_vars[func] = ctk.CTkCheckBox(frame, text=label)
            self.checkbox_vars[func].grid(row=i, column=0, sticky='ew', pady=3, padx=5)
            self.checkbox_vars[func].select()

    def setup_other_options_frame(self):
        # Create the frame for other options
        self.other_options_frame = ctk.CTkFrame(self)
        self.other_options_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
        self.other_options_frame.grid_columnconfigure(1, weight=1)

        # Title label
        title_label = ctk.CTkLabel(self.other_options_frame, text="Other options")
        title_label.grid(row=0, column=0, columnspan=2, sticky="w")

        # Row 1: Number of threads
        self.setup_number_of_threads(self.other_options_frame, row=1)

        # Row 2: Plot y axis
        self.setup_dropdown(self.other_options_frame, "plot_y_axis_var", "Plot y axis", ["Target variable", "Xxx"], 2, self.on_option_change)

        # Row 3: Plot x axis
        self.setup_dropdown(self.other_options_frame, "plot_x_axis_var", "Plot x axis", ["Row number", "x1", "x2"], 3, self.on_option_change)

        # Row 4: Plot scale
        self.setup_dropdown(self.other_options_frame, "plot_scale_var", "Plot scale", ["Regular", "Xxx"], 4, self.on_option_change)

    def setup_number_of_threads(self, frame, row):
        label = ctk.CTkLabel(frame, text="Number of threads")
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

        # Thread count entry and buttons
        thread_frame = ctk.CTkFrame(frame)
        thread_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        for i, weight in enumerate([3,1,1]):
            thread_frame.grid_columnconfigure(i, weight=weight, uniform="Silent_Creme")

        thread_var = IntVar(value=1)
        entry = ctk.CTkEntry(thread_frame, textvariable=thread_var, width=120)
        entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        minus_button = ctk.CTkButton(thread_frame, text="-", command=lambda: self.change_number(thread_var, -1))
        minus_button.grid(row=0, column=1, padx=5)
        plus_button = ctk.CTkButton(thread_frame, text="+", command=lambda: self.change_number(thread_var, 1))
        plus_button.grid(row=0, column=2, padx=5)

    def setup_dropdown(self, frame, variable_name, label_text, options, row, callback):
        label = ctk.CTkLabel(frame, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)
        variable = getattr(self, variable_name)
        variable.set(options[0])  # Initialize with the first option
        callback(variable_name, variable.get())
        variable.trace_add('write', lambda *args, var=variable, name=variable_name: callback(name, var.get()))
        dropdown = ctk.CTkOptionMenu(frame, variable=variable, values=options)
        dropdown.grid(row=row, column=1, sticky="ew", padx=5, pady=5)

    def on_option_change(self, variable_name, value):
        setattr(self, variable_name, value)
        print(f"Option {variable_name} changed to {value}")

    def change_number(self, var, delta):
        new_value = min(max(1, var.get() + delta), self.max_threads)   # Prevent going below 1
        var.set(new_value)

    def setup_run_button(self):
        run_button = ctk.CTkButton(self, text="Run", command=self.on_run_button_click)
        run_button.grid(row=4, column=0, columnspan=2, sticky='ew', pady=5)

    def browse_file(self, button_type):
        filepath = filedialog.askopenfilename()
        if filepath:
            button = self.input_file_button if button_type == 0 else self.error_file_button
            button.configure(text=filepath.split('/')[-1])
            setattr(self, 'input_file_path' if button_type == 0 else 'error_file_path', filepath)

    def on_run_button_click(self):
        if self.controller:
            self.controller.on_run_button_click()

    def set_controller(self, controller):
        self.controller = controller