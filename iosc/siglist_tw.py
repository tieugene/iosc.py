"""Signal list view
QTableWidget version
:todo: try QTableWidgetItem
"""
from PySide2.QtCore import Qt
# 2. 3rd
from PySide2.QtWidgets import QTableWidget, QAbstractItemView, QLabel
# 3. local
import mycomtrade
from sigwidget import TIMELINE_HEIGHT, TimeAxisView, \
    AnalogSignalCtrlView, AnalogSignalChartView, StatusSignalCtrlView, StatusSignalChartView
from wtable import WHeaderView
# x. const
ANALOG_ROW_HEIGHT = 64


class SignalListView(QTableWidget):
    slist: mycomtrade.SignalList

    def __init__(self, slist: mycomtrade.SignalList, ti: int, parent=None):
        super().__init__(parent)
        self.slist = slist
        self.setColumnCount(2)
        self.setRowCount(slist.count)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.setSelectionBehavior(QAbstractItemView.NoSelection)
        self.setSelectionMode(QAbstractItemView.NoSelection)

    def line_up(self, dwidth: int, w0: int):
        """Resize columns according to requirements.
        :param dwidth: Main window widths subtraction (available - actual)
        :param w0: Width of 0th column
        :fixme: subtract something (vheader width?)
        """
        self.setColumnWidth(0, w0)
        self.setColumnWidth(1, self.width() + dwidth - w0 - 48)  # FIXME: magic number


class AnalogSignalListView(SignalListView):
    time_axis: TimeAxisView

    def __init__(self, slist: mycomtrade.AnalogSignalList, ti: int, parent=None):
        super().__init__(slist, ti, parent)
        self.setHorizontalHeader(WHeaderView(Qt.Orientation.Horizontal, self))
        self.setHorizontalHeaderLabels((None, None))  # clean defaults
        self.horizontalHeader().set_widget(0, QLabel("ms"))
        self.time_axis = TimeAxisView(slist.time[0], slist.trigger_time, slist.time[-1], ti)
        self.horizontalHeader().set_widget(1, self.time_axis)
        self.horizontalHeader().setFixedHeight(TIMELINE_HEIGHT)  # FIXME: dirty hack
        for row in range(slist.count):
            ctrl = AnalogSignalCtrlView(self)
            ctrl.set_data(slist[row])
            self.setCellWidget(row, 0, ctrl)  # or .setItem(row, col, QTableWidgetItem())
            chart = AnalogSignalChartView(ti, self)
            chart.set_data(slist[row])
            self.setCellWidget(row, 1, chart)
            self.setRowHeight(row, ANALOG_ROW_HEIGHT)
            # self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # too high
        # self.resizeRowsToContents()
        self.resizeColumnToContents(0)

    def scrollContentsBy(self, dx: int, dy: int):
        super().scrollContentsBy(dx, dy)
        if dx:
            self.horizontalHeader().fix_widget_positions()


class StatusSignalListView(SignalListView):
    def __init__(self, slist: mycomtrade.StatusSignalList, ti: int, parent=None):
        super().__init__(slist, ti, parent)
        self.horizontalHeader().hide()
        # self.horizontalHeader().setVisible(False)
        for row in range(slist.count):
            ctrl = StatusSignalCtrlView(self)
            ctrl.set_data(slist[row])
            self.setCellWidget(row, 0, ctrl)
            chart = StatusSignalChartView(ti, self)
            chart.set_data(slist[row])
            self.setCellWidget(row, 1, chart)
        self.resizeRowsToContents()
        self.resizeColumnToContents(0)
