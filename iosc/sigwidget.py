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


def signal_color(signal: mycomtrade.Signal):
    if signal.sid and len(signal.sid) >= 2 and signal.sid[0].lower() in {'i', 'u'}:
        return DEFAULT_SIG_COLOR.get(signal.sid[1].lower(), UNKNOWN_SIG_COLOR)
    else:
        return UNKNOWN_SIG_COLOR


class SignalChart(QtCharts.QChart):
    series: QtCharts.QLineSeries

    def __init__(self, parent=None):
        super(SignalChart, self).__init__(parent)
        self.legend().setVisible(False)
        self.setMinimumHeight(100)  # FIXME: dirty hack
        self.series = QtCharts.QLineSeries()
        # decoration
        axis: QtCharts.QValueAxis = QtCharts.QValueAxis()
        axis.setTickType(QtCharts.QValueAxis.TicksDynamic)
        axis.setTickAnchor(0)  # dyn
        axis.setTickInterval(100)  # dyn
        # axis.setTickCount(3)  # fixed ticks; >= 2
        # axis.setLabelFormat("%d")
        axis.setLabelsVisible(False)
        # axis.setGridLineVisible(False)  # hide grid
        # axis.setMinorGridLineVisible(False)
        axis.setLineVisible(False)  # hide axis line and ticks
        self.addAxis(axis, Qt.AlignBottom)
        self.series.attachAxis(axis)

    def set_data(self, signal: mycomtrade.Signal):
        # Filling QLineSeries
        for i, t in enumerate(signal.time):
            self.series.append(1000 * (t - signal.meta.trigger_time), signal.value[i])
        self.addSeries(self.series)  # Note: attach after filling up, not before
        # color up
        pen: QPen = self.series.pen()
        pen.setWidth(1)
        pen.setColor(signal_color(signal))
        self.series.setPen(pen)


class SignalChartView(QtCharts.QChartView):
    def __init__(self, parent=None):
        super(SignalChartView, self).__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setChart(SignalChart())

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
