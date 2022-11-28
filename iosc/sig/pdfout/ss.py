"""SignalSuit printing things"""
import math

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainterPath, QPolygonF
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsPathItem


def mk_sin(h: int, w: int, s: int, p: int = 1) -> list[tuple[int, int]]:
    """
    Make sinusoide graph coordinates.
    :param h: Height, points
    :param w: Width, points
    :param s: Period sections
    :param p: periods
    :return: list of (x, y); x=0..w, y=0..h
    """
    retvalue = list()
    amplitude = h/2
    step = round(w / s)
    x_factor = 2 * math.pi / w
    for x in range(0, w + step, step):
        retvalue.append((x, round(amplitude * (1 + math.sin(x * x_factor)))))
    return retvalue


class SignalSuitPrnLabelItem(QGraphicsSimpleTextItem):
    """Object to print."""
    __ss: 'SignalSuit'

    def __init__(self, ss: 'SignalSuit', to_print: bool, parent: 'SignalBarLabelPrnItem' = None):
        super().__init__(ss.signal.sid, parent)  # TODO: add value on to_print
        self.__ss = ss
        self.setPen(ss.color)


class SignalSuitPrnGraphItem(QGraphicsPathItem):  # TODO: B-signal: Polygon?
    """Object to print."""
    __ss: 'SignalSuit'

    def __init__(self, ss: 'SignalSuit', parent: 'SignalBarPlotPrnItem' = None):
        super().__init__(parent)  # TODO: add value on to_print
        self.__ss = ss
        points = mk_sin(176, 720, 12)
        pg = QPolygonF([QPointF(p[0], p[1]) for p in points])
        pp = QPainterPath()
        pp.addPolygon(pg)  # TODO: spline
        self.setPath(pp)
        self.setPen(ss.color)  # FIXME: style
