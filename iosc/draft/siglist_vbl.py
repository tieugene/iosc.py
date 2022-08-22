"""Signal list view.
QVBoxLayout version"""
# 2. 3rd
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
# 3. local
import mycomtrade
from sigwidget import SignalChartView, SignalCtrlView


class SignalWidget(QWidget):
    label: QLabel
    chartview: SignalChartView

    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super(SignalWidget, self).__init__(parent)
        self.label = SignalCtrlView(self)
        self.chartview = SignalChartView(self)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.chartview)
        # ---
        self.label.set_data(signal)
        self.chartview.set_data(signal)


class SignalListWidget(QWidget):
    """Analog/Discrete signals list panel"""

    def __init__(self, slist: mycomtrade.SignalList, parent=None):
        super(SignalListWidget, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        for i in range(slist.count):
            self.layout().addWidget(SignalWidget(slist[i]))


class SignalListView(QScrollArea):
    def __init__(self, slist: mycomtrade.SignalList, parent=None):
        super(SignalListView, self).__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(SignalListWidget(slist))
