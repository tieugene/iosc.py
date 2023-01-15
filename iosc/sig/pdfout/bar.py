"""Row-level things."""
# 1. std
from typing import List, Union, Tuple
# 2. 3rd
from PyQt5.QtCore import QPointF, QSizeF, Qt, QSize
from PyQt5.QtGui import QPainterPath, QPolygonF, QBrush, QColor
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsLineItem
# 3. local
from .const import H_B_MULT, W_LABEL, H_ROW_GAP
from .gitem import ThinPen, RectTextItem, ClipedRichTextItem, GroupItem
from ..widget.sigsuit import StatusSignalSuit, AnalogSignalSuit
from ..widget.sigbar import SignalBar
from ...const import PENSTYLE_PTR_MSR, PENSTYLE_PTR_LVL

# x. const
IntX2 = Tuple[int, int]


class MsrPtrItem(QGraphicsLineItem):
    """MsrPtr representation."""

    __x: float

    def __init__(self, x: float, color: QColor, parent: 'AGraphItem'):
        """Init MsrPtrItem object."""
        super().__init__(parent)
        self.__x = x
        self.setPen(ThinPen(color, PENSTYLE_PTR_MSR))

    def set_size(self, s: QSizeF):
        """Set object size."""
        x = s.width() * self.__x
        self.setLine(x, 0, x, s.height())

    def update_visibility(self, v: bool):
        """Show/hide pointer."""
        self.setVisible(v)


class LvlPtrItem(QGraphicsLineItem):
    """LvlPtr representation."""

    y: float

    def __init__(self, y: float, color: QColor, parent: 'AGraphItem'):
        """Init LvlPtrItem object."""
        super().__init__(parent)
        self.y = y
        self.setPen(ThinPen(color, PENSTYLE_PTR_LVL))

    def update_visibility(self, v: bool):
        """Show/hide pointer."""
        self.setVisible(v)


class AGraphItem(QGraphicsPathItem):
    """Analog signal representation."""

    ymin: float  # Adjusted normalized min (-1..0 ... 0..1)
    ymax: float  # Adjusted normalized min
    __nvalue: List[float]  # normalized values slice
    msr_ptr: List[MsrPtrItem]
    lvl_ptr: List[LvlPtrItem]

    def __init__(self, ss: AnalogSignalSuit, i_range: IntX2):
        """Init AGraphItem."""
        super().__init__()
        amin = min(0.0, ss.v_min)  # adjusted absolute value
        amax = max(0.0, ss.v_max)
        asize = amax - amin  # FIXME: /0
        self.ymin = amin / asize
        self.ymax = amax / asize
        self.__nvalue = [v / asize for v in ss.v_slice(i_range[0], i_range[1])]
        self.setPen(ThinPen(ss.color))
        pp = QPainterPath()
        # default: x=0..SAMPLES, y=(-1..0)..(0..1)
        pp.addPolygon(QPolygonF([QPointF(x, -y) for x, y in enumerate(self.__nvalue)]))
        self.setPath(pp)
        self.msr_ptr = list()
        for mptr in ss.msr_ptr.values():
            if i_range[0] <= (i := mptr[0].i) <= i_range[1]:
                self.msr_ptr.append(MsrPtrItem((i - i_range[0]) / (i_range[1] - i_range[0]), ss.color, self))
        self.lvl_ptr = list()
        for lptr in ss.lvl_ptr.values():
            y = lptr[0].y_real / asize
            self.lvl_ptr.append(LvlPtrItem(y, ss.color, self))

    def set_size(self, s: QSizeF, ymax: float):
        """Set object size.

        :param s: Dest size of graph (e.g. 1077 x 28/112 for Landscape
        :param ymax: Normalized Y to shift down (in screen)
        """
        self.prepareGeometryChange()  # not helps
        # - prepare: X-scale factor, Y-shift, Y-scale factor
        kx = s.width() / (len(self.__nvalue) - 1)  # 13-1=12
        ky = s.height()
        pp = self.path()
        for i, y in enumerate(self.__nvalue):
            pp.setElementPositionAt(i, i * kx, (ymax - y) * ky)
        self.setPath(pp)
        for mptr in self.msr_ptr:
            mptr.set_size(s)
        for lptr in self.lvl_ptr:
            y = (ymax - lptr.y) * ky
            lptr.setLine(0, y, s.width(), y)

    def update_ptrs_visibility(self, v: bool):
        """Show/hide ptr."""
        for mptr in self.msr_ptr:
            mptr.update_visibility(v)
        for lptr in self.lvl_ptr:
            lptr.update_visibility(v)


class BGraphItem(QGraphicsPolygonItem):
    """Status signal representation."""

    __value: List[int]  # values slice
    ymin: float = 0.0
    ymax: float = H_B_MULT

    def __init__(self, ss: StatusSignalSuit, i_range: IntX2):
        """Init BGraphItem object."""
        super().__init__()
        self.__value = ss.v_slice(i_range[0], i_range[1])  # just copy
        self.setPen(ThinPen(ss.color))
        self.setBrush(QBrush(ss.color))  # , Qt.BrushStyle.Dense1Pattern
        self.setOpacity(0.5)
        self.__set_size(1, 1)

    def set_size(self, s: QSizeF, ymax: float):
        """Set object size.

        :param s: Size of graph
        :param ymax: Normalized Y to shift down (in screen)
        :note: L: s=(1077 x 28/112)
        """
        self.prepareGeometryChange()  # not helps
        self.__set_size(s.width() / (len(self.__value) - 1), s.height(), ymax)

    def __set_size(self, kx: float, ky: float, dy: float = 0.0):
        point_list = [QPointF(i * kx, (dy - y * H_B_MULT) * ky) for i, y in enumerate(self.__value)]
        if self.__value[0]:  # always start with 0
            point_list.insert(0, QPointF(0, (dy * ky)))
        if self.__value[-1]:  # always end with 0
            point_list.append(QPointF((len(self.__value) - 1) * kx, (dy * ky)))
        self.setPolygon(QPolygonF(point_list))


class BarLabelItem(RectTextItem):
    """Label part of signal bar."""

    __sb: SignalBar

    def __init__(self, sb: SignalBar):
        """Init BarLabelItem object."""
        super().__init__(ClipedRichTextItem())
        self.__sb = sb
        self.update_text()
        self.set_width(W_LABEL)

    @staticmethod
    def __gc2str(c: Qt.GlobalColor) -> str:
        """HTML representation of QGlobalColor value.

        :param c: Global color
        :return: HTML-compatible string representation
        """
        qc = QColor(c)
        return f"rgb({qc.red()},{qc.green()},{qc.blue()})"

    def __html(self, __2lines: bool = False) -> str:
        return ''.join([
            f"<span style='color: {self.__gc2str(ss.color)}'>{ss.get_label_html(__2lines)}</span><br/>"
            for ss in self.__sb.signals
        ])

    def update_text(self, prn_values: bool = False):
        """Update labels."""
        self.text.setHtml(self.__html(prn_values))


class BarGraphItem(GroupItem):
    """Graph part of signal bar.

    Used in: RowItem > … > Print
    """

    __graph: List[Union[AGraphItem, BGraphItem]]
    __y0line: QGraphicsLineItem  # Y=0 line
    __ymin: float  # Best Y-min normalized
    __ymax: float  # Best Y-max normalized
    __is_bool: bool

    def __init__(self, sb: SignalBar, i_range: IntX2):
        """Init BarGraphItem object."""
        super().__init__()
        self.__graph = list()
        self.__ymin = self.__ymax = 0.0  # same as self.__y0line
        self.__is_bool = True
        for d in sb.signals:
            self.__graph.append(BGraphItem(d, i_range) if d.is_bool else AGraphItem(d, i_range))
            self.addToGroup(self.__graph[-1])
            self.__ymin = min(self.__ymin, self.__graph[-1].ymin)
            self.__ymax = max(self.__ymax, self.__graph[-1].ymax)
            self.__is_bool &= d.is_bool
            # if not d.signal.is_bool:
            #    for mptr in self.__graph[-1].msr_ptr:
            #        self.addToGroup(mptr)
            #    for lptr in self.__graph[-1].lvl_ptr:
            #        self.addToGroup(lptr)
        if not self.__is_bool:
            self.__y0line = QGraphicsLineItem()
            self.__y0line.setPen(ThinPen(Qt.GlobalColor.gray, Qt.PenStyle.DotLine))
            self.addToGroup(self.__y0line)
        self.setY(H_ROW_GAP)

    def set_size(self, s: QSize):
        """Set object size."""
        h_norm = self.__ymax - self.__ymin  # normalized height, ≥ 1
        s_local = QSizeF(s.width(), (s.height() - H_ROW_GAP * 2) / h_norm)
        for gi in self.__graph:
            gi.set_size(s_local, self.__ymax)
        if not self.__is_bool:  # - move Y=0
            y0px = self.__ymax / h_norm * (s.height() - H_ROW_GAP * 2)
            self.__y0line.setLine(0, y0px, s.width(), y0px)

    def update_ptrs_visibility(self, v: bool):
        """Show/hide pointers."""
        for gi in self.__graph:
            if isinstance(gi, AGraphItem):
                gi.update_ptrs_visibility(v)


class RowItem(GroupItem):
    """Used in: TablePayload > … > View/Print."""

    __sb: SignalBar
    __plot: 'PlotPrint'  # noqa: F821; ref to father
    __label: BarLabelItem  # left side
    __graph: BarGraphItem  # right side
    __uline: QGraphicsLineItem  # underline

    def __init__(self, sb: SignalBar, plot: 'PlotPrint'):  # noqa: F821
        """Init RowItem object."""
        super().__init__()
        self.__sb = sb
        self.__plot = plot
        self.__label = BarLabelItem(sb)
        self.__graph = BarGraphItem(sb, plot.i_range)
        self.__uline = QGraphicsLineItem()
        self.__uline.setPen(ThinPen(Qt.GlobalColor.black, Qt.PenStyle.DashLine))
        # initial positions/sizes
        self.__label.set_width(W_LABEL)
        self.__graph.setX(W_LABEL + 1)
        self.update_size()
        self.update_ptrs_visibility()
        self.addToGroup(self.__label)
        self.addToGroup(self.__graph)
        self.addToGroup(self.__uline)

    def update_size(self):
        """Update geometry."""
        w = self.__plot.w_full - W_LABEL
        h = self.__plot.h_row(self.__sb)
        self.__label.set_height(h - 1)
        self.__graph.set_size(QSize(w, h - 1))
        self.__uline.setLine(0, h - 1, self.__plot.w_full, h - 1)

    def update_labels(self):
        """Show/hide signal labels."""
        self.__label.update_text(self.__plot.prn_values)

    def update_ptrs_visibility(self):
        """Show/hide pointers."""
        self.__graph.update_ptrs_visibility(self.__plot.prn_ptrs)
