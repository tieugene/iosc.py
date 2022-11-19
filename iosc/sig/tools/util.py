from PyQt5.QtGui import QColor


def sign_b2n(v: float, lim: float):
    if abs(v) < lim:
        return 0
    elif v < 0:
        return -1
    else:
        return 1


def color2style(c: QColor) -> str:
    """Convert QColor into stylesheet-compatible string"""
    return "rgb(%d, %d, %d)" % (c.red(), c.green(), c.blue())
