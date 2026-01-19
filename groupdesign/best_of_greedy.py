import time
from tqdm import tqdm
from itertools import combinations
from math import comb
import numpy as np
from groupdesign.utils import Packed2D, Packed3D

def element_degrees(n: int, t: int, _lambda: int) -> int:
    """Return how many times each element appears across all t-tuples (scaled by _lambda)."""
    if t < 1 or t > n:
        raise ValueError("t must be in [1, n]")
    return comb(n - 1, t - 1) * _lambda


def greedy_design(n: int, k: int, t: int = 2, elements: list | None = None,
                            m: int = 100, _lambda: int = 1) -> np.ndarray:
    """Generate a greedy block design that covers all pair comparisons."""
    start_time = time.time()
    if n <= 0:
        raise ValueError("n must be positive")
    if k <= 0 or k > n:
        raise ValueError("k must be positive and less than or equal to n")
    if k < t:
        raise ValueError("k must be at least t")
    if t <= 0:
        raise ValueError("t must be positive")
    if m <= 0:
        raise ValueError("m must be positive")
    if _lambda < 1:
        raise ValueError("_lambda must be positive")

    if elements is None:
        elements = np.arange(1, n + 1, dtype=int)
    elements = np.asarray(elements)
    if elements.size != n:
        raise ValueError("Elements must be a list of length n.")

    # Select packed storage based on t
    if t == 2:
        packer = Packed2D(n, _lambda, dtype=int)
        # Pre-fetch lookup array for speed (t=2 uses _T)
        _T = packer._T
    elif t == 3:
        packer = Packed3D(n, _lambda, dtype=int)
        # Pre-fetch lookup arrays for speed (t=3 uses _C2, _C3)
        _C2 = packer._C2
        _C3 = packer._C3
    else:
        raise NotImplementedError("Only t=2 and t=3 are currently supported with packed optimization.")

    coverage = packer.data  # Direct access to the flat array
    initial_degree_val = element_degrees(n, t, _lambda) #Number of times each element has to appear in blocks

    best_design = None
    rng = np.random.default_rng()

    # Calculate idealized minimal number of blocks: ceil(C(n, t) * _lambda / C(k, t))
    design_bound = int(np.ceil(comb(n, t) * _lambda / comb(k, t)))

    def build_block(current_degree: np.ndarray) -> np.ndarray:
        block = np.full(k, -1, dtype=int) #initialize empty block
        taken = np.zeros(n, dtype=bool) #mask of elements already included in block

        for position in range(k):
            if position < t - 1:
                # Not enough elements to form a tuple yet
                # Score is solely based on current_degree
                scores = current_degree.astype(float)
            else:
                scores = np.zeros(n, dtype=float)

                # Calculate coverage gain for each candidate
                if t == 2:
                    # For t=2: check pairs (existing, candidate)
                    existing_indices = block[:position]
                    for existing in existing_indices:
                        # Case 1: candidate < existing
                        c_lo = np.arange(existing)
                        idx_lo = existing * (existing - 1) // 2 + c_lo
                        scores[c_lo] += coverage[idx_lo]

                        # Case 2: candidate > existing
                        c_hi = np.arange(existing + 1, n)
                        idx_hi = _T[c_hi] + existing
                        scores[c_hi] += coverage[idx_hi]

                elif t == 3:
                    # For t=3: check triples (e1, e2, candidate)
                    existing_indices = block[:position]
                    for e1, e2 in combinations(existing_indices, 2): #iterate over all pairs that could form a triple
                        # Ensure a < b for correct indexing
                        a, b = (e1, e2) if e1 < e2 else (e2, e1)

                        # Calculate scores based on uncovered tuples each element contributes to
                        # Case 1: candidate < a < b
                        c1 = np.arange(a)
                        idx1 = c1 + _C2[a] + _C3[b]
                        scores[c1] += coverage[idx1]

                        # Case 2: a < candidate < b
                        c2 = np.arange(a + 1, b)
                        idx2 = a + _C2[c2] + _C3[b]
                        scores[c2] += coverage[idx2]

                        # Case 3: a < b < candidate
                        c3 = np.arange(b + 1, n)
                        idx3 = a + _C2[b] + _C3[c3]
                        scores[c3] += coverage[idx3]

                # If no tuple gives gain, we rely on degree (secondary objective)

            scores[taken] = -1.0 #Update score for selected element
            max_score = scores.max() #Identify maximum scores

            # Tie-breaking logic
            if max_score < 0:
                # Should not happen given k <= n
                break

            candidates = np.flatnonzero(scores == max_score) #Selects all indices where score = max_score
            if candidates.size > 1:
                # Secondary objective: max current_degree, select element that is included in the most uncovered tuples
                deg_subset = current_degree[candidates]
                max_deg = deg_subset.max()
                candidates = candidates[deg_subset == max_deg]

            chosen = int(rng.choice(candidates)) #choose at random if multiple candidates are left
            block[position] = chosen
            taken[chosen] = True

        return block

    pbar = tqdm(range(m))
    for i in pbar:

        # Reset state
        packer.data[:] = _lambda
        current_degree = np.full(n, initial_degree_val, dtype=int)
        blocks: list[np.ndarray] = []

        total_remaining = coverage.sum() #remaining pairs to cover

        while total_remaining > 0:
            block = build_block(current_degree)
            blocks.append(block.copy())

            # Update coverage and degrees based on the chosen block
            # Since block size k is small, explicit iteration is efficient enough
            sorted_block = np.sort(block)
            for t_tuple in combinations(sorted_block, t):
                if t == 2:
                    u, v = t_tuple  # u < v
                    # Packed2D expects i > j, so (v, u)
                    idx = v * (v - 1) // 2 + u
                elif t == 3:
                    u, v, w = t_tuple  # u < v < w
                    # Packed3D expects a < b < c
                    idx = u + _C2[v] + _C3[w]

                if coverage[idx] > 0:
                    coverage[idx] -= 1
                    total_remaining -= 1
                    current_degree[list(t_tuple)] -= 1

        design = np.vstack(blocks)
        if best_design is None or (design.shape[0] < best_design.shape[0]):
            best_design = design
            pbar.set_postfix({'Best Design': f'{best_design.shape[0]} Blocks'})

        if best_design.shape[0] <= design_bound:
            print(f"Runtime: {time.time() - start_time:.4f} seconds")
            return elements[best_design]

    if best_design is None:
        raise RuntimeError("Unable to generate a feasible design with the provided parameters.")

    print(f"Runtime: {time.time() - start_time:.4f} seconds")
    return elements[best_design]

if __name__ == "__main__":
    greedy_design(10, 2)