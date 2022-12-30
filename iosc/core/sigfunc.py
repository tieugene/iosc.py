"""Signal view functions.
Calling from AnalogSignalCtrlWidget to calc requested signal value.
FFT: [Libs](https://www.nayuki.io/page/free-small-fft-in-multiple-languages)
"""
# 1. std
import math
# 2. 3rd
import numpy as np


def _cutlpad(a: np.array, n: int, w: int) -> np.array:
    """Cut windows from array and lpad it by zero if required"""
    return a[n + 1 - w:n + 1] if n + 1 >= w else np.pad(a[:n + 1], (w - n - 1, 0))


def _sft(a: np.array, n: int, w: int, h: int) -> complex:
    if n < (w - 1):
        return 0 + 0j
    win = a[n + 1 - w:n + 1]
    mult_2 = 2 / w / math.sqrt(2)
    mult_1 = 2 * math.pi * h / w
    arg = n * mult_1
    sum_r = sum_i = 0.0
    for i, v in enumerate(win):
        arg += mult_1  # arg = (n + 1 + i) * mult_1
        sum_r += v * math.sin(arg)
        sum_i += v * math.cos(arg)
    return complex(sum_r * mult_2, sum_i * mult_2)


def asis(a: np.array, n: int, _: int) -> float:
    """
    Value as is
    :param a: Values array
    :param n: Value index in array
    :param _: Array window
    :return: Value
    """
    return a[n]


def mid(a: np.array, n: int, w: int) -> float:
    """Running average in window[, padded by 0 to left]."""
    return np.sum(a[max(n + 1 - w, 0):n + 1]) / w


def rms(a: np.array, n: int, w: int) -> float:
    """Effective value.
    :note: np.std(_cutlpad(a, n, w)) - not right
    :note: the same: np.sqrt(np.average(_cutlpad(np.array(a), n, w)**2))
    """
    return np.sqrt(sum(np.array(a[max(n + 1 - w, 0):n + 1]) ** 2) / w)


def hrm1(a: np.array, n: int, w: int) -> complex:
    """1-st harmonic.
    :todo: return python complex
    """
    return _sft(a, n, w, 1)


def hrm2(a: np.array, n: int, w: int) -> float:
    """2-nd harmonic"""
    return abs(_sft(a, n, w, 2))


def hrm3(a: np.array, n: int, w: int) -> float:
    """3-th harmonic"""
    return abs(_sft(a, n, w, 3))


def hrm5(a: np.array, n: int, w: int) -> float:
    """5-th harmonic"""
    return abs(_sft(a, n, w, 5))


func_list = (asis, mid, rms, hrm1, hrm2, hrm3, hrm5)
