search_options = [
        ("search_metric", "Search metric", [
            ("Mean squared error (MSE)", "mean_square_error"), 
            ("Mean absolute error (MAE)", "mean_absolute_error"), 
            ("Mean absolute percentage error (MAPE)", "mean_absolute_percentage_error")
        ]),
        ("train_test_split", "Train/test split", [
            ("No cross-validation", 1), ("50/50", 0.5), ("60/40", 0.6), ("70/30", 0.7), ("75/25", 0.75), ("80/20", 0.8)
        ]),
        ("test_sample", "Test sample", [
            ("Chosen randomly", "random"), ("Chosen sequentially", "sequential")
        ])
    ]

# dictionary for options for Input screen
options = {
    "Functions": [
        ("Addition", "+"), ("Subtraction", "-"), ("Multiplication", "*"), ("Division", "/"),
        ("Average", "avg"), ("Logarithm", "log"), ("Square root", "sqrt"), ("Minimum", "min"), 
        ("Maximum", "max"), ("Position", "pos"),("sin(x)", "sin"), ("cos(x)", "cos")
    ],
    "Registry parameters": [
        ("Linear scaling", "ECF/Registry/Entry/linear_scaling"),
        ("Population size", "ECF/Registry/Entry/population.size"),
        ("Mutation probability", "ECF/Registry/Entry/mutation.indprob"),
        ("Max generations", "ECF/Registry/Entry/term.maxgen"),
        ("Log frequency", "ECF/Registry/Entry/log.frequency"),
    ],

}