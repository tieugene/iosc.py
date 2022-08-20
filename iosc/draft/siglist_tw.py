"""Signal list view
QTableWidget version"""
# 2. 3rd
from PySide2.QtWidgets import QTableWidget, QLabel
# 3. local
import mycomtrade
from sigwidget import SignalCtrlView, SignalChartView


class SignalListView(QTableWidget):

    def __init__(self, slist: mycomtrade.SignalList, parent=None):
        super(SignalListView, self).__init__(parent)
        self.setColumnCount(2)
        self.setRowCount(slist.count)
        for row in range(slist.count):
            ctrl = SignalCtrlView()
            ctrl.set_data(slist[row])
            self.setCellWidget(row, 0, ctrl)
            chart = SignalChartView()
            chart.set_data(slist[row])
            self.setCellWidget(row, 1, chart)
