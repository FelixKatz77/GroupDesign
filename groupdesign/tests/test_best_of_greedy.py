import unittest
import numpy as np
from itertools import combinations
from groupdesign.best_of_greedy import greedy_design

class TestGreedyDesign(unittest.TestCase):
    def verify_coverage(self, design, n, k, t, lambda_val):
        """
        Validation Helper Logic:
        1. Generate all combinations of size t from the elements 1 to n.
        2. For each combination, iterate through the rows of the design matrix.
        3. Check if the combination is a subset of the row.
        4. Count the occurrences.
        5. Assert count >= lambda.
        """
        # Elements are 1-indexed based on the issue description "elements 1 to n"
        elements = list(range(1, n + 1))
        all_t_combinations = list(combinations(elements, t))
        
        for combo in all_t_combinations:
            count = 0
            combo_set = set(combo)
            for row in design:
                if combo_set.issubset(set(row)):
                    count += 1
            self.assertGreaterEqual(
                count, 
                lambda_val, 
                f"Combination {combo} covered only {count} times, expected at least {lambda_val}"
            )

    def test_fano_plane(self):
        # Test Case 1 (Pairs): n=7, k=3, t=2, lambda=1
        n, k, t, lambda_val = 7, 3, 2, 1
        design = greedy_design(n=n, k=k, t=t, _lambda=lambda_val, m=10)
        self.verify_coverage(design, n, k, t, lambda_val)

    def test_triples(self):
        # Test Case 2 (Triples): n=8, k=4, t=3, lambda=1
        n, k, t, lambda_val = 8, 4, 3, 1
        design = greedy_design(n=n, k=k, t=t, _lambda=lambda_val, m=10)
        self.verify_coverage(design, n, k, t, lambda_val)

    def test_high_lambda(self):
        # Test Case 3 (High Lambda): n=5, k=3, t=2, lambda=2
        n, k, t, lambda_val = 5, 3, 2, 2
        design = greedy_design(n=n, k=k, t=t, _lambda=lambda_val, m=10)
        self.verify_coverage(design, n, k, t, lambda_val)

if __name__ == '__main__':
    unittest.main()
