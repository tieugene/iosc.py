# 2. 3rd
from PySide2.QtCore import Qt, QPointF, QPoint
from PySide2.QtGui import QPainter, QPen, QColor
from PySide2.QtCharts import QtCharts
from PySide2.QtWidgets import QLabel, QMenu, QTableWidget
# 3. local
import mycomtrade
from sigprop import SigPropertiesDialog
# x. const
Z0_COLOR = 'black'
CHART_MIN_HEIGHT = 50
MARGINS_ZERO = (0, 0, 0, 0)
# normal
MARGINS_AXIS = MARGINS_ZERO
MARGINS_CHART = MARGINS_ZERO
TIMELINE_HEIGHT = 100
# abnormal
# MARGINS_AXIS = (-30, -50, -35, -10)
# MARGINS_CHART = (-35, -15, -35, -40)  # fill all: (-40, -20, -40, -45)
# TIMELINE_HEIGHT = 40


class TimeAxisView(QtCharts.QChartView):
    xaxis: QtCharts.QValueAxis

    def __init__(self, tmin: float, t0: float, tmax, ti: int, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)

        series = QtCharts.QLineSeries()
        series.append((tmin - t0) * 1000, 0)
        series.append((tmax - t0) * 1000, 0)

        chart = QtCharts.QChart()
        chart.legend().hide()
        chart.layout().setContentsMargins(*MARGINS_ZERO)
        chart.setContentsMargins(*MARGINS_AXIS)
        chart.addSeries(series)

        self.xaxis = QtCharts.QValueAxis()
        self.xaxis.setTickType(QtCharts.QValueAxis.TicksDynamic)
        self.xaxis.setTickAnchor(0)  # dyn
        self.xaxis.setTickInterval(ti)  # dyn
        self.xaxis.setLabelFormat("%d")
        # xaxis.setLabelsVisible(True)
        self.xaxis.setGridLineVisible(False)

        chart.setAxisX(self.xaxis, series)

        self.setChart(chart)


class SignalChart(QtCharts.QChart):
    series: QtCharts.QLineSeries
    xaxis: QtCharts.QValueAxis
    __signal: mycomtrade.Signal

    def __init__(self, ti: int, parent=None):
        """
        :param ti: Ticks interval, ms
        """
        super().__init__(parent)
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
        # expand
        self.layout().setContentsMargins(*MARGINS_ZERO)
        self.setContentsMargins(*MARGINS_CHART)
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored, QSizePolicy.DefaultType)  # no effect

    def set_data(self, signal: mycomtrade.Signal):
        self.__signal = signal
        # Filling QLineSeries
        for i, t in enumerate(signal.time):
            self.series.append(1000 * (t - signal.meta.trigger_time), signal.value[i])
        self.addSeries(self.series)  # Note: attach after filling up, not B4
        # self.series.attachAxis(self.xaxis)  # Note: attach after adding series to self, not B4
        self.setAxisX(self.xaxis, self.series)
        # color up
        self.set_style()

    def set_style(self):
        pen: QPen = self.series.pen()
        pen.setWidth(1)
        pen.setStyle((Qt.SolidLine, Qt.DotLine, Qt.DashDotDotLine)[self.__signal.line_type.value])
        pen.setColor(QColor.fromRgb(*self.__signal.rgb))
        self.series.setPen(pen)


class SignalChartView(QtCharts.QChartView):
    def __init__(self, ti: int, parent=None):
        """
        :param ti: Ticks interval, ms
        """
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setChart(SignalChart(ti))

    def drawForeground(self, painter, _):
        """
        :param painter:
        :param _: == rect
        :todo: not plots for status const Y=1
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
    __signal: mycomtrade.Signal

    def __init__(self, parent: QTableWidget = None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._handle_context_menu)

    def set_data(self, signal: mycomtrade.Signal):
        self.__signal = signal
        self.setText(signal.sid)

    def set_style(self):
        self.setStyleSheet("QLabel { color : rgb(%d,%d,%d); }" % self.__signal.rgb)

    def _handle_context_menu(self, point: QPoint):
        context_menu = QMenu()
        sig_property = context_menu.addAction("Signal property")
        chosen_action = context_menu.exec_(self.mapToGlobal(point))
        if chosen_action == sig_property:
            self.__set_sig_property()

    def __set_sig_property(self):
        """Show/set signal properties"""
        if SigPropertiesDialog(self.__signal).execute():
            self.set_style()
            self.parent().parent().cellWidget(self.__signal.i, 1).chart().set_style()  # Warning: 2 x parent
