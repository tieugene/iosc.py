from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter, QPen
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter, QScrollArea
from PySide2.QtCharts import QtCharts
import mycomtrade
# x. consts
DEFAULT_SIG_COLOR = {'a': 'orange', 'b': 'green', 'c': 'red'}


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
            series.append(1000 * t, signal.value[i])
        self.addSeries(series)
        # decoration
        __decorate_x(series)
        __decorate_y(series)
        # self.legend().setVisible(False)
        # legend on:
        series.setName(signal.sid)
        self.legend().setAlignment(Qt.AlignLeft)
        # color up
        if signal.sid and len(signal.sid) >= 2 and signal.sid[0].lower() in {'i', 'u'}:
            color = DEFAULT_SIG_COLOR.get(signal.sid[1].lower(), 'black')
        else:
            color = 'black'
        pen: QPen = series.pen()
        pen.setWidth(1)
        pen.setColor(color)
        series.setPen(pen)


class SignalChartView(QtCharts.QChartView):
    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super(SignalChartView, self).__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setChart(SignalChart(signal))


class SignalListView(QWidget):
    def __init__(self, parent=None):
        super(SignalListView, self).__init__(parent)
        self.setLayout(QVBoxLayout())

    def fill_list(self, slist: mycomtrade.SignalList, nmax: int = 0):
        for i in range(min(slist.count, nmax) if nmax else slist.count):
            self.layout().addWidget(SignalChartView(slist[i]))


class SignalScrollArea(QScrollArea):
    def __init__(self, panel: QWidget, parent=None):
        super(SignalScrollArea, self).__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(panel)


class ComtradeWidget(QWidget):
    analog_panel: SignalListView
    discret_panel: SignalListView

    def __init__(self, parent=None):
        super(ComtradeWidget, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        # 1. analog part
        self.analog_panel = SignalListView()
        self.analog_scroll = SignalScrollArea(self.analog_panel)
        splitter.addWidget(self.analog_scroll)
        # 2. digital part
        self.discret_panel = SignalListView(splitter)
        self.discret_scroll = SignalScrollArea(self.discret_panel)
        splitter.addWidget(self.discret_scroll)
        # 3. lets go
        self.layout().addWidget(splitter)

    def plot_charts(self, rec: mycomtrade.MyComtrade):
        """
        :param rec: Data
        :return:
        """
        self.analog_panel.fill_list(rec.analog)
        self.discret_panel.fill_list(rec.discret)
