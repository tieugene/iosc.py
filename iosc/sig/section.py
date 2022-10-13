"""Mainwidget widget lists"""
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDropEvent, QGuiApplication, QBrush
from PyQt5.QtWidgets import QTableWidget, QWidget, QHeaderView, QTableWidgetItem, QScrollBar
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.common import CleanScrollArea
from iosc.sig.widget.bottom import StatusBarWidget
from iosc.sig.widget.top import TimeAxisWidget
from iosc.sig.widget.ctrl import StatusSignalCtrlWidget, AnalogSignalCtrlWidget
from iosc.sig.widget.chart import SignalScrollArea, StatusSignalChartWidget, AnalogSignalChartWidget


class OneRowTable(QTableWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setRowCount(1)
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionMode(self.NoSelection)
        self.setColumnWidth(0, iosc.const.COL0_WIDTH)
        self.horizontalHeader().setStretchLastSection(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resizeRowsToContents()  # TODO: set fixed


class TimeAxisTable(OneRowTable):
    def __init__(self, osc: mycomtrade.MyComtrade, parent: QWidget):
        super().__init__(parent)
        self.setFixedHeight(self.rowHeight(0) + self.horizontalHeader().height() + iosc.const.XSCALE_H_PAD)
        self.setVerticalHeaderItem(0, QTableWidgetItem('↘'))
        self.setHorizontalHeaderItem(0, QTableWidgetItem('↔'))
        self.setHorizontalHeaderItem(1, QTableWidgetItem('↔'))
        self.setItem(0, 0, QTableWidgetItem("ms"))
        sa = CleanScrollArea(self)
        sa.setWidget(TimeAxisWidget(osc, parent, sa))
        self.setCellWidget(0, 1, sa)
        parent.hsb.valueChanged.connect(sa.horizontalScrollBar().setValue)


class StatusBarTable(OneRowTable):
    def __init__(self, osc: mycomtrade.MyComtrade, parent: QWidget):
        super().__init__(parent)
        self.setFixedHeight(self.rowHeight(0) + iosc.const.XSCALE_H_PAD)
        self.setVerticalHeaderItem(0, QTableWidgetItem('↗'))
        self.horizontalHeader().hide()
        self.setItem(0, 0, QTableWidgetItem(osc.raw.cfg.start_timestamp.date().isoformat()))
        sa = CleanScrollArea(self)
        sa.setWidget(StatusBarWidget(osc, parent, sa))
        self.setCellWidget(0, 1, sa)
        parent.hsb.valueChanged.connect(sa.horizontalScrollBar().setValue)


class SignalListTable(QTableWidget):
    _slist: mycomtrade.SignalList
    _parent: QWidget

    def __init__(self, slist: mycomtrade.SignalList, parent):
        super().__init__(parent)
        self._slist = slist
        self._parent = parent
        self.setColumnCount(2)
        self.setRowCount(len(slist))
        self.setEditTriggers(self.NoEditTriggers)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # not helps
        self.verticalHeader().setMinimumSectionSize(iosc.const.SIG_HEIGHT_MIN)
        self.verticalHeader().setMaximumSectionSize(int(QGuiApplication.screens()[0].availableGeometry().height()*2/3))
        # self.setAutoScroll(False)
        self.setColumnWidth(0, iosc.const.COL0_WIDTH)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().hide()
        # test
        # self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.verticalHeader().setSectionsMovable(True)
        # self.verticalHeader().hide()
        # DnD
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.setDragDropMode(self.InternalMove)
        for row in range(len(slist)):
            # self.insertRow(row)
            self.__apply_row(row, row)

    def dropEvent(self, event: QDropEvent):
        def _drop_on(__evt) -> int:
            # TODO: detect to put over or insert B4
            def _is_below(__pos, __idx) -> bool:
                __rect = self.visualRect(__idx)
                margin = 2
                if __pos.y() - __rect.top() < margin:
                    return False
                elif __rect.bottom() - __pos.y() < margin:
                    return True
                return __rect.contains(__pos, True) \
                       and not (int(self.model().flags(__idx)) & Qt.ItemIsDropEnabled) \
                       and __pos.y() >= __rect.center().y()

            __index = self.indexAt(__evt.pos())
            if not __index.isValid():  # below last
                return self.rowCount()
            return __index.row() + 1 if _is_below(__evt.pos(), __index) else __index.row()

        if event.isAccepted() or event.source() is not self:
            super().dropEvent(event)
            return
        # FIXME: event.accept() and return if before self (like 2=>3)
        dst_row_num = _drop_on(event)
        src_row_num = self.selectedIndexes()[0].row()
        # 1. add
        self.insertRow(dst_row_num)
        if src_row_num > dst_row_num:
            src_row_num += 1
        # 2. copy
        self.setCellWidget(dst_row_num, 0, self.cellWidget(src_row_num, 0))
        self.setCellWidget(dst_row_num, 1, self.cellWidget(src_row_num, 1))
        self.setRowHeight(dst_row_num, self.rowHeight(src_row_num))
        # 3. rm
        self.removeRow(src_row_num)
        # x. that's all
        event.ignore()  # warning: don't accept()!

    def __apply_row(self, row: int, i: int):
        signal = self._slist[i]
        sa = SignalScrollArea(self)
        if signal.is_bool:
            self.setCellWidget(row, 0, ctrl := StatusSignalCtrlWidget(signal, self, self._parent))
            sa.setWidget(StatusSignalChartWidget(signal, sa, self._parent, ctrl))
            self.setCellWidget(row, 1, sa)
            self.setRowHeight(row, iosc.const.SIG_HEIGHT_DEFAULT_D)
        else:
            self.setCellWidget(row, 0, ctrl := AnalogSignalCtrlWidget(signal, self, self._parent))
            sa.setWidget(AnalogSignalChartWidget(signal, sa, self._parent, ctrl))
            self.setCellWidget(row, 1, sa)
            self.setRowHeight(row, iosc.const.SIG_HEIGHT_DEFAULT_A)
        self.setVerticalHeaderItem(row, QTableWidgetItem('↕'))
        self._parent.hsb.valueChanged.connect(sa.horizontalScrollBar().setValue)

    def slot_unhide(self):
        for row in range(self.rowCount()):
            self.showRow(row)

    def whois(self, row: int) -> int:
        """What signal is in the row
        :param row: Row to ask
        :return: Signal No in correspondent signal list
        """
        return self.cellWidget(row, 0).whoami()

    def slot_vzoom_in(self):
        for row in range(self.rowCount()):
            if not self.cellWidget(row, 0).signal.is_bool:
                self.setRowHeight(row, int(self.rowHeight(row) * 1.2))

    def slot_vzoom_out(self):
        for row in range(self.rowCount()):
            if not self.cellWidget(row, 0).signal.is_bool:
                self.setRowHeight(row, int(self.rowHeight(row) / 1.2))


class HScroller(QScrollBar):
    """Bottom scrollbar.
    Subscribers of valueChaged() -> sa.horizontalScrollBar().setValue:
    - TimeAxisTable.__init__()
    - StatuBarTable.__init__()
    - SignalListTable.__init__()
    """
    def __init__(self, parent: QWidget):
        """
        :param parent:
        :type parent: ComtradeWidget
        """
        super().__init__(Qt.Horizontal, parent)
        parent.signal_xscale.connect(self._slot_chart_xscaled)

    def slot_col_resize(self, _: int, w_new: int):
        """Recalc scroller parm on aim column resized with mouse.
        :param _: Old chart column size
        :param w_new: New chart column width
        :todo: link to signal
        """
        self.setPageStep(w_new)
        if (chart_width := self.parent().chart_width) is not None:
            range_new = chart_width - self.pageStep()
            self.setRange(0, range_new)
            if self.value() > range_new:
                self.setValue(range_new)

    def _slot_chart_xscaled(self, w_old: int, w_new: int):
        """Recalc scroller parm on aim column x-scaled.
        :param w_old: Old chart width (px)
        :param w_new: New chart width (px)
        """
        # 1. range
        range_new = w_new - self.pageStep()
        self.setRange(0, range_new)
        if w_old == 0:  # initial => value() == 0
            return
        # 2. start ptr
        b_old = self.value()  # old begin
        if iosc.const.X_CENTERED:
            p_half = self.pageStep() / 2  # relative page mid
            b_new = int(round((b_old + p_half) * w_new / w_old - p_half))  # FIXME: glitches with right list scroller
        else:  # plan B (w/o glitches)
            b_new = b_old
        # 3. limit start ptr
        if b_new < 0:
            b_new = 0
        elif b_new > range_new:
            b_new = range_new
        self.setValue(b_new)
