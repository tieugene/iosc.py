"""Row-level things"""
# 1. std
from typing import List, Union
# 2. 3rd
from PyQt5.QtCore import QPointF, QSizeF, Qt, QSize
from PyQt5.QtGui import QPainterPath, QPolygonF, QBrush, QTransform, QColor
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsLineItem
# 3. local
from .const import H_B_MULT, W_LABEL, H_ROW_GAP, SAMPLES
from .gitem import ThinPen, RectTextItem, ClipedRichTextItem, GroupItem
from iosc.sig.widget.common import AnalogSignalSuit, StatusSignalSuit, SignalBar


def gc2str(c: Qt.GlobalColor) -> str:
    """
    :param c: Global color
    :return: HTML-compatible string representation
    """
    qc = QColor(c)
    return f"rgb({qc.red()},{qc.green()},{qc.blue()})"


class AGraphItem(QGraphicsPathItem):
    __ss: AnalogSignalSuit

    def __init__(self, ss: AnalogSignalSuit):
        super().__init__()
        self.__ss = ss
        self.setPen(ThinPen(ss.color))
        pp = QPainterPath()
        # default: x=0..SAMPLES, y=(-1..0)..(0..1)
        pp.addPolygon(QPolygonF([QPointF(x, -y) for x, y in enumerate(self.__ss.nvalue)]))
        self.setPath(pp)

    @property
    def ymin(self) -> float:
        return self.__ss.anmin

    @property
    def ymax(self) -> float:
        return self.__ss.anmax

    def set_size(self, s: QSizeF, ymax: float):
        """
        :param s: Dest size of graph (e.g. 1077 x 28/112 for Landscape
        :param ymax: Normalized Y to shift down (in screen)
        """
        self.prepareGeometryChange()  # not helps
        # - prepare: X-scale factor, Y-shift, Y-scale factor
        kx = s.width() / (self.__ss.count - 1)  # 13-1=12
        ky = s.height()
        pp = self.path()
        for i, y in enumerate(self.__ss.nvalue):
            pp.setElementPositionAt(i, i * kx, (ymax - y) * ky)
            # Неправильно. ky = ymax/(ymax - ymin) (как для y0line)
        self.setPath(pp)


class BGraphItem(QGraphicsPolygonItem):
    __ss: StatusSignalSuit
    ymin: float = 0.0
    ymax: float = H_B_MULT

    def __init__(self, ss: StatusSignalSuit):
        super().__init__()
        self.__ss = ss
        self.setPen(ThinPen(ss.color))
        self.setBrush(QBrush(ss.color))  # , Qt.BrushStyle.Dense1Pattern
        self.setOpacity(0.5)
        self.__set_size(1, 1)

    def set_size(self, s: QSizeF, ymax: float):
        """
        L: s=(1077 x 28/112)
        :param s: Size of graph
        :param ymax: Normalized Y to shift down (in screen)
        """
        self.prepareGeometryChange()  # not helps
        self.__set_size(s.width() / (self.__ss.count - 1), s.height(), ymax)

    def __set_size(self, kx: float, ky: float, dy: float = 0.0):
        point_list = [QPointF(i * kx, (dy - y * H_B_MULT) * ky) for i, y in enumerate(self.__ss.value)]
        if self.__ss.value[0]:  # always start with 0
            point_list.insert(0, QPointF(0, (dy * ky)))
        if self.__ss.value[-1]:  # always end with 0
            point_list.append(QPointF((self.__ss.count - 1) * kx, (dy * ky)))
        self.setPolygon(QPolygonF(point_list))


class BarLabelItem(RectTextItem):
    __sb: SignalBar
    """Label part of signal bar"""
    def __init__(self, sb: SignalBar):
        super().__init__(ClipedRichTextItem())
        self.__sb = sb
        self.update_text()
        self.set_width(W_LABEL)

    def update_text(self, prn_values: bool = False):
        self.text.setHtml(self.__sb.html(prn_values))

    def html(self, __2lines: bool = False) -> str:
        return ''.join([f"<span style='color: {gc2str(ss.color)}'>{ss.get_label(__2lines)}</span><br/>" for ss in self.__sb.signals])


class BarGraphItem(GroupItem):
    """Graph part of signal bar.
    Used in: RowItem > … > View/Print
    """
    __graph: List[Union[AGraphItem, BGraphItem]]
    __y0line: QGraphicsLineItem  # Y=0 line
    __ymin: float  # Best Y-min normalized
    __ymax: float  # Best Y-max normalized
    __is_bool: bool

    def __init__(self, bs: SignalBar):
        super().__init__()
        self.__graph = list()
        self.__ymin = self.__ymax = 0.0  # same as self.__y0line
        self.__is_bool = True
        for d in bs.signals:
            self.__graph.append(BGraphItem(d) if d.signal.is_bool else AGraphItem(d))
            self.__is_bool &= d.signal.is_bool
            self.addToGroup(self.__graph[-1])
            self.__ymin = min(self.__ymin, self.__graph[-1].ymin)
            self.__ymax = max(self.__ymax, self.__graph[-1].ymax)
        if not self.__is_bool:
            self.__y0line = QGraphicsLineItem()
            self.__y0line.setPen(ThinPen(Qt.GlobalColor.gray, Qt.PenStyle.DotLine))
            self.__y0line.setLine(0, 0, SAMPLES, 0)
            self.addToGroup(self.__y0line)
        self.setY(H_ROW_GAP)

    def __set_size_via_tr(self, s: QSize):
        """Resize self using QTransform.
        :note: Children boundingRect() include pen width.
        :todo: transform into rect
        """
        ky = s.height() / (self.__ymax - self.__ymin)
        # self.resetTransform()  # not helps
        self.setTransform(QTransform().translate(0, -self.__ymin * ky))
        self.setTransform(QTransform().scale(s.width() / SAMPLES, ky), True)
        self.update()

    def set_size(self, s: QSize):
        """Used in: View/Print.
        :todo: chk pen width
        """
        h_norm = self.__ymax - self.__ymin  # normalized height, ≥ 1
        s_local = QSizeF(s.width(), (s.height() - H_ROW_GAP * 2) / h_norm)
        for gi in self.__graph:
            gi.set_size(s_local, self.__ymax)
        if not self.__is_bool:  # - move Y=0
            y0px = self.__ymax / h_norm * (s.height() - H_ROW_GAP * 2)
            self.__y0line.setLine(0, y0px, s.width(), y0px)


class RowItem(GroupItem):
    """Used in: TablePayload > … > View/Print"""
    __bs: SignalBar
    __plot: 'PlotBase'  # ref to father
    __label: BarLabelItem  # left side
    __graph: BarGraphItem  # right side
    __uline: QGraphicsLineItem  # underline

    def __init__(self, bs: SignalBar, plot: 'PlotBase'):
        super().__init__()
        self.__bs = bs
        self.__plot = plot
        self.__label = BarLabelItem(bs)
        self.__graph = BarGraphItem(bs)
        self.__uline = QGraphicsLineItem()
        self.__uline.setPen(ThinPen(Qt.GlobalColor.black, Qt.PenStyle.DashLine))
        # initial positions/sizes
        self.__label.set_width(W_LABEL)
        self.__graph.setX(W_LABEL + 1)
        self.update_size()
        self.addToGroup(self.__label)
        self.addToGroup(self.__graph)
        self.addToGroup(self.__uline)

    def update_size(self):
        w = self.__plot.w_full - W_LABEL
        h = self.__plot.h_row(self.__bs)
        self.__label.set_height(h-1)
        self.__graph.set_size(QSize(w, h-1))
        self.__uline.setLine(0, h-1, self.__plot.w_full, h-1)

    def update_labels(self):
        self.__label.update_text(self.__plot.prn_values)
        # print("RowItem.update_labels")
