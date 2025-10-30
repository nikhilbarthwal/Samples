import numpy as np
import random
from typing import List
import math


def test(a, b):
    if len(a) != len(b):
        return False
    for i in range(len(a)):
        if round(abs(a[i] - b[i]), 5) != 0.0:
            return False
    return True

class FFT:

    def __init__(self, indexes: List[int]):
        self.indexes: List[int] = indexes
        self.N: int = len(indexes)
        if self.N > 1:
            assert self.N % 2 == 0
            self.even = FFT(
                [indexes[i] for i in range(self.N) if i % 2 == 0])
            self.odd = FFT(
                [indexes[i] for i in range(self.N) if i % 2 == 1])
            self.factor = []
            for i in range(self.N):
                theta = -2 * np.pi * i / self.N
                self.factor.append(math.cos(theta) + 1j * math.sin(theta))

    def compute(self, x):
        assert self.N > 0
        if self.N == 1:
            return [x[self.indexes[0]]]

        assert self.N % 2 == 0
        even = self.even.compute(x)
        odd = self.odd.compute(x)
        half = self.N // 2
        assert len(even) == half
        assert len(odd) == half

        def r(i):
            if i < half:
                return even[i] + self.factor[i] * odd[i]
            return even[i - half] + self.factor[i] * odd[i - half]

        return [r(i) for i in range(self.N)]


class IFFT:

    def __init__(self, indexes: List[int]):
        self.indexes: List[int] = indexes
        self.N: int = len(indexes)
        if self.N > 1:
            assert self.N % 2 == 0
            self.even = IFFT(
                [indexes[i] for i in range(self.N) if i % 2 == 0])
            self.odd = IFFT(
                [indexes[i] for i in range(self.N) if i % 2 == 1])
            self.factor = []
            for i in range(self.N):
                theta = 2 * np.pi * i / self.N
                self.factor.append(math.cos(theta) + 1j * math.sin(theta))

    def compute(self, x):
        assert self.N > 0
        if self.N == 1:
            return [x[self.indexes[0]]]

        assert self.N % 2 == 0
        even = self.even.compute(x)
        odd = self.odd.compute(x)
        half = self.N // 2
        assert len(even) == half
        assert len(odd) == half

        def r(i):
            if i < half:
                return (even[i] + self.factor[i] * odd[i]) / 2.0
            return (even[i - half] + self.factor[i] * odd[i - half])/2.0

        return [r(i) for i in range(self.N)]


def run(n):
    indexes = list(range(2**n))
    f = FFT(indexes)
    inv_f = IFFT(indexes)
    x = [random.randint(0, 1000) for _ in indexes]
    y = f.compute(x)
    assert test(y, np.fft.fft(x))
    assert test(x, inv_f.compute(y))


run(10)
