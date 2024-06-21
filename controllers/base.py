class BaseController:
    def __init__(self, model, controller, view, frame):
        self.model = model
        self.controller = controller
        self.view = view
        self.frame = frame

    def initialize_frame(self):
        self.frame.initialize_ui()