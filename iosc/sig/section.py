"""Mainwidget widget lists"""
from typing import Union, Optional

# 2. 3rd
from PyQt5.QtCore import Qt, QPoint, QModelIndex, pyqtSignal
from PyQt5.QtGui import QDropEvent, QGuiApplication
from PyQt5.QtWidgets import QTableWidget, QWidget, QHeaderView, QTableWidgetItem, QScrollBar
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.common import CleanScrollArea
from iosc.sig.widget.bottom import StatusBarWidget
from iosc.sig.widget.top import TimeAxisWidget
from iosc.sig.widget.ctrl import SignalCtrlWidget
from iosc.sig.widget.chart import SignalScrollArea, SignalChartWidget, AnalogSignalGraph


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
    widget: TimeAxisWidget

    def __init__(self, osc: mycomtrade.MyComtrade, parent: QWidget):
        super().__init__(parent)
        self.setFixedHeight(self.rowHeight(0) + self.horizontalHeader().height() + iosc.const.XSCALE_H_PAD)
        self.setVerticalHeaderItem(0, QTableWidgetItem('↘'))
        self.setHorizontalHeaderItem(0, QTableWidgetItem('↔'))
        self.setHorizontalHeaderItem(1, QTableWidgetItem('↔'))
        self.setItem(0, 0, QTableWidgetItem("ms"))
        sa = CleanScrollArea(self)
        self.widget = TimeAxisWidget(osc, parent, sa)
        sa.setWidget(self.widget)
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
    s_id: str  # for debug
    _slist: Union[mycomtrade.StatusSignalList, mycomtrade.AnalogSignalList]
    _parent: QWidget
    signal_rmrow = pyqtSignal(int)

    def __init__(self, slist: Union[mycomtrade.StatusSignalList, mycomtrade.AnalogSignalList], parent):
        super().__init__(parent)
        self._slist = slist
        self._parent = parent
        self.setColumnCount(2)
        self.setRowCount(len(slist))
        self.setEditTriggers(self.NoEditTriggers)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # not helps
        self.verticalHeader().setMinimumSectionSize(iosc.const.SIG_HEIGHT_MIN)
        self.verticalHeader().setMaximumSectionSize(
            int(QGuiApplication.screens()[0].availableGeometry().height() * 2 / 3))
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
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)
        # DnD
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.DragDrop)  # was self.InternalMove
        for row in range(len(slist)):
            self.__apply_row(row, self._slist[row].raw)
            self.__row_add_signal(row, self._slist[row])
            self.setRowHeight(row, iosc.const.SIG_HEIGHT_DEFAULT_D if self._slist[row].is_bool else iosc.const.SIG_HEIGHT_DEFAULT_A)
        self.signal_rmrow.connect(self.removeRow)
        self.s_id = 'base'

    def dropEvent(self, event: QDropEvent):
        def _drop_on(__evt: QDropEvent) -> int:
            """
            ... where drop to
            :param __evt: Drop event
            :return: Row number dropped before
            :todo: detect to put over or insert B4
            """

            def _is_below(__pos: QPoint, __idx: QModelIndex) -> bool:
                """
                Check whether drop below given row
                :param __pos: Position of dropping
                :param __idx: Index of row to check
                :return: True if below
                """
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

        def _i_move(__src_row_num: int):
            """In-table row movement"""
            # copy widgets
            self.setCellWidget(dst_row_num, 0, src_table.cellWidget(__src_row_num, 0))
            self.setCellWidget(dst_row_num, 1, src_table.cellWidget(__src_row_num, 1))
            self.setVerticalHeaderItem(dst_row_num, QTableWidgetItem(iosc.const.CH_TEXT))

        def _x_move(__src_row_num: int):
            """Cross-table row movement"""
            # 1. store
            chart: SignalChartWidget = src_table.cellWidget(__src_row_num, 1).widget()
            state = chart.state
            sig_state = []
            for sig in chart.sigraph:
                sig_state.append(sig.state)
            # 2. del
            src_table.removeRow(__src_row_num)  # remove old
            # 3. restore
            self.__apply_row(dst_row_num, sig_state[0].signal.raw)  # hack
            chart = self.cellWidget(dst_row_num, 1).widget()
            chart.restore(state)
            for state in sig_state:
                if sg := self.__row_add_signal(dst_row_num, state.signal):
                    sg.restore(state)

        if event.isAccepted():
            super().dropEvent(event)
            return
        # FIXME: event.drop() and return if before[/after?] self (like 2=>3)
        event.setDropAction(Qt.MoveAction)
        event.accept()
        src_table: QTableWidget = event.source()
        src_row_num: int = src_table.selectedIndexes()[0].row()
        dst_row_num: int = _drop_on(event)
        # 1. add
        self.insertRow(dst_row_num)
        if src_table == self:
            _i_move(src_row_num + 1 if src_row_num > dst_row_num else src_row_num)
        else:
            _x_move(src_row_num)
        self.setRowHeight(dst_row_num, src_table.rowHeight(src_row_num))

    def __apply_row(self, row: int, osc: mycomtrade.Comtrade):
        """

        :param row: Row number of this table
        :param osc: Comtrade
        :return:
        """
        self.setVerticalHeaderItem(row, QTableWidgetItem(iosc.const.CH_TEXT))
        self.setCellWidget(row, 0, ctrl := SignalCtrlWidget(self._parent, self))
        self.setCellWidget(row, 1, sa := SignalScrollArea(self))
        sa.setWidget(sw := SignalChartWidget(osc, ctrl, self._parent, sa))
        self._parent.hsb.valueChanged.connect(sa.horizontalScrollBar().setValue)

    def __row_add_signal(self, row: int, signal: mycomtrade.Signal) -> Optional[AnalogSignalGraph]:
        ctrl: SignalCtrlWidget = self.cellWidget(row, 0)
        chart: SignalChartWidget = self.cellWidget(row, 1).widget()
        sg = chart.add_signal(signal, ctrl.add_signal(signal))
        if not signal.is_bool:
            self._parent.sig_no2widget[signal.i] = sg
            return sg

    def slot_unhide(self):
        for row in range(self.rowCount()):
            self.showRow(row)

    def whois(self, row: int) -> int:
        """What signal is in the row
        :param row: Row to ask
        :return: Signal No in correspondent signal list
        """
        return self.cellWidget(row, 0).whoami

    def slot_vzoom_in(self):
        for row in range(self.rowCount()):
            # if not self.cellWidget(row, 0).signal.is_bool:  FIXME:
            self.setRowHeight(row, int(self.rowHeight(row) * 1.2))

    def slot_vzoom_out(self):
        for row in range(self.rowCount()):
            # if not self.cellWidget(row, 0).signal.is_bool:  # FIXME:
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
