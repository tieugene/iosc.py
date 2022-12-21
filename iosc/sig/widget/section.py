"""Mainwidget widget lists"""
# 1. std
from typing import Tuple
# 2. 3rd
from PyQt5.QtCore import Qt, pyqtSignal, QMargins
from PyQt5.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent, QPainter
from PyQt5.QtWidgets import QTableWidget, QWidget, QHeaderView, QScrollBar, QLabel, QHBoxLayout, QProxyStyle, QStyle,\
    QStyleOption
from QCustomPlot2 import QCustomPlot
# 3. local
import iosc.const
from iosc.sig.widget.common import SignalBar, SignalBarList
from iosc.sig.widget.ctrl import BarCtrlWidget
from iosc.sig.widget.top import TimeAxisPlot
from iosc.sig.widget.bottom import TimeStampsPlot


class OneRowBar(QWidget):
    class RStub(QScrollBar):
        def __init__(self, parent: 'OneRowBar' = None):
            super().__init__(Qt.Vertical, parent)
            self.setFixedHeight(0)

    _label: QLabel
    plot: QCustomPlot

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self._label = QLabel(self)

    def _post_init(self):
        # layout
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self._label)
        self.layout().addWidget(self.plot)
        self.layout().addWidget(self.RStub())
        self.layout().addWidget(self.RStub())
        # squeeze
        self.layout().setContentsMargins(QMargins())
        self.layout().setSpacing(0)
        self._label.setContentsMargins(QMargins())
        # init sizes
        self.__slot_resize_col_ctrl(self.parent().col_ctrl_width)
        self.parent().signal_resize_col_ctrl.connect(self.__slot_resize_col_ctrl)

    def __slot_resize_col_ctrl(self, x: int):
        self._label.setFixedWidth(x + iosc.const.LINE_CELL_SIZE)


class TimeAxisBar(OneRowBar):
    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self._label.setText('ms')
        self.plot = TimeAxisPlot(self)
        self._post_init()


class TimeStampsBar(OneRowBar):
    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.plot = TimeStampsPlot(self)
        self._post_init()


class SignalBarTable(QTableWidget):
    class DropmarkerStyle(QProxyStyle):
        def drawPrimitive(
                self,
                element: QStyle.PrimitiveElement,
                option: QStyleOption,
                painter: QPainter,
                widget: QWidget = None) -> None:
            if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
                pen = painter.pen()
                pen.setColor(Qt.red)
                painter.setPen(pen)
            super().drawPrimitive(element, option, painter, widget)

    oscwin: 'ComtradeWidget'
    bars: SignalBarList

    def __init__(self, oscwin: 'ComtradeWidget'):
        super().__init__()  # Parent will be QSplitter
        self.oscwin = oscwin
        self.setColumnCount(2)
        self.bars = list()
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
        self.setStyleSheet("QTableWidget:focus {border: 3px solid blue;}")
        # DnD
        # self.setDragEnabled(True)  # default=False
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(self.DragDropMode.DropOnly)  # default=DragDrop
        # signals/slot
        self.oscwin.signal_resize_col_ctrl.connect(self.__slot_resize_col_ctrl)

    def insertRow(self, row: int):
        super().insertRow(row)
        for i in range(row + 1, len(self.bars)):
            self.bars[i].row = i

    def removeRow(self, row: int):
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
                        src_object.parent().bar.table != self or
                        (dst_row_num - src_object.parent().bar.row) not in {0, 1}
                    )
            elif isinstance(src_object, BarCtrlWidget.SignalLabelList):
                if over:
                    return 2 * int(src_object.parent().bar.table != self or src_object.parent().bar.row != dst_row_num)
                else:  # sig.Ins
                    return 3 * int(src_object.count() > 1)
        return 0

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self.__chk_dnd_source(event):
            super().dragEnterEvent(event)  # paint decoration + accept

    def dragMoveEvent(self, event: QDragMoveEvent):
        super().dragMoveEvent(event)  # paint decoration
        dst_row_num, over = self.__drop_on(event)
        # TODO: cache prev
        if self.__chk_dnd_event(event.source(), dst_row_num, over):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.isAccepted():
            super().dropEvent(event)
            return
        src_object = event.source()
        dst_row_num, over = self.__drop_on(event)  # SignalBarTable/SignalLabelList
        todo = self.__chk_dnd_event(src_object, dst_row_num, over)
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
        return SignalBar(self, row)

    def bar_move(self, row: int, other_bar: SignalBar):
        """Move self bar content to other"""
        bar = self.bars[row]
        for i in range(bar.sig_count):
            bar.sig_move(0, other_bar)
        other_bar.gfx.plot.replot()

    def resize_y_all(self, inc: bool):
        mult = 1.2 if inc else 1 / 1.2
        for bar in self.bars:
            if not bar.is_bool():
                bar.height = round(bar.height * mult)


class XScroller(QScrollBar):
    signal_update_plots = pyqtSignal()

    def __init__(self, parent: 'ComtradeWidget'):
        """
        :param parent:
        :type parent: ComtradeWidget
        :note: An idea:
        - full width = plot width (px)
        - page size = current col1 width (px)
        """
        super().__init__(Qt.Horizontal, parent)
        parent.signal_x_zoom.connect(self.__slot_update_range)
        parent.timeaxis_bar.plot.signal_width_changed.connect(self.__slot_update_page)

    @property
    def norm_min(self) -> float:
        """Normalized (0..1) left page position"""
        return self.value() / (self.maximum() + self.pageStep())

    @property
    def norm_max(self) -> float:
        """Normalized (0..1) right page position"""
        return (self.value() + self.pageStep()) / (self.maximum() + self.pageStep())

    def __update_enabled(self):
        self.setEnabled(self.maximum() > 0)

    def __slot_update_range(self):
        """Update maximum against new x-zoom.
        (x_width_px changed, page (px) - not)"""
        page = self.pageStep()
        x_width_px = self.parent().x_width_px()
        if (max_new := x_width_px - self.pageStep()) < 0:
            max_new = 0
        v_new = min(
            max_new,
            max(
                0,
                round((self.value() + page / 2) / (self.maximum() + page) * x_width_px - (page / 2))
            )
        )
        self.setMaximum(max_new)
        if v_new != self.value():
            self.setValue(v_new)  # emit signal
        else:
            self.signal_update_plots.emit()
        self.__update_enabled()

    def __slot_update_page(self, new_page: int):
        """Update page against new signal windows width"""
        x_max = self.parent().x_width_px()
        if min(new_page, self.pageStep()) < x_max:
            if new_page > x_max:
                new_page = x_max
            self.setPageStep(new_page)
            v0 = self.value()
            self.setMaximum(self.parent().x_width_px() - new_page)  # WARN: value changed w/o signal emit
            if self.value() == v0:
                self.signal_update_plots.emit()  # Force update plots; plan B: self.valueChanged.emit(self.value())
        self.__update_enabled()
