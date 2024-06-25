import xml.etree.ElementTree as ET
import copy
import pandas as pd
import shutil
from sklearn.model_selection import train_test_split
from utils.file import delete_file_if_exists

class ProcessConfiguration:
    def __init__(self, parameters_path, input_file_path, best_file_path, log_file_path=None, tree=None, root=None):
        self.parameters_path = parameters_path
        self.input_file_path = input_file_path
        self.best_file_path = best_file_path
        self.log_file_path = log_file_path
        self.tree = tree
        self.root = root

class ConfigurationManager:
    tree = None
    root = None

    def __init__(self, default_parameters_path):
        self.default_parameters_path = default_parameters_path
        self.configurations = {}  # Stores ET trees for different processes
        self.test_configurations = {} # Stores ET trees for different test processes

    def set_tree_and_root(self):
        self.tree, self.root = self.parse_XML(self.default_parameters_path)

    def create_config(self, process_id, parameters_path, input_file_path, best_file_path, log_file_path, is_test=False):
        tree, root = self.parse_XML(self.default_parameters_path)
        
        process_config = ProcessConfiguration(parameters_path=parameters_path, input_file_path=input_file_path, best_file_path=best_file_path, log_file_path=log_file_path, tree=tree, root=root)
        self.create_parameters_file(process_config, is_test)

        if not is_test:
            self.configurations[process_id] = process_config
        else:
            self.test_configurations[process_id] = process_config

    def create_parameters_file(self, config, is_test=False):
        self.set_param_element("ECF/Registry/Entry/input_file", config.input_file_path, config.tree)
        self.set_param_element("ECF/Registry/Entry/bestfile", config.best_file_path, config.tree)
        self.set_param_element("ECF/Registry/Entry/log.filename", config.log_file_path, config.tree)
        if is_test:
            self.set_param_element("ECF/Registry/Entry/linear_scaling", "false", config.tree)

        self.write_config(config.tree, config.parameters_path)

        return True

    def parse_XML(self, parameters_path):
        with open(parameters_path) as f:
            tree = ET.ElementTree(file=f)
        root = tree.getroot()
        return tree, root
    
    def write_config(self, tree, file_path):
        ET.indent(tree, space="\t", level=0)
        print(f"Writing to file: {file_path}")
        tree.write(file_path)

    def update_config(self, params, process_id=None, is_test=False):
        if process_id is None:
            tree = self.tree
            parameters_path = self.default_parameters_path
        elif not is_test:
            config = self.configurations[process_id]
            tree = config.tree
            parameters_path = config.parameters_path
        else:
            print(f"Updating test configuration for process {process_id}")
            config = self.test_configurations[process_id]
            tree = config.tree
            parameters_path = config.parameters_path
        for path, value in params.items():
            if value is not None and value != "":
                print(f"Setting parameter {path} to {value}")
                self.set_param_element(path, value, tree)

        self.write_config(tree, parameters_path)

    def get_current_function_set(self):
        return self.get_current_param_value("ECF/Genotype/Entry/functionset")
    
    def get_current_terminal_set(self):
        return self.get_current_param_value("ECF/Genotype/Entry/terminalset")
    
    def get_current_param_value(self, path):
        # Load the XML tree from a file or an existing in-memory object
        if self.tree is None:
            self.set_tree_and_root()

        target_element = self.find_param_element(path, self.tree)

        if target_element is not None:
            return target_element.text  # Return the text content of the element
        return None  # If the element with the key doesn't exist, return None
    
    def set_param_element(self, path, value, tree):
        target_element = self.find_param_element(path, tree)
        if target_element is not None:
            target_element.text = value
        else:
            # If the parameter doesn't exist, consider creating it
            self.add_param_element(path, value, tree)
    
    def find_param_element(self, path, tree=None):
        # Split the path by slashes to navigate through the nodes
        elements = path.split('/')

        if tree is None:
            tree = self.tree
        root = tree.getroot()

        current_element = root

        # Navigate through the tree to find the target element
        for element in elements[1:-2]:  # Ignore the last segment because it's the attribute key
            current_element = current_element.find(f".//{element}")
            if current_element is None:
                return None  # If the path is invalid at any point, return None

        # The last part of the path should be the key of the attribute you are looking for
        entry = elements[-2]
        key = elements[-1]
        target_element = current_element.find(f".//{entry}[@key='{key}']")  # Find the element with the specified key

        return target_element

    def add_param_element(self, path, value, tree=None):
        if tree is None:
            tree = self.tree
        root = tree.getroot()

        try:
            # Assume self.root is already an ElementTree object of the loaded XML
            elements = path.split('/')
            parent_path = "/".join(elements[1:-2])  # Get the path to the parent node
            entry = elements[-2]
            key = elements[-1]

            # Navigate to the parent element
            parent = root.find(parent_path)
            if parent is None:
                print(f"Could not find the parent path: {parent_path}")
                return False

            # Check if the element already exists
            existing_element = parent.find(f"{entry}[@key='{key}']")
            if existing_element is not None:
                existing_element.text = value  # Update existing element
            else:
                # Create a new element and append it to the parent
                new_element = ET.Element(entry, key=key)
                new_element.text = value
                parent.append(new_element)

            ET.indent(tree, space="\t", level=0)
            return tree
        except Exception as e:
            print(f"Error when adding parameter: {e}")
            return None

    def split_train_test(self, input_data_path, train_output_path, test_output_path, train_test_split_ratio=1, test_sample_choice="random"):
        delete_file_if_exists(train_output_path)
        delete_file_if_exists(test_output_path) 

        if (train_test_split_ratio == 1):
            try:
                shutil.copyfile(input_data_path, train_output_path)
            except FileNotFoundError:
                print(f"Source file '{input_data_path}' not found.")
            except Exception as e:
                print(f"Error occurred while copying file: {e}")
            return True

        # Load the data
        data = pd.read_csv(input_data_path, delimiter='\t')

        # Determine if the data should be shuffled
        shuffle = test_sample_choice == "random"

        # Split the data
        train_data, test_data = train_test_split(data, test_size=1-train_test_split_ratio, shuffle=shuffle)

        # Save the data to files
        train_data.to_csv(train_output_path, sep='\t', index=False)
        test_data.to_csv(test_output_path, sep='\t', index=False)

        return True
    
    def create_individual_file(self, file_path, error, size, prefix_function):
        file_string = ""
        file_string += '<Individual size="1">\n'
        file_string += f'\t<FitnessMin value="{error}"/>\n'
        file_string += f'\t<Tree size="{size}">{prefix_function} </Tree>\n'
        file_string += '</Individual>'

        with open(file_path, 'w') as file:
            file.write(file_string)

    def parse_best_individual_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines() 
            error = float(lines[3].split('"')[1])
            solutions = []
            for i in range(7, len(lines)):
                if lines[i].strip() != "":
                    solutions.append(float(lines[i].strip())) 

        return error, solutions