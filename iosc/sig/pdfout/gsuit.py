"""Graphics things (application dependent)"""
import math
# 1. std
from typing import List
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsRectItem, QGraphicsItem
# 3. local
from .const import W_LABEL, H_HEADER, H_BOTTOM, TICS
from .gitem import ThinPen, RectTextItem, ClipedPlainTextItem, GroupItem, TCPlainTextItem
from .bar import RowItem
from iosc.sig.widget.common import SignalBarList
# x. const
PORS_TEXT = ('Primary', 'Secondary')


class HeaderItem(RectTextItem):
    """:fixme: pors test not changing"""
    __plot: 'PlotPrint'

    def __init__(self, oscwin: 'ComtradeWidget', plot: 'PlotPrint'):
        super().__init__(ClipedPlainTextItem(
            f"{oscwin.osc.path}"
            f"\nStation ID: {oscwin.osc.raw.rec_dev_id}, Station name: {oscwin.osc.raw.station_name}"
            f"\n{PORS_TEXT[int(oscwin.show_sec)]} values"
        ))
        self.__plot = plot
        self.update_size()

    def update_size(self):
        self.set_width(self.__plot.w_full)


class TableCanvas(GroupItem):
    """Table frame with:
    - header
    - border
    - columns separator
    - bottom underline
    - bottom scale
    - grid
    """

    class GridItem(GroupItem):
        __plot: 'PlotPrint'
        __x: float
        __line: QGraphicsLineItem
        __text: TCPlainTextItem

        def __init__(self, x: float, num: str, plot: 'PlotPrint'):
            """
            :param x: Normalized X-position, 0..1
            :param num: Text to label
            :param plot: Parent plot
            """
            super().__init__()
            self.__x = x
            self.__plot = plot
            self.__line = QGraphicsLineItem()
            self.__line.setPen(ThinPen(Qt.GlobalColor.lightGray))
            self.__text = TCPlainTextItem(num)
            # layout
            self.addToGroup(self.__line)
            self.addToGroup(self.__text)

        def update_size(self):
            x = W_LABEL + (self.__plot.w_full - W_LABEL) * self.__x
            y = self.__plot.h_full - H_BOTTOM
            self.__line.setLine(x, H_HEADER, x, y)
            self.__text.setPos(x, y)

    __plot: 'PlotPrint'
    __header: HeaderItem
    __frame: QGraphicsRectItem  # external border; TODO: clip all inners (header, tic labels) by this
    __colsep: QGraphicsLineItem  # columns separator
    __btmsep: QGraphicsLineItem  # bottom separator
    __grid: List[GridItem]  # tics (v-line+label)

    def __init__(self, oscwin: 'ComtradeWidget', plot: 'PlotPrint'):
        super().__init__()
        self.__plot = plot
        self.__header = HeaderItem(oscwin, plot)
        pen = ThinPen(Qt.GlobalColor.gray)
        self.__frame = QGraphicsRectItem()
        self.__frame.setPen(pen)
        self.__frame.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape)
        self.__colsep = QGraphicsLineItem()
        self.__colsep.setPen(pen)
        self.__btmsep = QGraphicsLineItem()
        self.__btmsep.setPen(pen)
        # layout
        self.addToGroup(self.__header)
        self.addToGroup(self.__frame)
        self.addToGroup(self.__colsep)
        self.addToGroup(self.__btmsep)
        self.__mk_grid(oscwin)
        # go
        self.update_sizes()

    def __mk_grid_(self, _):
        self.__grid = list()
        for x, num in TICS.items():
            self.__grid.append(self.GridItem(x, num, self.__plot))
            self.__grid[-1].setParentItem(self.__frame)
            self.addToGroup(self.__grid[-1])

    def __mk_grid(self, oscwin: 'ComtradeWidget'):
        """
        - get T0 (agains 0)
        - get Tmax (against 0)
        - get step
        """
        x_step: int = oscwin.x_px_width_us() * 100  # μs, grid step (1..1000 * 100, e.g. 1000)
        i_range = self.__plot.i_range
        t0: float = oscwin.osc.x[i_range[0]] * 1000  # μs, 1st sample position (e.g. -81666.(6))
        t1: float = oscwin.osc.x[i_range[1]] * 1000  # μs, last sample position (e.g. 116666.(6))
        t_size: float = t1 - t0
        x_us: int = math.ceil(t0 / x_step) * 100000  # μs, 1st grid position
        # print(t0, t1, x_step, x_us)
        self.__grid = list()
        while x_us < t1:
            x_norm = (x_us - t0) / t_size
            num = str(x_us // 1000) if x_step > 1000 else "%.1f" % (x_us / 1000)
            self.__grid.append(self.GridItem(x_norm, num, self.__plot))
            self.__grid[-1].setParentItem(self.__frame)
            self.addToGroup(self.__grid[-1])
            x_us += x_step

    def update_sizes(self):
        self.__header.update_size()
        self.__frame.setRect(0, H_HEADER, self.__plot.w_full, self.__plot.h_full - H_HEADER)
        self.__colsep.setLine(W_LABEL, H_HEADER, W_LABEL, self.__plot.h_full - H_BOTTOM)
        self.__btmsep.setLine(0, self.__plot.h_full - H_BOTTOM, self.__plot.w_full, self.__plot.h_full - H_BOTTOM)
        for g in self.__grid:
            g.update_size()


class TablePayload(GroupItem):
    """Just rows with underlines.
    Used in: PlotScene > … > Print
    """
    __rowitem: list[RowItem]

    def __init__(self, sblist: SignalBarList, plot: 'PlotPrint'):
        super().__init__()
        self.__rowitem = list()
        y = 0
        # return  # stub
        for sb in sblist:
            item = RowItem(sb, plot)
            item.setY(y)
            y += item.boundingRect().height()
            self.__rowitem.append(item)
            self.addToGroup(self.__rowitem[-1])

    def update_sizes(self):
        # y = self.__rowitem[0].boundingRect().y()
        y = H_HEADER
        for item in self.__rowitem:
            item.update_size()
            item.setY(y)
            y += item.boundingRect().height()

    def update_labels(self):
        for item in self.__rowitem:
            item.update_labels()


class PlotScene(QGraphicsScene):
    """Used in: PlotPrint > PrintView"""
    __canvas: TableCanvas
    __payload: TablePayload

    def __init__(self, sblist: SignalBarList, oscwin: 'ComtradeWidget', plot: 'PlotPrint'):
        super().__init__()
        self.__canvas = TableCanvas(oscwin, plot)
        self.__payload = TablePayload(sblist, plot)
        self.__payload.setY(H_HEADER)
        self.addItem(self.__canvas)
        self.addItem(self.__payload)

    def update_sizes(self):
        self.__canvas.update_sizes()
        self.__payload.update_sizes()
        self.setSceneRect(self.itemsBoundingRect())

    def update_labels(self):
        self.__payload.update_labels()
