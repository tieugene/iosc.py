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


class SignalChartView(QtCharts.QChartView):
    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super(SignalChartView, self).__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setChart(SignalChart(signal))


class SignalListView(QWidget):
    def __init__(self, parent=None):
        super(SignalListView, self).__init__(parent)
        self.setLayout(QVBoxLayout())

    def fill_list(self, slist: mycomtrade.SignalList, nmax: int):
        for i in range(min(slist.count, nmax)):
            self.layout().addWidget(SignalChartView(slist[i]))


class ComtradeWidget(QWidget):
    analog_panel: SignalListView
    discret_panel: SignalListView

    def __init__(self, parent=None):
        super(ComtradeWidget, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        # 1. analog part
        self.analog_panel = SignalListView(splitter)
        splitter.addWidget(self.analog_panel)
        # 2. digital part
        self.discret_panel = SignalListView(splitter)
        splitter.addWidget(self.discret_panel)
        # 3. lets go
        self.layout().addWidget(splitter)

    def plot_charts(self, rec: mycomtrade.MyComtrade):
        """
        :param rec: Data
        :return:
        """
        self.analog_panel.fill_list(rec.analog, 2)
        self.discret_panel.fill_list(rec.discret, 1)
