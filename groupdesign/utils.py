import numpy as np
from math import comb

class Packed1D:
    def __init__(self, n: int, value:int, dtype=np.float32):
        self.n = int(n)
        self.size = self.n
        self.data = np.full(self.size, value, dtype=dtype)

class Packed2D:
    def __init__(self, n: int, value:int, dtype=np.float32):
        self.n = int(n)
        self.size = self.n * (self.n - 1) // 2
        self.data = np.full(self.size, value, dtype=dtype)

        # T[i] = i*(i-1)//2 for i=0..n
        x = np.arange(self.n + 1, dtype=np.int64)
        self._T = x * (x - 1) // 2

    def index(self, i, j):
        i = int(i); j = int(j)
        if i == j:
            raise KeyError("Diagonal not stored")
        if i < j:
            i, j = j, i
        if not (0 <= j < i < self.n):
            raise IndexError
        return i * (i - 1) // 2 + j

class Packed3D:
    def __init__(self, n: int, value:int, dtype=np.int64):
        self.n = int(n)
        self.size = self.n * (self.n - 1) * (self.n - 2) // 6
        self.data = np.full(self.size, value, dtype=dtype)

        # Precompute for fast inverse mapping (rank -> triple)
        x = np.arange(self.n + 1, dtype=np.int64)
        self._C2 = x * (x - 1) // 2
        self._C3 = x * (x - 1) * (x - 2) // 6

    @staticmethod
    def _C2_int(x: int) -> int:
        """Helper function for computing C2(x)"""
        return x * (x - 1) // 2

    @staticmethod
    def _C3_int(x: int) -> int:
        """Helper function for computing C3(x)"""
        return x * (x - 1) * (x - 2) // 6

    def index(self, i, j, k):
        i = int(i); j = int(j); k = int(k)
        if i == j or i == k or j == k:
            raise KeyError("Requires all distinct indices")
        if not (0 <= i < self.n and 0 <= j < self.n and 0 <= k < self.n):
            raise IndexError

        a, b, c = sorted((i, j, k))  # canonical representative
        return a + self._C2_int(b) + self._C3_int(c)

def element_degrees(n: int, t: int, _lambda: int) -> int:
    """Return how many times each element appears across all t-tuples (scaled by _lambda)."""
    if t < 1 or t > n:
        raise ValueError("t must be in [1, n]")
    return comb(n - 1, t - 1) * _lambda