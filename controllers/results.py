from .base import BaseController

class ResultsController(BaseController):
    def __init__(self, model, controller, view):
        super().__init__(model, controller, view, view.frames["results"])
        self.register_callbacks()

    def initialize_frame(self):
        super().initialize_frame()
        self.update_plot()

    def register_callbacks(self):
        self.frame.register_callback('move_selection', self.move_selection)
        self.frame.register_callback('select_row', self.select_row)
        self.frame.register_callback('update_plot', self.update_plot)
        self.frame.register_callback('dropdown_option_change', self.handle_dropdown_option_change)

    def move_selection(self, direction):
        if direction == "up" and self.frame.current_active_row > 0:
            self.select_row(self.frame.current_active_row - 1)
        elif direction == "down" and self.frame.current_active_row < len(self.frame.solutions_list_frame.winfo_children()) // 3 - 1:
            self.select_row(self.frame.current_active_row + 1)

    def select_row(self, row):
        if row != self.frame.current_active_row:
            self.frame.current_active_row = row
            function = self.model.best_functions[row]["function"]
            error = self.model.best_functions[row]["error"]
            
            self.frame.update_info(function, error)
            self.update_plot(function)
            self.frame.solutions_list_frame.focus_set()
            self.frame.reset_row_colors()
            self.frame.set_active_row_color(row)

    def update_plot(self, function=None):
        x_data, y_data = self.model.get_plot_data()
        
        if x_data is None or y_data is None:
            return

        multivar = self.model.is_multivar()

        try:
            if function:
                x_values, function_results = self.controller.evaluate_function(function, multivar)
                self.frame.update_plot(x_data, y_data, x_values, function_results, multivar)
            else:
                self.frame.update_plot(x_data, y_data)
        except Exception as e:
            self.view.display_error(f"Error evaluating function '{function}': {e}")

    def update_solutions_frame(self, best_functions):
        if self.frame.best_functions == best_functions:
            return

        for i, func in enumerate(best_functions):
            if i < len(self.frame.best_functions):
                if func["function"] != self.frame.best_functions[i]["function"]:
                    self.frame.update_solution_row(func, i)
                    if self.frame.current_active_row is not None and self.frame.current_active_row == i:
                        self.select_row(i)
            else:
                self.frame.create_solution_row(func, i)
                if self.frame.current_active_row is None and i == 0:
                    self.select_row(i)

        if len(best_functions) < len(self.frame.best_functions):
            for i in range(len(best_functions), len(self.frame.best_functions)):
                self.frame.destroy_solution_row(i)

        self.frame.best_functions = best_functions

    def clear_frame(self):
        self.frame.clear_frame()
        self.update_plot()

    def handle_dropdown_option_change(self, variable_name, value):
        self.model.set_variable(variable_name, value)
        function = None
        if self.frame.current_active_row is not None:
            function = self.model.best_functions[self.frame.current_active_row]["function"]
        self.update_plot(function)

    def add_test_option(self, should_add=False):
        print("Adding test option")
        self.frame.setup_info_frame(test_option=should_add)
