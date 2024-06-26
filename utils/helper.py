import random

def set_to_string(my_set):
    return ' '.join(str(item) for item in my_set)

def string_to_set(my_string):
    return set(my_string.split(" "))

def find_index_of_dict_with_value_in_array(array, key, value):
    for i, item in enumerate(array):
        if item[key] == value:
            return i
    return -1

def choose_random_element_with_probability(array):
    keys, probabilities = zip(*array)
    return random.choices(keys, weights=probabilities, k=1)[0]