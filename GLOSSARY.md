# Glossary

**ECF**: Evolutionary Computation Framework, the C++ library that runs the evolutionary algorithms.

**SRM**: the C++ program built on ECF that solves symbolic regression. The app runs it; the app never evolves anything itself.

**Symbolic regression**: finding a mathematical expression that fits the input data, rather than fitting the parameters of a fixed model.

**Input data**: a tab-separated file. Each row is a sample, the last column is the target, the columns before it are the variables `x1`, `x2` and so on.

**Terminal set**: the variables and constants an expression may use.

**Function set**: the operators an expression may use.

**Parameter file**: the XML file SRM takes when it starts.

**Template**: one of the parameter files a Process is created from: GP, GEP or AP, drawn at probabilities 0.8, 0.1 and 0.1.

**Process**: one running SRM instance with its own parameter file. A run has several, and their results are combined.

**Best file**: the file a Process writes its best individuals to. The app reads it while the Process runs.

**Individual**: one candidate expression, with its size and error.

**Pareto front**: the Individuals that no other Individual beats on both size and error. This is what the results screen lists.

**Train set, test set**: the two parts the input data is split into. Evolution sees only the train set. With Show Test Data ticked, the Pareto front ranks Individuals by test error; otherwise by train error.
