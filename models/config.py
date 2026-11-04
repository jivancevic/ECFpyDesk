import itertools
import logging
import math
import os
import random
import re
import xml.etree.ElementTree as ET

from models.best_file import parse_evaluation
from utils import paths
from utils.file import delete_file_if_exists
from utils.helper import choose_random_element_with_probability
from utils.parameters import options

logger = logging.getLogger(__name__)

FUNCTION_SET_PATH = "ECF/Genotype/Entry/functionset"
TERMINAL_SET_PATH = "ECF/Genotype/Entry/terminalset"
LINKING_FUNCTIONS_PATH = "ECF/Genotype/GEPChromosome/Entry/linkingfunctions"
INPUT_FILE_PATH = "ECF/Registry/Entry/input_file"
ERROR_WEIGHTS_PATH = "ECF/Registry/Entry/error_weights.file"
POPULATION_SIZE_PATH = "ECF/Registry/Entry/population.size"
SEED_PATH = "ECF/Registry/Entry/randomizer.seed"
EVALUATION_POPULATION_SIZE = 10  # an evaluation run builds a population it never uses
ALL_FUNCTIONS = [function for _, function in options["Functions"]]

class ProcessConfiguration:
    def __init__(self, parameters_path, input_file_path, best_file_path, log_file_path=None, tree=None, root=None, template_path=None, error_weights_path=None, keeps_seed=False):
        self.parameters_path = parameters_path
        self.input_file_path = input_file_path
        self.best_file_path = best_file_path
        self.log_file_path = log_file_path
        self.tree = tree
        self.root = root
        self.template_path = template_path
        self.error_weights_path = error_weights_path
        self.keeps_seed = keeps_seed

class ConfigurationManager:
    tree = None
    root = None

    def __init__(self):
        # Default parameters file paths, they are written in format (path, probability of being chosen)
        self.default_parameters_paths = [
            (paths.resource_path("srm", "srmGP.txt"), 0.8),
            (paths.resource_path("srm", "srmGEP.txt"), 0.1),
            (paths.resource_path("srm", "srmAP.txt"), 0.1)
        ]
        self.default_evaluation_parameters_paths = [
            (paths.resource_path("srm", "srm_eval.txt"), 1)
        ]
        self.eval_configurations = {}
        self.configurations = {}
        self.test_configurations = {}
        # Counting up, so that no two runs of SRM in this session share a seed
        self.seeds = itertools.count(random.randrange(1, 2**30))

    def set_tree_and_root(self):
        self.tree, self.root = self.load_template(self.default_parameters_paths[0][0])

    def saved_path(self, template_path):
        return os.path.join(paths.saved_parameters_dir(), os.path.basename(template_path))

    def load_template(self, template_path):
        """The user's saved copy of a template if there is a usable one, else the template itself."""
        saved_path = self.saved_path(template_path)
        if os.path.exists(saved_path):
            try:
                tree, root = self.parse_XML(saved_path)
                self.validate_parameters(tree)
                return tree, root
            except (ET.ParseError, ValueError) as e:
                logger.warning(f"Ignoring unusable saved parameters {saved_path}: {e}")
        return self.parse_XML(template_path)

    def validate_parameters(self, tree):
        """The app and SRM cannot work with parameters that lack these."""
        if tree.getroot().find("Registry") is None:
            raise ValueError("The parameters have no Registry section")
        for path, name in ((FUNCTION_SET_PATH, "functionset"), (TERMINAL_SET_PATH, "terminalset")):
            elements = self.find_param_elements(path, tree)
            if not elements or not (elements[0].text or "").strip():
                raise ValueError(f"The parameters have no {name}")

    def create_config(self, process_id, parameters_path, input_file_path, best_file_path, log_file_path, is_test=False, params=None, error_weights_path=None):
        if is_test:
            template_path = choose_random_element_with_probability(self.default_evaluation_parameters_paths)
        else:
            template_path = choose_random_element_with_probability(self.default_parameters_paths)

        tree, root = self.load_configured_template(template_path, params)
        if is_test:
            self.allow_all_functions(tree)
            self.set_param_element(POPULATION_SIZE_PATH, EVALUATION_POPULATION_SIZE, tree)
        elif not self.restrict_linking_functions(tree):
            # GEP cannot run without a linking function, so this Process uses GP instead
            template_path = self.default_parameters_paths[0][0]
            tree, root = self.load_configured_template(template_path, params)

        process_config = ProcessConfiguration(parameters_path=parameters_path, input_file_path=input_file_path, best_file_path=best_file_path, log_file_path=log_file_path, tree=tree, root=root, template_path=template_path, error_weights_path=error_weights_path, keeps_seed=self.has_chosen_seed(tree))
        self.create_parameters_file(process_config, is_test)

        if process_id == 'eval':
            self.eval_configurations[process_id] = process_config
        elif not is_test:
            self.configurations[process_id] = process_config
        else:
            self.test_configurations[process_id] = process_config

    def load_configured_template(self, template_path, params):
        tree, root = self.load_template(template_path)
        self.update_parameters(params or {}, tree)
        self.prepare_config(tree, template_path)
        return tree, root

    def create_parameters_file(self, config, is_test=False):
        # SRM runs in the temp directory. Relative paths keep spaces and non-ASCII characters
        # of the user's home directory away from it.
        self.set_param_element(INPUT_FILE_PATH, self.relative_path(config.input_file_path), config.tree)
        self.set_param_element("ECF/Registry/Entry/bestfile", self.relative_path(config.best_file_path), config.tree)
        self.set_param_element("ECF/Registry/Entry/log.filename", self.relative_path(config.log_file_path), config.tree)
        if config.error_weights_path:
            self.set_param_element(ERROR_WEIGHTS_PATH, self.relative_path(config.error_weights_path), config.tree)
        if is_test:
            self.set_param_element("ECF/Registry/Entry/linear_scaling", "false", config.tree)

        self.write_config(config.tree, config.parameters_path)

        return True

    def relative_path(self, path):
        return os.path.relpath(path, paths.temp_dir())

    def parse_XML(self, parameters_path):
        tree = ET.parse(parameters_path)
        return tree, tree.getroot()

    def write_config(self, tree, file_path):
        ET.indent(tree, space="\t", level=0)
        tree.write(file_path)

    def update_config(self, params):
        """Saves params as the user's defaults. The templates themselves never change."""
        saved_params = dict(params)
        for path in (INPUT_FILE_PATH, ERROR_WEIGHTS_PATH):
            if saved_params.get(path):
                saved_params[path] = paths.portable_path(saved_params[path])
        for (path, probs) in self.default_parameters_paths + self.default_evaluation_parameters_paths:
            tree, root = self.load_configured_template(path, saved_params)
            self.write_config(tree, self.saved_path(path))

    def read_manual_parameters(self):
        """The text the "Change Manually" editor shows."""
        template_path = self.default_parameters_paths[0][0]
        saved_path = self.saved_path(template_path)
        with open(saved_path if os.path.exists(saved_path) else template_path, 'r') as file:
            return file.read()

    def save_manual_parameters(self, text):
        try:
            tree = ET.ElementTree(ET.fromstring(text))
        except ET.ParseError as e:
            raise ValueError(f"The parameters are not valid XML: {e}") from e
        self.validate_parameters(tree)
        with open(self.saved_path(self.default_parameters_paths[0][0]), 'w') as file:
            file.write(text)
        self.set_tree_and_root()

    def update_parameters(self, params, tree):
        for path, value in params.items():
            if value is not None and value != "":
                self.set_param_element(path, value, tree)

    def set_new_seed(self, process_id):
        """SRM seeds itself from the clock, so Processes started in the same second could run
        alike. Each run of SRM gets its own seed, unless the user set one in the parameters."""
        config = self.configurations[process_id]
        if config.keeps_seed:
            return
        self.set_param_element(SEED_PATH, next(self.seeds), config.tree)
        self.write_config(config.tree, config.parameters_path)

    def has_chosen_seed(self, tree):
        elements = self.find_param_elements(SEED_PATH, tree)
        return bool(elements) and (elements[0].text or "0").strip() != "0"

    def allow_all_functions(self, tree):
        """An evaluation run must read any Individual, and SRM aborts on a function outside the
        function set. Individuals can hold more than the user's set: GEP links genes with its
        linking functions, and linear scaling wraps every expression in + and *."""
        current = self.find_param_elements(FUNCTION_SET_PATH, tree)[0].text.split()
        functions = current + [function for function in ALL_FUNCTIONS if function not in current]
        self.set_param_element(FUNCTION_SET_PATH, " ".join(functions), tree)

    def restrict_linking_functions(self, tree):
        """SRM aborts on a linking function outside the function set. Returns False if the
        tree is a GEP one and no linking function is left."""
        linking_elements = self.find_param_elements(LINKING_FUNCTIONS_PATH, tree)
        if not linking_elements:
            return True
        function_set = self.find_param_elements(FUNCTION_SET_PATH, tree)[0].text.split()
        linking = [function for function in linking_elements[0].text.split() if function in function_set]
        if not linking:
            return False
        linking_elements[0].text = " ".join(linking)
        return True

    def get_current_function_set(self):
        return self.get_current_param_value(FUNCTION_SET_PATH)
    
    def get_current_terminal_set(self):
        return self.get_current_param_value(TERMINAL_SET_PATH)
    
    def get_current_param_value(self, path):
        # Load the XML tree from a file or an existing in-memory object
        if self.tree is None:
            self.set_tree_and_root()

        target_elements = self.find_param_elements(path, self.tree)

        if target_elements != []:
            return target_elements[0].text  # Return the text content of the element
        return None  # If the element with the key doesn't exist, return None
    
    def set_param_element(self, path, value, tree):
        target_elements = self.find_param_elements(path, tree)
        if target_elements != []:
            for element in target_elements:
                element.text = str(value)
        else:
            # If the parameter doesn't exist, consider creating it
            self.add_param_element(path, value, tree)
    
    def find_param_elements(self, path, tree=None):
        # Split the path by slashes to navigate through the nodes
        elements = path.split('/')

        if tree is None:
            tree = self.tree
        root = tree.getroot()

        current_element = root

        # Navigate through the tree to find the target element
        for element in elements[1:-2]:  # Use all elements except the last one for navigation

            current_element = current_element.find(f".//{element}")
            if current_element is None:
                return []  # Return an empty list if any part of the path is invalid

        # The last part of the path should be the key of the attribute you are looking for
        entry = elements[-2]
        key = elements[-1]

        # Use findall to collect all elements that match the final part of the path
        target_elements = current_element.findall(f".//{entry}[@key='{key}']")

        return target_elements


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
                logger.warning(f"Could not find the parent path: {parent_path}")
                return False

            # Check if the element already exists
            existing_element = parent.find(f"{entry}[@key='{key}']")
            if existing_element is not None:
                existing_element.text = str(value)  # Update existing element
            else:
                # Create a new element and append it to the parent
                new_element = ET.Element(entry, key=key)
                new_element.text = str(value)
                parent.append(new_element)

            ET.indent(tree, space="\t", level=0)
            return tree
        except Exception as e:
            logger.error(f"Error when adding parameter: {e}")
            return None
        
    def prepare_config(self, tree, parameters_path=None):
        num_vars = self.calculate_num_vars(tree)
        max_depth = math.trunc(4.5 + math.sqrt(num_vars))
        dimension = 2 * max_depth

        if self.find_param_elements("ECF/Genotype/Tree/Entry/maxdepth", tree):
            self.set_param_element("ECF/Genotype/Tree/Entry/maxdepth", max_depth, tree)
        if self.find_param_elements("ECF/Genotype/APGenotype/Entry/dimension", tree):
            self.set_param_element("ECF/Genotype/APGenotype/Entry/dimension", dimension, tree)

    def calculate_num_vars(self, tree):
        terminal_set_element = self.find_param_elements(TERMINAL_SET_PATH, tree)[0]
        terminal_set = terminal_set_element.text

        terminal_set = terminal_set.split(" ")
        pattern = re.compile(r'^x\d+$')
        variables = [element for element in terminal_set if re.match(pattern, element)]

        return len(variables)

    def read_rows(self, file_path):
        # SRM takes an empty line for a sample without values
        with open(file_path, 'r') as file:
            return [line.rstrip("\r\n") for line in file if line.strip()]

    def write_rows(self, rows, indices, file_path):
        with open(file_path, 'w') as file:
            file.writelines(rows[i] + "\n" for i in indices)

    def split_train_test(self, input_data_path, train_output_path, test_output_path, train_test_split_ratio=1, test_sample_choice="random", error_weights_path=None, train_weights_path=None, test_weights_path=None):
        """Splits the rows of the input data, and of the error weights in the same way so that
        each row keeps its weight. Rows are copied as text, so no value changes on the way."""
        for path in (train_output_path, test_output_path, train_weights_path, test_weights_path):
            if path is not None:
                delete_file_if_exists(path)

        rows = self.read_rows(input_data_path)
        indices = list(range(len(rows)))

        if train_test_split_ratio >= 1:
            train_indices, test_indices = indices, []
        else:
            if len(rows) < 2:
                raise ValueError("Splitting into train and test sets needs at least two rows")
            test_count = min(max(round(len(rows) * (1 - train_test_split_ratio)), 1), len(rows) - 1)
            if test_sample_choice == "random":
                random.shuffle(indices)
            train_indices, test_indices = indices[:-test_count], indices[-test_count:]

        self.write_rows(rows, train_indices, train_output_path)
        if test_indices:
            self.write_rows(rows, test_indices, test_output_path)

        if error_weights_path:
            weights = self.read_rows(error_weights_path)
            if len(weights) < len(rows):
                raise ValueError(f"The error weights file has {len(weights)} rows, the input data has {len(rows)}")
            self.write_rows(weights, train_indices, train_weights_path)
            if test_indices:
                self.write_rows(weights, test_indices, test_weights_path)

    def create_individual_file(self, file_path, error, size, prefix_function):
        file_string = ""
        file_string += '<Individual size="1">\n'
        file_string += f'\t<FitnessMin value="{error}"/>\n'
        file_string += f'\t<Tree size="{size}">{prefix_function} </Tree>\n'
        file_string += '</Individual>'

        with open(file_path, 'w') as file:
            file.write(file_string)

    def read_evaluation(self, best_file_path, output_path):
        with open(best_file_path, 'r') as best_file, open(output_path, 'r', errors='replace') as output:
            return parse_evaluation(best_file.read(), output.read())
