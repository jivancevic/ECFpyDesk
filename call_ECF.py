import subprocess
import os
import json

def call_ECF(input_file_path="", error_weights_file_path="", error_metric="MSE", terminal_entry=""):
    
    # Open the JSON file for reading
    with open('config.json', 'r') as file:
        # Load its content and turn it into a Python dictionary
        config = json.load(file)

    # Run the executable
    subprocess.call([config["SRM_path"], config["SRM_config_path"]])

    # Change back to the current directory
    os.chdir(os.path.dirname(__file__))
