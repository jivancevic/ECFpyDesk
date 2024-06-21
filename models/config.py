import xml.etree.ElementTree as ET
import itertools
import os
import shutil
import pandas as pd
from sklearn.model_selection import train_test_split
from utils.file import delete_file_if_exists
from .parameters import param_paths

class ConfigurationManager:
    tree = None
    root = None

    def __init__(self, parameters_path):
        self.parameters_path = parameters_path

    def parse_XML(self):
        with open(self.parameters_path) as f:
            tree = ET.ElementTree(file=f)
        root = tree.getroot()
        return tree, root

    def write_config(self, tree):
        file_content = ET.tostring(tree.getroot(), encoding='unicode')
        with open(self.parameters_path, 'w') as f:
            f.write(file_content)

    def update_config(self, params):
        self.tree, self.root = self.parse_XML()

        for path, value in params.items():
            if value is not None and value != "":
                if path == param_paths["input_path"]:
                    value = value.replace('.txt', '_train.txt')
                self.set_param_element(path, value)

        self.write_config(self.tree)

    def get_current_function_set(self):
        return self.get_current_param_value("ECF/Genotype/Entry/functionset")
    
    def get_current_terminal_set(self):
        return self.get_current_param_value("ECF/Genotype/Entry/terminalset")
    
    def get_current_param_value(self, path):
        # Load the XML tree from a file or an existing in-memory object
        if self.tree is None or self.root is None:
            self.set_tree_and_root()

        target_element = self.find_param_element(path)

        if target_element is not None:
            return target_element.text  # Return the text content of the element
        return None  # If the element with the key doesn't exist, return None
    
    def set_param_element(self, path, value):
        target_element = self.find_param_element(path)
        if target_element is not None:
            target_element.text = value
        elif value is not None and value != "":
            self.add_param_element(path, value)
    
    def find_param_element(self, path):
        # Split the path by slashes to navigate through the nodes
        elements = path.split('/')
        current_element = self.root

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

    def add_param_element(self, path, value):
        try:
            # Assume self.root is already an ElementTree object of the loaded XML
            elements = path.split('/')
            parent_path = "/".join(elements[1:-2])  # Get the path to the parent node
            entry = elements[-2]
            key = elements[-1]

            # Navigate to the parent element
            parent = self.root.find(parent_path)
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

            ET.indent(self.tree, space="\t", level=0)
            return True
        except Exception as e:
            print(f"Error when adding parameter: {e}")
            return False

    
    def set_tree_and_root(self):
        self.tree, self.root = self.parse_XML()

    def split_train_test(self, input_data_path, train_test_split_ratio, test_sample_choice):
        # Define output file paths
        train_output_path = input_data_path.replace('.txt', '_train.txt')
        test_output_path = input_data_path.replace('.txt', '_test.txt')

        delete_file_if_exists(train_output_path)
        delete_file_if_exists(test_output_path) 

        if (train_test_split_ratio == 1):
            try:
                shutil.copyfile(input_data_path, train_output_path)
            except FileNotFoundError:
                print(f"Source file '{input_data_path}' not found.")
            except Exception as e:
                print(f"Error occurred while copying file: {e}")
            return train_output_path, None

        # Load the data
        data = pd.read_csv(input_data_path, delimiter='\t')

        # Determine if the data should be shuffled
        shuffle = test_sample_choice == "random"

        # Split the data
        train_data, test_data = train_test_split(data, test_size=1-train_test_split_ratio, shuffle=shuffle)

        # Save the data to files
        train_data.to_csv(train_output_path, sep='\t', index=False)
        test_data.to_csv(test_output_path, sep='\t', index=False)

        return train_output_path, test_output_path