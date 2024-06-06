import numpy as np

safe_dict = {
    '__builtins__': {'None': None, 'True': True, 'False': False},
    'np': np,
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'atan': np.arctan,
    # Add other mathematical functions as needed
}
