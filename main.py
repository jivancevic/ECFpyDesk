from models.main import Model

import os
import platform

# Silence macOS system Tk deprecation warning (optional)
if platform.system() == "Darwin":
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

from views.main import View
from controllers.main import Controller

def main():
    app_directory = os.path.dirname(os.path.abspath(__file__))  # Get the directory of main.py
    # Initialize the MVC components
    model = Model()
    view = View()
    controller = Controller(model, view, app_directory)
    
    # Start the application
    controller.start()

if __name__ == "__main__":
    main()
