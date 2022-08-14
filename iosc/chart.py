from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide2.QtCharts import QtCharts
import mycomtrade


class SignalChart(QtCharts.QChart):
    def __init__(self, signal: mycomtrade.Signal):
        def __decorate_x(s):
            # Setting X-axis
            axis: QtCharts.QValueAxis = QtCharts.QValueAxis()
            axis.setTickType(QtCharts.QValueAxis.TicksDynamic)
            axis.setTickInterval(100)
            axis.setTickAnchor(1000 * signal.meta.trigger_time)  # TODO: brush=black
            # print("Anchor:", 1000 * time0)
            axis.setLabelFormat("%d")
            # axis.setLabelsVisible(False)
            # axis_x.setTitleText("Time")  # axis label
            self.addAxis(axis, Qt.AlignBottom)
            s.attachAxis(axis)

        def __decorate_y(s):
            # Setting Y-axis
            axis: QtCharts.QValueAxis = QtCharts.QValueAxis()
            axis.setTickAnchor(0)  # TODO: brush=...
            axis.setTickCount(5)
            # axis.setLabelFormat("%.1f")  # default
            axis.setLabelsVisible(False)
            # axis.setTitleText(v_name)  # axis label
            self.addAxis(axis, Qt.AlignLeft)
            s.attachAxis(axis)

        super(SignalChart, self).__init__()
        series = QtCharts.QLineSeries()
        # Filling QLineSeries
        for i, t in enumerate(signal.time):
            series.append(1000*t, signal.value[i])
        self.addSeries(series)
        # decoration
        __decorate_x(series)
        __decorate_y(series)
        # self.legend().setVisible(False)
        series.setName(signal.sid)
        self.legend().setAlignment(Qt.AlignLeft)


class AnalogSignalChartView(QtCharts.QChartView):
    def __init__(self, asignal: mycomtrade.Signal, parent=None):
        super(AnalogSignalChartView, self).__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setChart(SignalChart(asignal))


class AnalogSignalListView(QWidget):
    def __init__(self, parent=None):
        super(AnalogSignalListView, self).__init__(parent)
        self.setLayout(QVBoxLayout())

    def fill_list(self, alist: mycomtrade.AnalogSignalList):
        for i in range(min(alist.count, 3)):
            self.layout().addWidget(AnalogSignalChartView(alist[i]))


class ComtradeWidget(QWidget):
    analog_panel: AnalogSignalListView
    # digital_panel: QWidget

    def __init__(self, parent=None):
        super(ComtradeWidget, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        # 1. analog part
        self.analog_panel = AnalogSignalListView(splitter)
        splitter.addWidget(self.analog_panel)
        # 2. digital part
        # self.digital_panel = QWidget(splitter)
        # splitter.addWidget(self.digital_panel)
        # 3. lets go
        self.layout().addWidget(splitter)

    def plot_charts(self, rec: mycomtrade.MyComtrade):
        """
        :param rec: Data
        :return:
        """
        self.analog_panel.fill_list(rec.analog)
