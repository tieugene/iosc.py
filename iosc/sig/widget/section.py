"""Mainwidget widget lists."""
# 1. std
from typing import Tuple, Optional
# 2. 3rd
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent, QPainter
from PyQt5.QtWidgets import QTableWidget, QWidget, QHeaderView, QProxyStyle, QStyle, QStyleOption
# 3. local
from iosc.sig.widget.chart import BarPlotWidget
from iosc.sig.widget.sigbar import SignalBar, SignalBarList
from iosc.sig.widget.ctrl import BarCtrlWidget
from iosc.sig.widget.finder import FindDialog


class SignalBarTable(QTableWidget):
    """Signal bar table."""

    class DropmarkerStyle(QProxyStyle):
        """Highlight table item as drop dest."""

        def drawPrimitive(
                self,
                element: QStyle.PrimitiveElement,
                option: QStyleOption,
                painter: QPainter,
                widget: QWidget = None) -> None:
            """Inherited."""
            if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
                pen = painter.pen()
                pen.setColor(Qt.red)
                painter.setPen(pen)
            super().drawPrimitive(element, option, painter, widget)

    oscwin: 'ComtradeWidget'  # noqa: F821
    bars: SignalBarList
    __find_dialog: Optional[FindDialog]

    def __init__(self, oscwin: 'ComtradeWidget'):  # noqa: F821
        """Init SignalBarTable object."""
        super().__init__()  # Parent will be QSplitter
        self.oscwin = oscwin
        self.setColumnCount(2)
        self.bars = list()
        self.__find_dialog = None
        # self.horizontalHeader().setMinimumSectionSize(1)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().hide()
        self.__slot_resize_col_ctrl(self.oscwin.col_ctrl_width)
        # self.verticalHeader().setMinimumSectionSize(1)
        self.verticalHeader().hide()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setShowGrid(False)
        self.setStyle(self.DropmarkerStyle())
        # selection
        self.setSelectionMode(self.SelectionMode.NoSelection)  # default=SingleSelection
        self.setStyleSheet("QTableWidget:focus {border: 1px solid blue;}")
        # DnD
        # self.setDragEnabled(True)  # default=False
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(self.DragDropMode.DropOnly)  # default=DragDrop
        # signals/slot
        self.oscwin.signal_resize_col_ctrl.connect(self.__slot_resize_col_ctrl)

    def insertRow(self, row: int):
        """Inherited."""
        super().insertRow(row)
        for i in range(row + 1, len(self.bars)):
            self.bars[i].row = i

    def removeRow(self, row: int):
        """Inherited."""
        super().removeRow(row)
        for i in range(row, len(self.bars)):
            self.bars[i].row = i

    @staticmethod
    def __chk_dnd_source(event: QDropEvent):
        return type(event.source()) in {BarCtrlWidget.Anchor, BarCtrlWidget.SignalLabelList}

    def __drop_on(self, event: QDropEvent) -> Tuple[int, bool]:
        __dip = self.dropIndicatorPosition()  # 0: on row, 3: out
        __index = self.indexAt(event.pos())  # isValid: T: on row, F: out
        if not __index.isValid():  # below last
            return self.rowCount(), False
        if __dip == self.DropIndicatorPosition.AboveItem:
            return __index.row(), False
        elif __dip == self.DropIndicatorPosition.BelowItem:
            return __index.row() + 1, False
        elif __dip == self.DropIndicatorPosition.OnItem:
            return __index.row(), True
        else:
            return -1, False

    def __chk_dnd_event(self, src_object, dst_row_num: int, over: bool) -> int:
        """Check whether drop event acceptable.

        :param src_object: Source object
        :param dst_row_num: Destination object row number
        :param over: Source object overlaps (True) or insert before (False) destination object
        :return:
        - 0: n/a
        - 1: bar move
        - 2: signal join/move
        - 3: signal unjoin
        """
        if dst_row_num >= 0:
            if isinstance(src_object, BarCtrlWidget.Anchor):
                if not over:
                    return int(
                        src_object.parent().bar.table != self
                        or (dst_row_num - src_object.parent().bar.row) not in {0, 1}
                    )
            elif isinstance(src_object, BarCtrlWidget.SignalLabelList):
                if over:
                    return 2 * int(src_object.parent().bar.table != self or src_object.parent().bar.row != dst_row_num)
                else:  # sig.Ins
                    return 3 * int(src_object.count() > 1)
        return 0

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Inherited."""
        if self.__chk_dnd_source(event):
            super().dragEnterEvent(event)  # paint decoration + accept

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Inherited."""
        super().dragMoveEvent(event)  # paint decoration
        dst_row_num, over = self.__drop_on(event)
        # TODO: cache prev
        if self.__chk_dnd_event(event.source(), dst_row_num, over):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Inherited."""
        if event.isAccepted():
            super().dropEvent(event)
            return
        src_object = event.source()
        dst_row_num, over = self.__drop_on(event)  # SignalBarTable/SignalLabelList
        todo = self.__chk_dnd_event(src_object, dst_row_num, over)
        print(dst_row_num, over, todo)
        if todo == 1:  # Bar.Ins
            src_object.parent().bar.table.bar_move(src_object.parent().bar.row, self.bar_insert(dst_row_num))
        elif todo == 2:  # Sig.Ovr (join, move)
            src_object.parent().bar.sig_move(src_object.selected_row, self.bars[dst_row_num])
            src_object.clearSelection()
        elif todo == 3:  # Sig.Ins (unjoin)
            src_object.parent().bar.sig_move(src_object.selected_row, self.bar_insert(dst_row_num))
            src_object.clearSelection()
        event.accept()
        event.setDropAction(Qt.IgnoreAction)

    def __slot_resize_col_ctrl(self, x: int):
        self.setColumnWidth(0, x)

    def bar_insert(self, row: int = -1) -> SignalBar:
        """Insert new signal bar."""
        return SignalBar(self, row)

    def bar_move(self, row: int, other_bar: SignalBar):
        """Move self bar content to other table."""
        bar = self.bars[row]
        for i in range(bar.sig_count):
            bar.sig_move(0, other_bar)
        other_bar.gfx.plot.replot()

    def resize_y_all(self, inc: bool):
        """Resize all bars height by + or -20%."""
        mult = 1.2 if inc else 1 / 1.2
        for bar in self.bars:
            if not bar.is_bool():
                bar.height = round(bar.height * mult)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Intercept QCustomPlot wheel events."""
        if event.type() == QEvent.Wheel and isinstance(obj, BarPlotWidget.BarPlot):
            self.verticalScrollBar().event(event)  # works
            return True
        return False
