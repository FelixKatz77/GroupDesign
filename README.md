# GroupDesign

**GroupDesign** is a Python library for generating and deconvoluting combinatorial experimental designs.

## Best of Greedy Algorithm

This repository includes an implementation of the "Best of Greedy" algorithm for generating block designs. This implementation is based on the following publication:

> J. A. MacDonald, M. C. Hout, J. Schmidt, *Behav. Res.* **2020**, *52*, 1459.

The algorithm generates designs by running a greedy construction strategy multiple times and selecting the best result (closest to the theoretical lower bound of blocks).

## Usage

### Python API

```python
from groupdesign.best_of_greedy import greedy_design

# Generate a design with:
# n = 7 (number of elements)
# k = 3 (size of each block)
# t = 2 (tuples to cover, e.g., pairs)
design = greedy_design(n=7, k=3, t=2)

print(design)
```

### Command Line Interface

You can also use the CLI to generate designs:

```bash
python -m groupdesign.cli 7 3 --t 2 --m 100 --output design.csv
```

#### Arguments:
- `n`: Total number of elements (positional)
- `k`: Size of each block (positional)
- `--t`: Tuple size to cover (default: 2)
- `--m`: Number of design attempts (default: 100)
- `--lambda`: Coverage factor (default: 1)
- `--output`, `-o`: CSV output path