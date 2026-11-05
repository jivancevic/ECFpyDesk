import customtkinter as ctk
from tkinter import StringVar
from utils.helper import initial_label
from utils.publisher import Publisher
from utils.tooltips import add_tooltip


class PillButton(ctk.CTkButton):
    """A button whose width follows its text (side padding included), up to `max_width`.

    Controllers change the label with `configure(text=...)`, for instance to a chosen file name,
    so the width is recomputed there instead of leaving a fixed-width button with clipped text.
    """
    def __init__(self, master, text="", side_pad=28, min_width=0, max_width=260, font=None, **kwargs):
        self._side_pad, self._min_width, self._max_width = side_pad, min_width, max_width
        self._measure_font = font or ctk.CTkFont(size=13)
        super().__init__(master, text=self._fit(text), width=self._width_for(text), font=self._measure_font, **kwargs)

    def _width_for(self, text):
        return min(self._max_width, max(self._min_width, self._measure_font.measure(text) + 2 * self._side_pad))

    def _fit(self, text):
        """Shorten the text with an ellipsis when it would not fit in `max_width`."""
        room = self._max_width - 2 * self._side_pad
        if self._measure_font.measure(text) <= room:
            return text
        while text and self._measure_font.measure(text + "...") > room:
            text = text[:-1]
        return text + "..."

    def configure(self, require_redraw=False, **kwargs):
        if "text" in kwargs:
            text = kwargs["text"]
            kwargs["width"] = self._width_for(text)
            kwargs["text"] = self._fit(text)
        super().configure(require_redraw=require_redraw, **kwargs)


class FilePicker(ctk.CTkFrame):
    """A fixed-size "Select File" button with the chosen file name in a label beside it.

    Controllers show the choice with `button.configure(text=file_name)`; `configure(text=)` here
    puts the name in the label and keeps the button's own text, so the button never changes size.
    """
    BUTTON_TEXT = "Select File"
    NAME_WIDTH = 150

    def __init__(self, master, command, tooltip_key, side_pad=28, height=48, font=None):
        super().__init__(master, fg_color="transparent")
        self._font = font or ctk.CTkFont(size=13)
        self._full_name = ""
        width = self._font.measure(self.BUTTON_TEXT) + 2 * side_pad
        self.button = ctk.CTkButton(self, text=self.BUTTON_TEXT, command=command, width=width, height=height,
                                    corner_radius=height // 2, font=self._font)
        self.button.grid(row=0, column=0)
        self.name_label = ctk.CTkLabel(self, text="", width=self.NAME_WIDTH, anchor="w", font=self._font)
        self.name_label.grid(row=0, column=1, padx=(8, 0))
        add_tooltip(self.button, tooltip_key)
        add_tooltip(self.name_label, lambda: self._full_name)

    def configure(self, require_redraw=False, **kwargs):
        if "text" in kwargs:
            self._full_name = kwargs.pop("text")
            self.name_label.configure(text=self._ellipsize(self._full_name))
        if kwargs:
            self.button.configure(**kwargs)

    def _ellipsize(self, text):
        room = self.NAME_WIDTH - 8
        if self._font.measure(text) <= room:
            return text
        while text and self._font.measure(text + "...") > room:
            text = text[:-1]
        return text + "..."


class BaseView(ctk.CTkFrame, Publisher):
    # Layout constants shared by all screens
    PAD = 8                 # space between widgets and around cards
    BUTTON_HEIGHT = 48      # buttons are content-width pills, at least this tall
    BUTTON_SIDE_PAD = 28    # horizontal padding inside a button, each side
    FIELD_HEIGHT = 36       # entries and dropdowns
    DROPDOWN_WIDTH = 300
    ENTRY_WIDTH = 140
    CARD_COLOR = "#e4e4e4"
    LIST_COLOR = "#f0f0f0"
    SCROLLBAR_COLOR = "#b8b8b8"   # the handle; the track is transparent, so it blends with its frame
    SCROLLBAR_HOVER = "#9a9a9a"

    def __init__(self, parent):
        ctk.CTkFrame.__init__(self, parent)
        Publisher.__init__(self)
        self.initial_values = {}  # controllers set this, by variable name, before building dropdowns
        self.font = ctk.CTkFont(family="Arial", size=14, weight="bold")
        self.button_font = ctk.CTkFont(size=13)

    def create_button(self, parent, text, command, min_width=0, tooltip=None, **kwargs):
        """A content-width button: side padding of BUTTON_SIDE_PAD, never stretched by the grid."""
        kwargs.setdefault("height", self.BUTTON_HEIGHT)
        kwargs.setdefault("corner_radius", self.BUTTON_HEIGHT // 2)
        button = PillButton(parent, text=text, command=command, side_pad=self.BUTTON_SIDE_PAD,
                            min_width=min_width, font=self.button_font, **kwargs)
        if tooltip:
            add_tooltip(button, tooltip)
        return button

    def setup_dropdown(self, frame, variable_name, label_text, choices, row, column=1):
        # Rebuilding a dropdown in the same place (e.g. the x axis after new data) replaces the old one.
        for old in frame.grid_slaves(row=row, column=0) + frame.grid_slaves(row=row, column=column):
            old.destroy()
        label = ctk.CTkLabel(frame, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=self.PAD, pady=self.PAD // 2)
        display_var = StringVar()
        display_var.trace_add('write', lambda *args: self.invoke_callback('dropdown_option_change', variable_name, label_to_value_map[display_var.get()]))
        label_to_value_map = {label: value for label, value in choices}
        dropdown_labels = list(label_to_value_map.keys())
        display_var.set(initial_label(choices, self.initial_values.get(variable_name)))
        dropdown = ctk.CTkOptionMenu(frame, variable=display_var, values=dropdown_labels,
                                     width=self.DROPDOWN_WIDTH, height=self.FIELD_HEIGHT, dynamic_resizing=False)
        dropdown.grid(row=row, column=column, sticky="w", padx=self.PAD, pady=self.PAD // 2)
        add_tooltip(label, variable_name)
        add_tooltip(dropdown, variable_name)
