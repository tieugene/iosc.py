from PySide2.QtCore import Qt, QPointF
from PySide2.QtGui import QPainter, QPen
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter, QScrollArea, QHBoxLayout, QLabel
from PySide2.QtCharts import QtCharts
import mycomtrade
# x. consts
DEFAULT_SIG_COLOR = {'a': 'orange', 'b': 'green', 'c': 'red'}
UNKNOWN_SIG_COLOR = 'black'
Z0_COLOR = 'black'


def signal_color(signal: mycomtrade.Signal):
    if signal.sid and len(signal.sid) >= 2 and signal.sid[0].lower() in {'i', 'u'}:
        return DEFAULT_SIG_COLOR.get(signal.sid[1].lower(), UNKNOWN_SIG_COLOR)
    else:
        return UNKNOWN_SIG_COLOR


class SignalChart(QtCharts.QChart):
    def __init__(self, signal: mycomtrade.Signal):
        def __decorate_x(s):
            # Setting X-axis
            axis: QtCharts.QValueAxis = QtCharts.QValueAxis()
            axis.setTickType(QtCharts.QValueAxis.TicksDynamic)
            axis.setTickAnchor(0)  # dyn
            axis.setTickInterval(100)  # dyn
            # axis.setTickCount(3)  # fixed ticks; >= 2
            # axis.setLabelFormat("%d")
            axis.setLabelsVisible(False)
            # axis.setGridLineVisible(False)  # hide grid
            # axis.setMinorGridLineVisible(False)
            axis.setLineVisible(False)    # hide axis line and ticks
            self.addAxis(axis, Qt.AlignBottom)
            s.attachAxis(axis)

        super(SignalChart, self).__init__()
        series = QtCharts.QLineSeries()
        # Filling QLineSeries
        for i, t in enumerate(signal.time):
            series.append(1000 * (t - signal.meta.trigger_time), signal.value[i])
        self.addSeries(series)
        # decoration
        __decorate_x(series)
        self.legend().setVisible(False)
        # legend on:
        # series.setName(signal.sid)
        # self.legend().setAlignment(Qt.AlignLeft)
        # color up
        pen: QPen = series.pen()
        pen.setWidth(1)
        pen.setColor(signal_color(signal))
        series.setPen(pen)


class SignalChartView(QtCharts.QChartView):
    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super(SignalChartView, self).__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setChart(SignalChart(signal))

    def drawForeground(self, painter, rect):
        painter.save()
        pen = QPen()
        pen.setColor(Z0_COLOR)
        pen.setWidth(1)
        painter.setPen(pen)
        z = self.chart().mapToPosition(QPointF(0, 0))  # point zero
        r = self.chart().plotArea()
        painter.drawLine(QPointF(z.x(), r.top()), QPointF(z.x(), r.bottom()))
        painter.drawLine(QPointF(r.left(), z.y()), QPointF(r.right(), z.y()))
        painter.restore()


class SignalWidget(QWidget):
    label: QLabel
    chartview: SignalChartView

    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super(SignalWidget, self).__init__(parent)
        self.label = QLabel(signal.sid, self)
        self.label.setStyleSheet("QLabel { color : %s; }" % signal_color(signal))
        self.chartview = SignalChartView(signal, self)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.chartview)


class SignalListView(QWidget):
    def __init__(self, parent=None):
        super(SignalListView, self).__init__(parent)
        self.setLayout(QVBoxLayout())

    def fill_list(self, slist: mycomtrade.SignalList, nmax: int = 0):
        for i in range(min(slist.count, nmax) if nmax else slist.count):
            self.layout().addWidget(SignalWidget(slist[i]))


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
