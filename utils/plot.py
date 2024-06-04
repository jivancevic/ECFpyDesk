import numpy as np

safe_dict = {
    'np': np,
    'x': None, # Placeholder, will be set dynamically
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'atan': np.arctan,
    # Add other mathematical functions as needed
}

def set_x_range(x_data, num_points=400):
    # Sets the range of x based on given data
    safe_dict['x'] = np.linspace(np.min(x_data), np.max(x_data), num_points)