"""Signal view functions.
Calling from AnalogSignalCtrlView to calc requested signal value.
FFT:
- [RTFM](http://digitalsubstation.com/i-mt/2016/12/05/modelirovanie-rza-chast-vtoraya/)
- [Libs](https://www.nayuki.io/page/free-small-fft-in-multiple-languages)
"""

import numpy as np


def _cutlpad(a: np.array, n: int, w: int) -> np.array:
    """Cut windows from array and lpad it by zero if required"""
    return a[n + 1 - w:n + 1] if n + 1 >= w else np.pad(a[:n + 1], (w - n - 1, 0))


def _fft(a: np.array, n: int, w: int):
    return np.fft.fft(_cutlpad(a, n, w))


def asis(a: np.array, n: int, _: int) -> float:
    """
    Value as is
    :param a: Values array
    :param n: Value index in array
    :param _: Array window
    :return: Value
    """
    return a[n]


def mid(a: np.array, n: int, w: int):
    """Running average in window[, padded by 0 to left]."""
    return np.sum(a[max(n + 1 - w, 0):n + 1]) / w


def eff(a: np.array, n: int, w: int):
    """Effective value.
    :note: np.std(_cutlpad(a, n, w)) - not right
    """
    return np.sqrt(np.average(_cutlpad(np.array(a), n, w)**2))


def hrm1(a: np.array, n: int, w: int):
    """1-st harmnic.
    :todo: return python complex
    """
    c = _fft(a, n, w)
    return np.absolute(c)[1], np.degrees(np.angle(c))[1]


def hrm2(a: np.array, n: int, w: int):
    """2-nd harmnic"""
    return np.absolute(_fft(a, n, w))[2]


def hrm3(a: np.array, n: int, w: int):
    """3-th harmnic"""
    return np.absolute(_fft(a, n, w))[3]


def hrm5(a: np.array, n: int, w: int):
    """5-th harmnic"""
    return np.absolute(_fft(a, n, w))[5]


func_list = (
    asis,
    mid,
    eff,
    hrm1,
    hrm2,
    hrm3,
    hrm5
)
