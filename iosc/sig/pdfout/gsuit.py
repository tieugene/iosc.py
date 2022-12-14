"""Graphics things (application dependent)"""
# 1. std
from typing import List
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsRectItem, QGraphicsItem
# 3. local
from .const import W_LABEL, H_HEADER, H_BOTTOM, HEADER_TXT, SAMPLES, TICS
from .gitem import ThinPen, RectTextItem, ClipedPlainTextItem, GroupItem, TCPlainTextItem
from .bar import RowItem
from iosc.sig.widget.common import SignalBarList


class HeaderItem(RectTextItem):
    __plot: 'PlotPrint'

    def __init__(self, plot: 'PlotPrint'):
        super().__init__(ClipedPlainTextItem(HEADER_TXT))
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

        def __init__(self, x: float, num: int, plot: 'PlotPrint'):
            super().__init__()
            self.__x = x
            self.__plot = plot
            self.__line = QGraphicsLineItem()
            self.__line.setPen(ThinPen(Qt.GlobalColor.lightGray))
            self.__text = TCPlainTextItem(str(num))
            # layout
            self.addToGroup(self.__line)
            self.addToGroup(self.__text)

        def update_size(self):
            x = W_LABEL + (self.__plot.w_full - W_LABEL) * self.__x / SAMPLES
            y = self.__plot.h_full - H_BOTTOM
            self.__line.setLine(x, H_HEADER, x, y)
            self.__text.setPos(x, y)

    __plot: 'PlotPrint'
    __header: HeaderItem
    __frame: QGraphicsRectItem  # external border; TODO: clip all inners (header, tic labels) by this
    __colsep: QGraphicsLineItem  # columns separator
    __btmsep: QGraphicsLineItem  # bottom separator
    __grid: List[GridItem]  # tics (v-line+label)

    def __init__(self, plot: 'PlotPrint'):
        super().__init__()
        self.__plot = plot
        self.__header = HeaderItem(plot)
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
        # grid
        self.__grid = list()
        for x, num in TICS.items():
            self.__grid.append(self.GridItem(x, num, plot))
            self.addToGroup(self.__grid[-1])
            self.__grid[-1].setParentItem(self.__frame)
        # go
        self.update_sizes()

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

    def __init__(self, bslist: SignalBarList, plot: 'PlotPrint'):
        super().__init__()
        self.__rowitem = list()
        y = 0
        return
        for bs in bslist:
            item = RowItem(bs, plot)
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

    def __init__(self, bslist: SignalBarList, plot: 'PlotPrint'):
        super().__init__()
        self.__canvas = TableCanvas(plot)
        self.__payload = TablePayload(bslist, plot)
        self.__payload.setY(H_HEADER)
        self.addItem(self.__canvas)
        self.addItem(self.__payload)

    def update_sizes(self):
        self.__canvas.update_sizes()
        self.__payload.update_sizes()
        self.setSceneRect(self.itemsBoundingRect())

    def update_labels(self):
        self.__payload.update_labels()
