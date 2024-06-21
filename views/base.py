import customtkinter as ctk
from utils.publisher import Publisher

class BaseView(ctk.CTkFrame, Publisher):
    def __init__(self, parent):
        ctk.CTkFrame.__init__(self, parent)
        Publisher.__init__(self)