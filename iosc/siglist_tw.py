"""Signal list view.
QTableWidget version
:todo: try QTableWidgetItem
"""
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDropEvent, QGuiApplication
from PyQt5.QtWidgets import QTableWidget, QLabel, QWidget
# 3. local
import const
import mycomtrade
from sigwidget import TimeAxisView, \
    AnalogSignalCtrlView, AnalogSignalChartView, \
    StatusSignalCtrlView, StatusSignalChartView, SignalScrollArea
from wtable import WHeaderView


class SignalListView(QTableWidget):
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
            self.setCellWidget(row, 0, ctrl := StatusSignalCtrlView(signal, self, self._parent))
            # self.setCellWidget(row, 1, StatusSignalChartView(signal, self, self._parent, ctrl))
            sa.setWidget(StatusSignalChartView(signal, sa, self._parent, ctrl))
            self.setCellWidget(row, 1, sa)
            self.setRowHeight(row, const.SIG_HEIGHT_DEFAULT_D)
        else:
            self.setCellWidget(row, 0, ctrl := AnalogSignalCtrlView(signal, self, self._parent))
            sa.setWidget(AnalogSignalChartView(signal, sa, self._parent, ctrl))
            self.setCellWidget(row, 1, sa)
            self.setRowHeight(row, const.SIG_HEIGHT_DEFAULT_A)
        self.verticalHeader().setMinimumSectionSize(const.SIG_HEIGHT_MIN)
        self.verticalHeader().setMaximumSectionSize(int(QGuiApplication.screens()[0].availableGeometry().height()*2/3))
        # self.verticalHeader().hide()

    def slot_lineup(self):
        """Resize columns according to requirements.
        :fixme: subtract something (vheader width?)
        """
        w_screen = QGuiApplication.screens()[0].availableGeometry().width()  # all available desktop (e.g. 1280)
        w_main = QGuiApplication.topLevelWindows()[0].width()  # current main window width (e.g. 960)
        w_self = self.width()  # current [table] widget width  (e.g. 940)
        self.setColumnWidth(0, const.COL0_WIDTH)
        self.setColumnWidth(1, w_self + (w_screen - w_main) - const.COL0_WIDTH - const.MAGIC_WIDHT)

    def slot_unhide(self):
        for row in range(self.rowCount()):
            self.showRow(row)

    def whois(self, row: int) -> int:
        """What signal is in the row
        :param row: Row to ask
        :return: Signal No in correspondent signal list
        """
        return self.cellWidget(row, 0).whoami()

    def slot_zoom_in(self):
        for row in range(self.rowCount()):
            if not self.cellWidget(row, 0).signal.is_bool:
                self.setRowHeight(row, int(self.rowHeight(row) * 1.2))

    def slot_zoom_out(self):
        for row in range(self.rowCount()):
            if not self.cellWidget(row, 0).signal.is_bool:
                self.setRowHeight(row, int(self.rowHeight(row) / 1.2))


class AnalogSignalListView(SignalListView):
    time_axis: TimeAxisView

    def __init__(self, slist: mycomtrade.AnalogSignalList, parent):
        super().__init__(slist, parent)
        self.setHorizontalHeader(WHeaderView(self))
        self.setHorizontalHeaderLabels(('', ''))  # clean defaults
        self.horizontalHeader().set_widget(0, QLabel("ms"))
        self.time_axis = TimeAxisView(slist.raw.time[0], slist.raw.trigger_time, slist.raw.time[-1], self, parent)
        self.horizontalHeader().set_widget(1, self.time_axis)
        self.horizontalHeader().setFixedHeight(const.XSCALE_HEIGHT)

    def scrollContentsBy(self, dx: int, dy: int):
        super().scrollContentsBy(dx, dy)
        if dx:
            self.horizontalHeader().fix_widget_positions()


class StatusSignalListView(SignalListView):
    def __init__(self, slist: mycomtrade.StatusSignalList, parent):
        super().__init__(slist, parent)
        self.horizontalHeader().hide()
