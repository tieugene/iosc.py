"""Signal list view.
QTableWidget version
:todo: try QTableWidgetItem
"""
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import QTableWidget, QLabel, QWidget
# 3. local
import const
import mycomtrade
from sigwidget import TimeAxisView, \
    AnalogSignalCtrlView, AnalogSignalChartView, \
    StatusSignalCtrlView, StatusSignalChartView
from wtable import WHeaderView


class SignalListView(QTableWidget):
    _slist: mycomtrade.SignalList
    _parent: QWidget
    _ti: int

    def __init__(self, slist: mycomtrade.SignalList, ti: int, parent):
        super().__init__(parent)
        self._slist = slist
        self._ti = ti
        self._parent = parent
        self.setColumnCount(2)
        self.setRowCount(len(slist))
        self.setEditTriggers(self.NoEditTriggers)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        # self.setAutoScroll(False)
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
            self.__insert_row(row)

    def dropEvent(self, event: QDropEvent):
        def _drop_on(__evt) -> int:
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

        if not event.isAccepted() and event.source() == self:
            dst_row_num = _drop_on(event)
            src_row_num = self.selectedIndexes()[0].row()
            self.insertRow(dst_row_num)
            if src_row_num > dst_row_num:
                src_row_num += 1
            # 2. move
            for column in range(self.columnCount()):
                self.setItem(dst_row_num, column, self.takeItem(src_row_num, column))
                self.setCellWidget(dst_row_num, column, self.cellWidget(src_row_num, column))
            # 3. drop old
            self.removeRow(src_row_num)
            if dst_row_num > src_row_num:
                dst_row_num -= 1
            # x. that's all
            event.accept()
            self.reset()
            # self.item(dst_row_num, 0).setSelected(True)
            # self.item(dst_row_num, 1).setSelected(True)
            # FIXME: dst is empty => drop row and recreate it
            # TODO: inner data independent Signal*Widget
        super().dropEvent(event)

    def __insert_row(self, row: int):
        signal = self._slist[row]
        if signal.is_bool:
            self.setCellWidget(row, 0, ctrl := StatusSignalCtrlView(signal, self, self._parent))
            self.setCellWidget(row, 1, StatusSignalChartView(signal, self._ti, self, self._parent, ctrl))
            self.setRowHeight(row, const.SIG_D_HEIGHT)
        else:
            self.setCellWidget(row, 0, ctrl := AnalogSignalCtrlView(signal, self, self._parent))
            self.setCellWidget(row, 1, AnalogSignalChartView(signal, self._ti, self, self._parent, ctrl))
            self.setRowHeight(row, const.SIG_A_HEIGHT)

    def slot_lineup(self, dwidth: int):
        """Resize columns according to requirements.
        :param dwidth: Main window widths subtraction (available - actual)
        :fixme: subtract something (vheader width?)
        """
        self.setColumnWidth(0, const.COL0_WIDTH)
        self.setColumnWidth(1, self.width() + dwidth - const.COL0_WIDTH - 48)  # FIXME: magic number

    def slot_unhide(self):
        for row in range(self.rowCount()):
            self.showRow(row)


class AnalogSignalListView(SignalListView):
    time_axis: TimeAxisView

    def __init__(self, slist: mycomtrade.AnalogSignalList, ti: int, parent):
        super().__init__(slist, ti, parent)
        self.setHorizontalHeader(WHeaderView(self))
        self.setHorizontalHeaderLabels(('', ''))  # clean defaults
        self.horizontalHeader().set_widget(0, QLabel("ms"))
        self.time_axis = TimeAxisView(slist.raw.time[0], slist.raw.trigger_time, slist.raw.time[-1], ti, self, parent)
        self.horizontalHeader().set_widget(1, self.time_axis)
        self.horizontalHeader().setFixedHeight(const.XSCALE_HEIGHT)

    def scrollContentsBy(self, dx: int, dy: int):
        super().scrollContentsBy(dx, dy)
        if dx:
            self.horizontalHeader().fix_widget_positions()


class StatusSignalListView(SignalListView):
    def __init__(self, slist: mycomtrade.StatusSignalList, ti: int, parent):
        super().__init__(slist, ti, parent)
        self.horizontalHeader().hide()
