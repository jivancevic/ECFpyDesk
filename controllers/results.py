import logging
import numpy as np
from utils.helper import find_index_of_dict_with_value_in_array
from utils.parameters import plot_options
from .base import BaseController

logger = logging.getLogger(__name__)

class ResultsController(BaseController):
    def __init__(self, model, controller, view):
        super().__init__(model, controller, view, view.frames["results"])
        self.test_option = False
        self.register_callbacks()

    def initialize_frame(self):
        super().initialize_frame()
        self.update_plot()

    def register_callbacks(self):
        self.frame.register_callback('move_selection', self.move_selection)
        self.frame.register_callback('select_row', self.select_row)
        self.frame.register_callback('update_plot', self.update_plot)
        self.frame.register_callback('show_test_data', self.handle_show_test_data)
        self.frame.register_callback('dropdown_option_change', self.handle_dropdown_option_change)

    def move_selection(self, direction):
        if self.frame.current_active_row is None:
            return
        if direction == "up" and self.frame.current_active_row > 0:
            self.select_row(self.frame.current_active_row - 1)
        elif direction == "down" and self.frame.current_active_row < len(self.frame.solutions_list_frame.winfo_children()) // 3 - 1:
            self.select_row(self.frame.current_active_row + 1)

    def select_row(self, row):
        if row != self.frame.current_active_row:
            self.frame.current_active_row = row
            self.select_active_row()
            self.frame.solutions_list_frame.focus_set()

    def select_active_row(self):
        row = self.frame.current_active_row
        function = self.model.best_functions[row]["function"]
        error = self.model.best_functions[row]["error"]
        
        self.frame.update_info(function, error)
        self.update_plot(function)
        self.frame.reset_row_colors()
        self.frame.set_active_row_color(row)

    def update_plot(self, function=None, data_type=None):
        if data_type is None:
            data_type = self.model.get_data_type()

        x_data, y_data = self.model.get_plot_data(data_type)
        plot_scale = self.model.plot_scale
        plot_y_index = self.model.plot_y_index
        plot_type = self.model.plot_type
        
        if x_data is None or y_data is None:
            return

        multivar = self.model.is_multivar()

        try:
            if function:
                x_values, function_results = self.controller.evaluate_function(function, multivar, data_type=data_type)
                if plot_type == "plot" and function_results is not None:
                    # A line joins the points in order, and the rows of a train set are shuffled
                    order = np.argsort(x_data, kind="stable")
                    x_data, y_data, function_results = np.take(x_data, order), np.take(y_data, order), np.take(function_results, order)
                self.frame.update_plot(x_data, y_data, x_values, function_results, multivar, plot_scale=plot_scale, plot_y_index=plot_y_index, plot_type=plot_type)
            else:
                self.frame.update_plot(x_data, y_data, plot_scale=plot_scale, plot_y_index=plot_y_index, plot_type=plot_type)
        except Exception as e:
            logger.error(f"Error evaluating function '{function}': {e}")
            self.view.display_error(f"Error evaluating function '{function}': {e}")

    def update_solutions_frame(self, best_functions):
        shown_functions = self.frame.best_functions
        if shown_functions == best_functions:
            return

        active_row = self.frame.current_active_row
        active_function = shown_functions[active_row]["function"] if active_row is not None else None

        for i, func in enumerate(best_functions):
            if i >= len(shown_functions):
                self.frame.create_solution_row(func, i)
            elif func != shown_functions[i]:
                self.frame.update_solution_row(func, i)
        for i in range(len(best_functions), len(shown_functions)):
            self.frame.destroy_solution_row(i)

        self.frame.best_functions = best_functions

        if not best_functions:
            self.frame.current_active_row = None
            return

        # The selection stays on its function, which may have moved or left the front
        new_row = find_index_of_dict_with_value_in_array(best_functions, "function", active_function)
        if new_row == -1:
            new_row = 0 if active_row is None else min(active_row, len(best_functions) - 1)
        self.frame.current_active_row = new_row
        self.select_active_row()

    def clear_frame(self):
        self.frame.clear_frame()
        self.update_plot()

    def handle_show_test_data(self, should_show):
        data_type = 'test' if should_show else 'train'
        self.model.data_type = data_type
        self.controller.update_solutions_frame()
        if self.frame.current_active_row is None:
            self.update_plot()
        else:
            self.select_active_row()

    def handle_dropdown_option_change(self, variable_name, value):
        self.model.set_variable(variable_name, value)
        function = None
        if self.frame.current_active_row is not None:
            function = self.model.best_functions[self.frame.current_active_row]["function"]
        self.update_plot(function)

    def update_plot_x_axis(self, var_num):
        # The plot options sit below the test data checkbox when there is one
        start_row = 3 if self.test_option else 2
        for idx, option in enumerate(plot_options):
            variable_name, label, choices = option
            if variable_name == "plot_x_index":
                choices = [("Row number", -1)] + [(f"x{i+1}", i) for i in range(var_num)]
                self.frame.setup_dropdown(self.frame.info_frame, variable_name, label, choices, idx+start_row, 1)

    def add_test_option(self, should_add=False):
        self.test_option = should_add
        self.frame.info_frame.destroy()
        self.frame.setup_info_frame(test_option=should_add)
        self.update_plot_x_axis(len(self.model.input_data) - 1)
