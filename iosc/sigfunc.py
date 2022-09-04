"""Signal view functions.
Calling from AnalogSignalCtrlView to calc requested signal value"""

import numpy as np


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
    return np.sum(a[max(n - w + 1, 0):n + 1]) / w


def eff(a: np.array, n: int, w: int):
    """Effective value"""
    return a[n]


def hrm1(a: np.array, n: int, w: int):
    """1-st harmnic"""
    return a[n]


def hrm2(a: np.array, n: int, w: int):
    """2-nd harmnic"""
    return a[n]


def hrm3(a: np.array, n: int, w: int):
    """3-th harmnic"""
    return a[n]


def hrm5(a: np.array, n: int, w: int):
    """5-th harmnic"""
    return a[n]


func_list = (
    asis,
    mid,
    eff,
    hrm1,
    hrm2,
    hrm3,
    hrm5
)
