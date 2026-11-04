import random

def set_to_string(my_set):
    return ' '.join(str(item) for item in my_set)

def string_to_set(my_string):
    return set(my_string.split())

def find_index_of_dict_with_value_in_array(array, key, value):
    for i, item in enumerate(array):
        if item[key] == value:
            return i
    return -1

def initial_label(choices, value):
    """The dropdown label for a value, or the first label if no choice has that value."""
    for label, choice_value in choices:
        if choice_value == value:
            return label
    return choices[0][0]

def choose_random_element_with_probability(array):
    keys, probabilities = zip(*array)
    return random.choices(keys, weights=probabilities, k=1)[0]