import unittest
from unittest.mock import patch
import numpy as np
import itertools
import re
import random
from groupdesign.interval_sectioning import interval_sectioning


class Oracle:
    """
    Simulates a user responding to the interval_sectioning algorithm.
    It holds the 'ground truth' of active tuples and answers 'y' if a queried
    group contains at least one active tuple.
    """

    def __init__(self, active_tuples, t):
        # Convert to a set of sorted tuples for easy lookup
        self.active_tuples = set(tuple(sorted(x)) for x in active_tuples)
        self.t = t

    def __call__(self, prompt):
        # Parse the group from the prompt string: "Is the group [ ... ] active? (y/n): "
        # We assume N is small enough that numpy doesn't truncate the output with "..."
        match = re.search(r"Is the group \[(.*?)\] active\?", prompt, re.DOTALL)
        if not match:
            # Fallback for different numpy formatting or unexpected prompts
            return 'n'

        content = match.group(1)
        # Extract all numbers from the array string
        numbers = [int(s) for s in content.split() if s.isdigit()]
        group = np.array(numbers)

        # Check if any active tuple is a subset of this group
        # This mimics the physical test: if the pool contains a hit, the result is positive.

        # Optimization: If the group is smaller than t, it can't contain a tuple
        if len(group) < self.t:
            return 'n'

        # Generate all combinations of size t from the group
        # In a real scenario, this might be expensive for large groups,
        # but for unit tests with small N it is fine.
        has_active = False
        # We only need to find one to say 'yes'
        for subset in itertools.combinations(group, self.t):
            if tuple(sorted(subset)) in self.active_tuples:
                has_active = True
                break

        return 'y' if has_active else 'n'


class TestIntervalSectioning(unittest.TestCase):

    def setUp(self):
        # Ensure numpy print options don't truncate arrays in the prompt
        # so our regex parsing works reliably.
        np.set_printoptions(threshold=np.inf)

    def generate_random_active_set(self, n, t, density=0.01):
        """Generates a random set of active tuples."""
        elements = np.arange(1, n + 1)
        all_possible = list(itertools.combinations(elements, t))

        # Calculate how many to pick
        k = max(1, int(len(all_possible) * density))

        active_indices = random.sample(range(len(all_possible)), k)
        active_tuples = [list(all_possible[i]) for i in active_indices]
        return active_tuples

    @patch('builtins.input')
    def test_find_all_active_pairs(self, mock_input):
        """
        Test that the algorithm finds ALL active pairs in a noisy environment.
        """
        n = 30
        t = 2
        # ~1% hit rate
        ground_truth = self.generate_random_active_set(n, t, density=0.05)
        # Using 5% to ensure we definitely get a few pairs for the test,
        # 1% of 30*29/2 (435) is ~4 pairs.

        oracle = Oracle(ground_truth, t)
        mock_input.side_effect = oracle

        print(f"\n[Test] Searching for {len(ground_truth)} active pairs among {n} items...")

        found_tuples = interval_sectioning(n, t)

        # Convert results to set of sorted tuples for comparison
        found_set = set(tuple(sorted(x)) for x in found_tuples)
        truth_set = set(tuple(sorted(x)) for x in ground_truth)

        self.assertEqual(found_set, truth_set,
                         f"Algorithm missed or hallucinated pairs.\nExpected: {truth_set}\nFound: {found_set}")

    @patch('builtins.input')
    def test_max_hits_early_stopping(self, mock_input):
        """
        Test that the algorithm stops early when max_hits is reached.
        """
        n = 30
        t = 2
        # Ensure we have enough targets to actually hit the limit
        ground_truth = self.generate_random_active_set(n, t, density=0.10)
        target_hits = 2

        # Sanity check to ensure we actually generated enough data for the test
        if len(ground_truth) <= target_hits:
            self.skipTest("Random generation didn't produce enough active tuples for max_hits test.")

        oracle = Oracle(ground_truth, t)
        mock_input.side_effect = oracle

        found_tuples = interval_sectioning(n, t, max_hits=target_hits)

        self.assertEqual(len(found_tuples), target_hits,
                         f"Should have stopped exactly at {target_hits} hits.")

        # Verify that the found ones are actually correct
        found_set = set(tuple(sorted(x)) for x in found_tuples)
        truth_set = set(tuple(sorted(x)) for x in ground_truth)

        self.assertTrue(found_set.issubset(truth_set),
                        "Found tuples should be a subset of the ground truth.")


if __name__ == '__main__':
    unittest.main()