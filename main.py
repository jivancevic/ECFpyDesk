from models.main import Model

import logging
import os
import platform
import sys

# Silence macOS system Tk deprecation warning (optional)
if platform.system() == "Darwin":
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

from views.main import View
from controllers.main import Controller

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        from utils.self_test import run
        sys.exit(run(sys.argv[2]))

    # Initialize the MVC components
    model = Model()
    view = View()
    controller = Controller(model, view)
    
    # Start the application
    controller.start()

if __name__ == "__main__":
    main()
