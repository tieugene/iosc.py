"""Mainwidget widget lists"""
from typing import Union, Optional

# 2. 3rd
from PyQt5.QtCore import Qt, QPoint, QModelIndex, pyqtSignal, qDebug
from PyQt5.QtGui import QDropEvent, QGuiApplication
from PyQt5.QtWidgets import QTableWidget, QWidget, QHeaderView, QTableWidgetItem, QScrollBar, QListWidgetItem
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.common import CleanScrollArea
from iosc.sig.widget.bottom import StatusBarWidget
from iosc.sig.widget.top import TimeAxisWidget
from iosc.sig.widget.ctrl import SignalCtrlWidget, SignalLabelList, SignalLabel
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
            Detect where droped to
            :param __evt: Drop event
            :return: Pseudo-row number dropped on: 0 = B4 0th, 3 = over 1st, 6 = after 2nd
            """
            __pos = __evt.pos()
            __index = self.indexAt(__pos)
            if not __index.isValid():  # below last
                return self.rowCount() << 1
            __rect = self.visualRect(__index)
            __margin = 2  # FIXME: too strict; find tolerance
            if __pos.y() - __rect.top() < __margin:  # above
                return __index.row() << 1
            elif __rect.bottom() - __pos.y() < __margin:  # below
                return (__index.row() + 1) << 1
            if __rect.contains(__pos, True):  # over
                return (__index.row() << 1) + 1

        def _t_b2n_i(__src_row_num: int, __dst_row_num: int):
            """In-table row move"""
            self.insertRow(__dst_row_num)
            self.setRowHeight(__dst_row_num, self.rowHeight(__src_row_num))
            if __src_row_num > __dst_row_num:
                __src_row_num += 1
            # copy widgets
            self.setCellWidget(__dst_row_num, 0, self.cellWidget(__src_row_num, 0))
            self.setCellWidget(__dst_row_num, 1, self.cellWidget(__src_row_num, 1))
            self.setVerticalHeaderItem(__dst_row_num, QTableWidgetItem(iosc.const.CH_TEXT))

        def _t_b2n_x(__src_table: SignalListTable, __src_row_num: int, __dst_row_num: int):
            """Cross-table row move"""
            self.insertRow(__dst_row_num)
            self.setRowHeight(__dst_row_num, __src_table.rowHeight(__src_row_num))
            # 1. store
            __src_chart: SignalChartWidget = __src_table.cellWidget(__src_row_num, 1).widget()
            __state = __src_chart.state
            __sig_state = [s.state for s in __src_chart.sigraph]
            # 2. del
            __src_table.removeRow(__src_row_num)  # remove old
            # 3. restore
            self.__apply_row(__dst_row_num, __sig_state[0].signal.raw)  # hack
            __dst_chart = self.cellWidget(__dst_row_num, 1).widget()
            __dst_chart.restore(__state)
            for __state in __sig_state:
                __sg = self.__row_add_signal(__dst_row_num, __state.signal)
                __sg.restore(__state)

        def _s_ovr(__src_list: SignalLabelList, __src_row_num: int, __dst_row_num: int, b2n: bool = False):
            """Move signal from one row to another"""
            # store | rm | add | restore
            # 1. store
            __src_label = __src_list.item(__src_row_num)  # SignalLabel
            __src_graph = __src_label.sibling  # SignalGrpah
            __src_chart = __src_graph.graph.parentPlot()
            __sig_state = __src_graph.state
            __chart_state = __src_chart.state
            # 2. rm old
            __src_ctrl = __src_list.parent()  # ?
            __src_ctrl.del_siglabel(__src_label)
            # if __row_ctrl_widget.sig_count() == 0:
            __src_chart.del_sigraph(__src_graph)
            if __src_ctrl.sig_count != __src_chart.sig_count:
                print("Something bad with counters")
            # y. unjoin
            if b2n:  # newly created
                self.setRowHeight(
                    __dst_row_num,
                    iosc.const.SIG_HEIGHT_DEFAULT_D if __sig_state.signal.is_bool else iosc.const.SIG_HEIGHT_DEFAULT_A
                )
                __dst_chart = self.cellWidget(__dst_row_num, 1).widget()
                __dst_chart.restore(__chart_state)
            # 3. add
            __sg = self.__row_add_signal(__dst_row_num, __sig_state.signal)
            # 4. restore
            __sg.restore(__sig_state)
            # x. join (rm old row if required)
            if __src_ctrl.sig_count == 0:
                __src_ctrl.table.removeRow(__src_ctrl.row)

        def _s_b2n(__src_list: SignalLabelList, __src_row_num: int, __dst_row_num: int):
            """Extract signal to separate row"""
            self.insertRow(__dst_row_num)
            self.__apply_row(__dst_row_num, __src_list.item(__src_row_num).signal.raw)
            _s_ovr(__src_list, __src_row_num, __dst_row_num, True)

        if event.isAccepted():
            super().dropEvent(event)
            return
        event.accept()
        if (dst_row_num := _drop_on(event)) is None:
            print("Something wrong (x)")
            event.setDropAction(Qt.IgnoreAction)
            return
        over = bool(dst_row_num & 1)
        dst_row_num >>= 1
        src_object = event.source()  # SignalListTable/SignalLabelList
        event.setDropAction(Qt.IgnoreAction)
        if isinstance(src_object, SignalListTable):  # tbl.
            if over:  # tbl.Ovr
                print("tbl.Ovr %d (1) not supported" % dst_row_num)
            else:  # tbl.B2n
                src_row_num: int = src_object.selectedIndexes()[0].row()
                if src_object == self:
                    if (dst_row_num - src_row_num) in {0, 1}:
                        print("Moving near has no sense")
                    else:
                        print("tbl.B2n.i (2)")
                        _t_b2n_i(src_row_num, dst_row_num)
                        event.setDropAction(Qt.MoveAction)
                else:
                    print("tbl.B2n.x (3)")
                    _t_b2n_x(src_object, src_row_num, dst_row_num)
                    event.setDropAction(Qt.MoveAction)
        elif isinstance(src_object, SignalLabelList):  # sig.
            src_row_num: int = src_object.selectedIndexes()[0].row()
            if over:  # sig.B2n
                print("sig.Ovr %d (4)" % dst_row_num)
                _s_ovr(src_object, src_row_num, dst_row_num)
                # MoveAction clears all of listwidget on sig move
                # event.setDropAction(Qt.MoveAction)
            else:
                if src_object.count() == 1:
                    print("Extracting the only signal has no sense")
                else:
                    print("sig.B2n (5)")
                    _s_b2n(src_object, src_row_num, dst_row_num)
        else:
            print("Unknown src object (y):", src_object.metaObject().className())

    def __apply_row(self, row: int, osc: mycomtrade.Comtrade):
        """
        Prepare newly created table row to fill out with signals.
        :param row: Row number of this table
        :param osc: Comtrade
        """
        self.setVerticalHeaderItem(row, QTableWidgetItem(iosc.const.CH_TEXT))
        self.setCellWidget(row, 0, ctrl := SignalCtrlWidget(self._parent, self))
        self.setCellWidget(row, 1, sa := SignalScrollArea(self))
        sa.setWidget(sw := SignalChartWidget(osc, ctrl, self._parent, sa))
        self._parent.hsb.valueChanged.connect(sa.horizontalScrollBar().setValue)

    def __row_add_signal(self, row: int, signal: mycomtrade.Signal) -> Optional[AnalogSignalGraph]:
        ctrl: SignalCtrlWidget = self.cellWidget(row, 0)
        chart: SignalChartWidget = self.cellWidget(row, 1).widget()
        return chart.add_signal(signal, ctrl.add_signal(signal))

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
