# GroupDesign

**GroupDesign** is a Python library for generating and deconvoluting combinatorial experimental designs.

## Best of Greedy Algorithm

This repository includes an implementation of the "Best of Greedy" algorithm for generating block designs. This implementation is based on the following publication:

> J. A. MacDonald, M. C. Hout, J. Schmidt, *Behav. Res.* **2020**, *52*, 1459.

The algorithm generates designs by running a greedy construction strategy multiple times and selecting the best result (closest to the theoretical lower bound of blocks).

## Interval Sectioning Algorithm

The "Interval Sectioning" algorithm is an active search strategy for identifying a set of "active" tuples (e.g., specific combinations of elements that trigger a response) using a minimal number of group tests. It recursively divides the element space into groups and asks for feedback (active/inactive) to narrow down the search.

## Installation

You can install the package directly from the source directory:

```bash
pip install .
```

## Usage

### Python API

#### Generating a Design (Best of Greedy)

```python
from groupdesign import greedy_design

# Generate a design with:
# n = 7 (number of elements)
# k = 3 (size of each block)
# t = 2 (tuples to cover, e.g., pairs)
design = greedy_design(n=7, k=3, t=2)

print(design)
```

#### Searching for Active Tuples (Interval Sectioning)

```python
from groupdesign import interval_sectioning

# Search for active pairs (t=2) among n=10 elements
# The algorithm will prompt for feedback (y/n) in the console
active_tuples = interval_sectioning(n=10, t=2)

print(active_tuples)
```

### Command Line Interface

If you run the command without any arguments, it will start an **interactive mode** to guide you through the process:

```bash
groupdesign
```

Alternatively, you can provide arguments directly:

```bash
# Generate a design
groupdesign 7 3 --t 2 --m 100 --output design.csv

# Run interval sectioning search
groupdesign 10 --algorithm interval --t 2 --max-hits 1
```

Alternatively, you can run it via `python -m`:

```bash
python -m groupdesign.cli 7 3 --t 2 --m 100 --output design.csv
```

#### Arguments:
- `n`: Total number of elements (positional)
- `k`: Size of each block (positional, required for `greedy`)
- `--algorithm`: Algorithm to run: `greedy` or `interval` (default: `greedy`)
- `--t`: Tuple size (default: 2)
- `--m`: Number of design attempts (greedy only, default: 100)
- `--lambda`: Coverage factor (greedy only, default: 1)
- `--max-hits`: Maximum number of active tuples to find (interval only)
- `--output`, `-o`: CSV output path