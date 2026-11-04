"""Hover tooltips: the text for every input element, and the small class that shows it.

Keys are the names the views already use: the option variable names from
`utils/parameters.py`, the registry paths of the parameter fields, the function
symbols, and a few names for the fixed widgets.
"""
import tkinter as tk

TOOLTIPS = {
    # Input options
    "input_file": "Tab-separated data file. One row per sample, the last column is the target.\nPick the file first: the variables below are read from it.",
    "error_file": "Optional file with a weight for each sample's error.\nLeave it unset to weigh all samples equally.",
    "variables": "Input variables (columns of the input file) the expressions may use.\nTick the ones that matter; fewer variables make the search easier.",
    "all_none": "Select all input variables, or clear the selection if all are already selected.",
    "terminal_set": "Constants the expressions may use besides the ticked variables.\nA range such as [-1 1] means random constants between -1 and 1.",
    # Search options
    "search_metric": "Error measure that ranks the expressions.\nMSE punishes big misses, MAE is robust to outliers, MAPE is relative (avoid targets near 0).",
    "train_test_split": "Share of the rows used for training, the rest forms the test set.\n'No cross-validation' trains on all rows. 70/30 or 80/20 are usual.",
    "test_sample": "How the test rows are picked: at random, or in file order.\nUse random unless the rows are already shuffled.",
    # Other options
    "thread_num": "Number of SRM processes that run at the same time.\nSensible: up to the number of CPU cores (the + button stops there).",
    "linear_scaling": "Fits a scale and an offset to each expression's output before measuring the error.\nUsually best left on.",
    # Registry parameters
    "ECF/Registry/Entry/term.maxgen": "Generation limit of one SRM run (term.stagnation and term.eval also end it).\nA process starts a new run until you press Stop. Sensible: 100 to 1000.",
    "ECF/Registry/Entry/population.size": "Expressions in the population of each process.\nSensible: 500 to 5000. Larger finds more but runs slower.",
    "ECF/Registry/Entry/mutation.indprob": "Chance that an expression is mutated, from 0 to 1.\nSensible: 0.3 to 0.9.",
    "ECF/Registry/Entry/log.frequency": "Every this many generations the best expression is written out and shown on the Results screen.\nMust be above 0.",
    # Action buttons
    "apply": "Save these settings as the defaults for the next start.\nA run always uses what is on screen.",
    "apply_edit": "Save the text below as the parameter file.",
    "change": "Edit the parameter file as plain XML, for options this screen does not list.",
    "change_back": "Leave the XML editor and return to the settings.",
    "config_editor": "The parameter file as XML. Press Save to keep the changes.",
    # Navigation
    "nav_input": "Set up the data, functions and parameters.",
    "nav_results": "See the best expressions found so far and plot them.",
    "toggle_start": "Start a run, or continue a paused one.",
    "toggle_pause": "Pause the run. It can be continued from here.",
    "stop": "Stop the run. Available only while a run is active.",
    # Results
    "solutions": "The best expressions found by all processes, by size and error.\nClick a row, or use the up and down keys, to plot it.",
    "show_test_data": "Plot the test set instead of the train set.",
    "plot_y_index": "What the y axis shows: the target and the function, the signed residual (data minus function),\nor the absolute residual in percent.",
    "plot_x_index": "What the x axis shows: the row number, or one of the input variables.",
    "plot_type": "Draw the points as a scatter plot or joined by a line.",
    "plot_scale": "Use a logarithmic scale on one or both axes.\nLog scales need positive values.",
}

# Function set checkboxes, keyed by the symbol SRM uses.
TOOLTIPS.update({
    "+": "Addition of two values.",
    "-": "Subtraction of two values.",
    "*": "Multiplication of two values.",
    "/": "Protected division: 1 if the divisor is close to 0.",
    "avg": "Average of two values.",
    "log": "Base-10 logarithm; 0 if the value is not positive.",
    "sqrt": "Square root; 0 for values of 0 or below.",
    "min": "Smaller of two values.",
    "max": "Larger of two values.",
    "pos": "Positive part: the value if it is above 0, otherwise 0.",
    "sin": "Sine.",
    "cos": "Cosine.",
})


def tooltip_text(key):
    return TOOLTIPS.get(key, "")


class Tooltip:
    """Shows `text` in a small window under `widget` after the pointer rests on it.

    `text` may be a string or a function returning one, for widgets whose meaning changes.
    """
    DELAY_MS = 600
    BG = "#fffbe6"
    FG = "#222222"

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._after_id = None
        self._window = None
        for event, handler in (("<Enter>", self._schedule), ("<Leave>", self._hide),
                               ("<ButtonPress>", self._hide), ("<Destroy>", self._hide),
                               ("<Unmap>", self._hide), ("<FocusOut>", self._hide)):
            widget.bind(event, handler, add="+")

    def _current_text(self):
        return self.text() if callable(self.text) else self.text

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.DELAY_MS, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self):
        self._after_id = None
        text = self._current_text()
        if not text or self._window is not None or not self.widget.winfo_exists() or not self._pointer_inside():
            return
        window = tk.Toplevel(self.widget.winfo_toplevel())  # not a child of the widget: containers list their children
        window.wm_overrideredirect(True)
        try:
            window.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        tk.Label(window, text=text, justify="left", bg=self.BG, fg=self.FG, relief="solid",
                 borderwidth=1, padx=8, pady=5, wraplength=360, font=("Arial", 11)).pack()
        window.update_idletasks()
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        # Keep the tip on screen: flip above the widget near the bottom, shift left near the right edge.
        if y + window.winfo_reqheight() > self.widget.winfo_screenheight():
            y = self.widget.winfo_rooty() - window.winfo_reqheight() - 6
        x = max(0, min(x, self.widget.winfo_screenwidth() - window.winfo_reqwidth() - 4))
        window.wm_geometry(f"+{x}+{y}")
        self._window = window

    def _pointer_inside(self):
        px, py = self.widget.winfo_pointerxy()
        x, y = self.widget.winfo_rootx(), self.widget.winfo_rooty()
        return x <= px < x + self.widget.winfo_width() and y <= py < y + self.widget.winfo_height()

    def _hide(self, _event=None):
        self._cancel()
        if self._window is not None:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
            self._window = None


def add_tooltip(widget, key_or_text):
    """Attach a tooltip. `key_or_text` is a key of TOOLTIPS, or a function returning text.

    Returns the widget so it can be used inline. A key with no text attaches nothing.
    """
    if callable(key_or_text):
        Tooltip(widget, key_or_text)
    else:
        text = tooltip_text(key_or_text)
        if text:
            Tooltip(widget, text)
    return widget
