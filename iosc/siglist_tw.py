"""Signal list view
QTableWidget version
:todo: try QTableWidgetItem
"""
# 2. 3rd
from PySide2.QtWidgets import QTableWidget, QLabel, QAbstractItemView, QHeaderView, QFrame
# 3. local
import mycomtrade
from sigwidget import SignalCtrlView, SignalChartView


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
        # self.setStyleSheet("QTableWidget::item { padding: 0px }")  # not works
        for row in range(slist.count):
            ctrl = SignalCtrlView()
            ctrl.set_data(slist[row])
            self.setCellWidget(row, 0, ctrl)  # or .setItem(row, col, QTableWidgetItem())
            chart = SignalChartView()
            chart.set_data(slist[row])
            self.setCellWidget(row, 1, chart)
            # self.setRowHeight(row, 50)
            # self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # too high
        # self.resizeRowsToContents()
