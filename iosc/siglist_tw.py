"""Signal list view.
QTableWidget version
:todo: try QTableWidgetItem
"""
# 2. 3rd
from PyQt5.QtWidgets import QTableWidget, QLabel
# 3. local
import const
import mycomtrade
from sigwidget import TimeAxisView, \
    AnalogSignalCtrlView, AnalogSignalChartView, \
    StatusSignalCtrlView, StatusSignalChartView
from wtable import WHeaderView


class SignalListView(QTableWidget):
    slist: mycomtrade.SignalList

    def __init__(self, slist: mycomtrade.SignalList, ti: int, parent):
        super().__init__(parent)
        self.slist = slist
        self.setColumnCount(2)
        self.setRowCount(len(slist))
        self.setEditTriggers(self.NoEditTriggers)
        # self.setSelectionBehavior(self.NoSelection)
        self.setSelectionMode(self.NoSelection)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setAutoScroll(False)
        for row in range(len(slist)):
            signal = slist[row]
            if signal.is_bool:
                self.setCellWidget(row, 0, ctrl := StatusSignalCtrlView(signal, self, parent))
                self.setCellWidget(row, 1, StatusSignalChartView(signal, ti, self, parent, ctrl))
                self.setRowHeight(row, const.SIG_D_HEIGHT)
            else:
                self.setCellWidget(row, 0, ctrl := AnalogSignalCtrlView(signal, self, parent))
                self.setCellWidget(row, 1, AnalogSignalChartView(signal, ti, self, parent, ctrl))
                self.setRowHeight(row, const.SIG_A_HEIGHT)

    def line_up(self, dwidth: int):
        """Resize columns according to requirements.
        :param dwidth: Main window widths subtraction (available - actual)
        :fixme: subtract something (vheader width?)
        """
        self.setColumnWidth(0, const.COL0_WIDTH)
        self.setColumnWidth(1, self.width() + dwidth - const.COL0_WIDTH - 48)  # FIXME: magic number

    def sig_unhide(self):
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
