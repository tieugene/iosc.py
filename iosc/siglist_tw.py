"""Signal list view
QTableWidget version
:todo: try QTableWidgetItem
"""
# 2. 3rd
from PySide2.QtWidgets import QTableWidget, QAbstractItemView, QLabel, QHeaderView, QGraphicsOpacityEffect
# 3. local
import mycomtrade
from sigwidget import SignalCtrlView, SignalChartView, TimeAxisView
from wtable import WHTableWidget
# x. const
ANALOG_ROW_HEIGHT = 64
TIMELINE_HEIGHT = 100


class SignalListView(WHTableWidget):
    slist: mycomtrade.SignalList
    time_axis: TimeAxisView

    def __init__(self, slist: mycomtrade.SignalList, ti: int, parent=None):
        super().__init__(parent)
        self.slist = slist
        self.setColumnCount(2)
        self.setRowCount(slist.count)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.setShowGrid(True)  # default
        # self.setContentsMargins(0, 0, 0, 0)  # not works
        # self.setFrameStyle(QFrame.NoFrame)  # remove table outer frame lines
        # self.verticalHeader().setVisible(False)
        # self.horizontalHeader().setVisible(False)
        # self.setSelectionBehavior(QAbstractItemView.NoSelection)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        # self.setStyleSheet("QTableWidget::item { padding: 0; margin: 0; }")  # not works
        # specials (all columns must be set)
        self.setHorizontalHeaderLabels((None, None))  # clean defaults
        self.horizontalHeader().set_widget(0, QLabel("ms"))
        self.time_axis = TimeAxisView(slist.time[0], slist.trigger_time, slist.time[-1], ti)
        self.horizontalHeader().set_widget(1, self.time_axis)
        self.horizontalHeader().setFixedHeight(TIMELINE_HEIGHT)  # FIXME: dirty hack
        # self.horizontalHeader().set_widget(1, QLabel("One"))
        for row in range(slist.count):
            ctrl = SignalCtrlView(self)
            ctrl.set_data(slist[row])
            self.setCellWidget(row, 0, ctrl)  # or .setItem(row, col, QTableWidgetItem())
            chart = SignalChartView(ti, self)
            chart.set_data(slist[row])
            self.setCellWidget(row, 1, chart)
            self.setRowHeight(row, ANALOG_ROW_HEIGHT)
            # self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # too high
        # self.resizeRowsToContents()
        # <dbg>
        # self.setCellWidget(0, 1, self.time_axis)
        # </dbg>
        self.resizeColumnToContents(0)
        # self.horizontalHeader().setStretchLastSection(True)  # FIXME: calc; default = 100

    def line_up(self, dwidth: int, w0: int):
        """Resize columns according to requirements.
        :param dwidth: Main window widths subtraction (available - actual)
        :param w0: Width of 0th column
        :fixme: subtract something (vheader width?)
        """
        self.setColumnWidth(0, w0)
        self.setColumnWidth(1, self.width() + dwidth - w0 - 48)  # FIXME: magic number
