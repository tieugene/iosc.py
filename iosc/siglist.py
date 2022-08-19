"""Simplest version of signal list"""
# 2. 3rd
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
# 3. local
import mycomtrade
from sigwidget import SignalChartView, SignalCtrlView


class SignalWidget(QWidget):
    label: QLabel
    chartview: SignalChartView

    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super(SignalWidget, self).__init__(parent)
        self.label = SignalCtrlView(signal, self)
        self.chartview = SignalChartView(signal, self)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.chartview)


class SignalListView(QWidget):
    """Analog/Discrete signals list panel"""
    def __init__(self, slist: mycomtrade.SignalList, parent=None):
        super(SignalListView, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        for i in range(slist.count):
            self.layout().addWidget(SignalWidget(slist[i]))
