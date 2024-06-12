from utils.plot import safe_dict
import numpy as np

# Mock data
x1 = np.array([1, 2, 3])
x2 = np.array([4, 5, 6])
data = [x1, x2]
print(data)

function_str = "(((log(((avg(x2, x1) - (x1 / x2)) + avg(x2, log(x2)))) + (0.416379 / avg(log((0.837553 / -0.36384)), log(x2)))) * log(x1)) - (log((x1 * (x1 - (x2 * x1)))) * 0.236243))"

variable_dict = {f'x{i+1}': data[i] for i in range(len(data))}
# Add these to the safe dict for evaluation
safe_dict.update(variable_dict)
print(safe_dict)
try:
    # Evaluate the function string safely
    results = eval(function_str, {"__builtins__": None}, safe_dict)

    # Test the function
    print(results)
except Exception as e:
    print(f"Error evaluating multivariable function: {e}")



