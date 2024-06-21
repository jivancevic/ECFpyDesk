def set_to_string(my_set):
    return ' '.join(str(item) for item in my_set)

def string_to_set(my_string):
    return set(my_string.split(" "))