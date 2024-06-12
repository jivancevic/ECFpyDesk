import numpy as np

def custom_avg(*args):
    # Convert all inputs to numpy arrays ensuring at least 1D
    args = [np.atleast_1d(a) for a in args]

    try:
        # Attempt to broadcast all arguments to a common shape
        broadcasted_args = np.broadcast_arrays(*args)
        # Calculate the mean across these broadcasted arrays
        result = np.mean(np.stack(broadcasted_args, axis=0), axis=0)
    except ValueError as e:
        raise ValueError(f"Cannot broadcast arrays to a common shape: {str(e)}")
    
    return result

def custom_log(x):
    # Adding a small constant to ensure the input is positive
    # np.clip is used here to avoid negative and zero values
    # Alternatively, you can return a default value or handle the case as needed
    safe_x = np.clip(x, a_min=1e-10, a_max=None)  # Avoid log(0) which results in -inf
    return np.log(safe_x)

safe_dict = {
    '__builtins__': {'None': None, 'True': True, 'False': False},
    'np': np,
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'atan': np.arctan,
    'avg': custom_avg,
    'log': custom_log,
    'sqrt': np.sqrt,
    'min': np.min,
    'max': np.max,
    'pos': np.where
}