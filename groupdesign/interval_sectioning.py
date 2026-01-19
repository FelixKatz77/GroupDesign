import itertools
import numpy as np
from groupdesign.utils import Packed1D, Packed2D, Packed3D


class MaxHitsReached(Exception):
    pass

def make_groups(elements: np.ndarray, t: int):
    n = elements.size
    number_of_blocks = t + 1

    # 1. Pre-calculate block boundaries
    base_size = n // number_of_blocks
    remainder = n % number_of_blocks

    lengths = np.full(number_of_blocks, base_size)
    lengths[:remainder] += 1

    # Calculate start indices for every block
    starts = np.zeros(number_of_blocks, dtype=int)
    starts[1:] = np.cumsum(lengths)[:-1]

    groups_padding = np.arange(number_of_blocks - remainder, number_of_blocks)

    groups = []

    # Create a reusable mask (True = keep, False = drop)
    mask = np.ones(n, dtype=bool)

    for i in range(number_of_blocks):
        # The original code removes blocks[-(i+1)]
        excluded_blk_idx = number_of_blocks - 1 - i

        blk_start = starts[excluded_blk_idx]
        blk_end = blk_start + lengths[excluded_blk_idx]

        # Turn off the bits for the block we want to remove
        mask[blk_start:blk_end] = False

        # Optimization for the padding case:
        # Instead of 'inserting', simply turn the first bit of that block back on
        if remainder and i in groups_padding:
            mask[blk_start] = True

        # Create the group in one efficient memory copy
        groups.append(elements[mask])

        # Reset the mask for the next iteration
        mask[blk_start:blk_end] = True

    return groups

STATE_INACTIVE = 0    # Pruned / Known Inactive
STATE_UNKNOWN = 1     # Initial State
STATE_ACTIVE = 2      # Confirmed Active
STATE_POTENTIAL = 3   # Soft Track: In an active group, but specific tuple not confirmed

def interval_sectioning(n:int, t:int, max_hits:int=None):

    if t == 1:
        opt = Packed1D(n, STATE_UNKNOWN, dtype=np.int8)
    elif t == 2:
        opt = Packed2D(n, STATE_UNKNOWN, dtype=np.int8)
    elif t == 3:
        # Packed3D defaults to int64, force int8 if compatible or stick to int
        opt = Packed3D(n, STATE_UNKNOWN, dtype=np.int8)
    else:
        raise ValueError("Only r=1,2,3 are supported")

    active_tuples = []
    current_group = np.arange(1, n+1)

    def search_group(current_group: np.ndarray, max_hits=max_hits):
        groups = make_groups(current_group, t)
        for group in groups:
            # 1. Vectorized Combination & Index Calculation
            elements_0 = group - 1

            # Generate all combinations as an array (N x t)
            comb_arr = np.array(list(itertools.combinations(elements_0, t)), dtype=np.int64)
            if comb_arr.size == 0:
                continue

            # Vectorized index calculation
            if t == 1:
                indices = comb_arr.flatten()
            elif t == 2:
                indices = (comb_arr[:, 1] * (comb_arr[:, 1] - 1) // 2) + comb_arr[:, 0]
            elif t == 3:
                a, b, c = comb_arr[:, 0], comb_arr[:, 1], comb_arr[:, 2]
                indices = a + (b * (b - 1) // 2) + (c * (c - 1) * (c - 2) // 6)
            else:
                raise ValueError(f"t={t} is not supported in vectorized search")

            # 2. Status Check
            current_vals = opt.data[indices]

            # Check if group has ANY non-inactive elements (Unknown, Active, or Potential)
            # If everything is 0 (Inactive), we skip entirely.
            if not np.any(current_vals > STATE_INACTIVE):
                continue

            # We are interested in resolving Unknowns (1) and Potentials (3)
            is_unresolved = (current_vals == STATE_UNKNOWN) | (current_vals == STATE_POTENTIAL)

            # Optimization: Skip if nothing to discover (all 0 or 2)
            if not np.any(is_unresolved):
                continue

            # 3. Filter Elements (Simplify Group)
            # Keep only elements that participate in at least one unresolved combination
            unresolved_combos = comb_arr[is_unresolved]
            active_elems = np.unique(unresolved_combos)

            # Reconstruct group (back to 1-based)
            refined_group = active_elems + 1

            if refined_group.size < t:
                continue

            # 4. Check if the simplified group implies known activity (Auto-Skip)
            pos_mask = current_vals == STATE_ACTIVE
            is_auto_active = False
            known_triggers = []

            if np.any(pos_mask):
                pos_combos = comb_arr[pos_mask]
                # Check which of these positive combos are fully contained in the current refined group
                contained_mask = np.all(np.isin(pos_combos, active_elems), axis=1)

                if np.any(contained_mask):
                    is_auto_active = True
                    known_triggers = (pos_combos[contained_mask] + 1).tolist()

            # Indices of the unresolved tuples we want to resolve/prune in this step
            relevant_indices = indices[is_unresolved]

            if is_auto_active:
                print(f"  [Algo] Group {refined_group} is active (contains known {known_triggers}). Recursing...")
                if refined_group.size > t:
                    search_group(refined_group)
                continue

            # 5. User Interaction
            response = input(f"Is the group {refined_group} active? (y/n): ").strip().lower()

            if response in ('y', 'yes'):
                if refined_group.size > t:
                    # Soft Tracking: Mark 'Unknown' (1) tuples as 'Potentially Active' (3)
                    # We only update 1s. 0s stay 0, 2s stay 2.
                    soft_update_mask = (opt.data[relevant_indices] == STATE_UNKNOWN)
                    if np.any(soft_update_mask):
                        indices_to_soft_mark = relevant_indices[soft_update_mask]
                        opt.data[indices_to_soft_mark] = STATE_POTENTIAL

                    search_group(refined_group)

                    # Check for Impossible Selection (Post-recursion validation)
                    # After searching the subgroup, at least one tuple inside *should* have been found (STATE_ACTIVE).
                    # relevant_indices tracks what was unresolved *before* recursion.
                    new_states = opt.data[relevant_indices]
                    if not np.any(new_states == STATE_ACTIVE):
                        print(
                            "  [Algo] Impossible selection: Group was marked active, but no active tuples were found inside!")

                else:
                    # Group size == t: The specific tuple is confirmed active
                    opt.data[relevant_indices] = STATE_ACTIVE
                    active_tuples.append(refined_group.tolist())
                    if len(active_tuples) == max_hits:
                        raise MaxHitsReached


            elif response in ('n', 'no'):
                # Safe to mark as 0 (Inactive) because we verified 'refined_group'
                # does not contain known positives (via is_auto_active check).
                opt.data[relevant_indices] = STATE_INACTIVE

            else:
                raise ValueError("Invalid input. Please enter 'y' or 'n'.")
    try:
        search_group(current_group)
        print(f"Done! Found {len(active_tuples)} active tuples: {active_tuples}")
    except MaxHitsReached:
        print(f"\nTarget number of active tuples ({max_hits}) reached. Active tuples: {active_tuples}. Stopping search.")
    return active_tuples

if __name__ == "__main__":
    interval_sectioning(10, 2, max_hits=1)