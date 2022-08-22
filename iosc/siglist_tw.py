"""Signal list view
QTableWidget version
:todo: try QTableWidgetItem
"""
# 2. 3rd
from PySide2.QtWidgets import QTableWidget, QAbstractItemView
# 3. local
import mycomtrade
from sigwidget import SignalCtrlView, SignalChartView
# x. const
ANALOG_ROW_HEIGHT = 64


class SignalListView(QTableWidget):

    def __init__(self, slist: mycomtrade.SignalList, parent=None):
        super(SignalListView, self).__init__(parent)
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
        for row in range(slist.count):
            ctrl = SignalCtrlView()
            ctrl.set_data(slist[row])
            self.setCellWidget(row, 0, ctrl)  # or .setItem(row, col, QTableWidgetItem())
            chart = SignalChartView()
            chart.set_data(slist[row])
            self.setCellWidget(row, 1, chart)
            self.setRowHeight(row, ANALOG_ROW_HEIGHT)
            # self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # too high
        # self.resizeRowsToContents()
        self.resizeColumnToContents(0)
        self.horizontalHeader().setStretchLastSection(True)  # FIXME: calc
