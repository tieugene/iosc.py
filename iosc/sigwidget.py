# 2. 3rd
from PySide2.QtCore import Qt, QPointF
from PySide2.QtGui import QPainter, QPen
from PySide2.QtCharts import QtCharts
from PySide2.QtWidgets import QLabel
# 3. local
import mycomtrade
# x. const
DEFAULT_SIG_COLOR = {'a': 'orange', 'b': 'green', 'c': 'red'}
UNKNOWN_SIG_COLOR = 'black'
Z0_COLOR = 'black'
CHART_MIN_HEIGHT = 50


def signal_color(signal: mycomtrade.Signal):
    if signal.sid and len(signal.sid) >= 2 and signal.sid[0].lower() in {'i', 'u'}:
        return DEFAULT_SIG_COLOR.get(signal.sid[1].lower(), UNKNOWN_SIG_COLOR)
    else:
        return UNKNOWN_SIG_COLOR


class SignalChart(QtCharts.QChart):
    series: QtCharts.QLineSeries
    xaxis: QtCharts.QValueAxis

    def __init__(self, ti: int, parent=None):
        super(SignalChart, self).__init__(parent)
        self.legend().hide()
        # self.legend().setVisible(False)
        # self.setMinimumHeight(CHART_MIN_HEIGHT)  # FIXME: dirty hack
        self.series = QtCharts.QLineSeries()
        # decorate X-axis
        self.xaxis = QtCharts.QValueAxis()
        self.xaxis.setTickType(QtCharts.QValueAxis.TicksDynamic)
        self.xaxis.setTickAnchor(0)  # dyn
        self.xaxis.setTickInterval(ti)  # dyn
        # axis.setTickCount(3)  # fixed ticks; >= 2
        # axis.setLabelFormat("%d")
        self.xaxis.setLabelsVisible(False)
        self.xaxis.setGridLineVisible(True)
        # axis.setMinorGridLineVisible(False)
        self.xaxis.setLineVisible(False)  # hide axis line and ticks
        self.addAxis(self.xaxis, Qt.AlignBottom)
        # expand
        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored, QSizePolicy.DefaultType)  # no effect

    def set_data(self, signal: mycomtrade.Signal):
        # Filling QLineSeries
        for i, t in enumerate(signal.time):
            self.series.append(1000 * (t - signal.meta.trigger_time), signal.value[i])
        self.addSeries(self.series)  # Note: attach after filling up, not B4
        self.series.attachAxis(self.xaxis)  # Note: attach after adding series to self, not B4
        # color up
        pen: QPen = self.series.pen()
        pen.setWidth(1)
        pen.setColor(signal_color(signal))
        self.series.setPen(pen)


class SignalChartView(QtCharts.QChartView):
    def __init__(self, ti: int, parent=None):
        super(SignalChartView, self).__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setChart(SignalChart(ti))

    def drawForeground(self, painter, _):
        """
        :param painter:
        :param _: == rect
        :todo: not plots for discrete const Y=1
        """
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

    def set_data(self, signal: mycomtrade.Signal):
        self.chart().set_data(signal)


class SignalCtrlView(QLabel):
    def __init__(self, parent=None):
        super(SignalCtrlView, self).__init__(parent)

    def set_data(self, signal: mycomtrade.Signal):
        self.setStyleSheet("QLabel { color : %s; }" % signal_color(signal))
        self.setText(signal.sid)
