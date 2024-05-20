from models.main import Model
from views.main import View
from controllers.main import Controller

def main():
    # Initialize the MVC components
    model = Model()
    view = View()
    controller = Controller(model, view)
    view.set_controller(controller)
    
    # Start the application
    controller.start()

if __name__ == "__main__":
    main()
