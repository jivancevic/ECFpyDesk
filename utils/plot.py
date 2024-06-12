import numpy as np

def safe_divide(x, y):
    """Safely divide x by y, replacing division by zero with zero."""
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.divide(x, y)
        result[np.isinf(result) | np.isnan(result)] = 0  # replace inf and NaN with 0
    return result

def safe_sqrt(x):
    """Square root that handles non-positive values by returning zero."""
    return np.where(x > 0, np.sqrt(x), 0)

def safe_log(x):
    """Logarithm that handles non-positive values by returning zero."""
    return np.where(x > 0, np.log10(x), 0)

def if_pos(v, d1, d2):
    """Return d1 if v is non-negative, otherwise d2."""
    return np.where(v >= 0, d1, d2)

def if_gt(v1, v2, d1, d2):
    """Return d1 if v1 is greater than v2, otherwise d2."""
    return np.where(v1 > v2, d1, d2)

safe_dict = {
    '__builtins__': None,  # Disable direct access to built-ins
    'np': np,
    'sin': np.sin,
    'cos': np.cos,
    'add': np.add,          # C++ ADD
    'sub': np.subtract,     # C++ SUB
    'mul': np.multiply,     # C++ MUL
    'div': safe_divide,     # C++ DIV with zero check
    'pos': lambda x: np.maximum(0, x),  # C++ POS
    'ifpos': if_pos,
    'ifgt': if_gt,
    'min': np.minimum,      # C++ MIN
    'max': np.maximum,      # C++ MAX
    'avg': lambda x, y: (x + y) / 2,  # C++ AVG
    'sqrt': safe_sqrt,      # C++ SQRT
    'log': safe_log,        # C++ LOG
}