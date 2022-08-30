# 2. 3rd
from PyQt5.QtCore import Qt, QPointF, QPoint, QMargins
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PyQt5.QtWidgets import QLabel, QMenu, QTableWidget
from PyQt5 import QtChart
# 3. 4rd
from QCustomPlot2 import QCustomPlot, QCPAxisRect, QCPAxis
# 4. local
import mycomtrade, const
from sigprop import SigPropertiesDialog

# x. const
Z0_COLOR = 'black'
PLOTAREA_COLOR = (240, 240, 240)
CHART_MIN_HEIGHT = 50
MARGINS_ZERO = (0, 0, 0, 0)
NOFONT = QFont('', 1)
# normal
MARGINS_AXIS = MARGINS_ZERO
MARGINS_CHART = MARGINS_ZERO


class TimeAxisView(QCustomPlot):
    xaxis: QtChart.QValueAxis

    def __init__(self, tmin: float, t0: float, tmax, ti: int, parent=None):
        super().__init__(parent)
        self.xAxis.setRange((tmin - t0) * 1000, (tmax - t0) * 1000)
        # TODO: setTickInterval(ti)
        # TODO: setLabelFormat("%d")
        self.__squeeze()
        # decorate
        self.xAxis.ticker().setTickCount(10)  # QCPAxisTicker
        self.xAxis.setTickLabelFont(QFont(*const.XSCALE_FONT))

    def __squeeze(self):
        ar = self.axisRect(0)
        ar.setMinimumMargins(QMargins())  # the best
        ar.removeAxis(self.yAxis)
        ar.removeAxis(self.yAxis2)
        ar.removeAxis(self.xAxis2)
        # -xaxis.setTickLabels(False)
        # -xaxis.setTicks(False)
        self.xAxis.setTickLabelSide(QCPAxis.lsInside)
        self.xAxis.grid().setVisible(False)
        self.xAxis.setPadding(0)


class SignalCtrlView(QLabel):
    __signal: mycomtrade.Signal

    def __init__(self, parent: QTableWidget = None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._handle_context_menu)

    def set_data(self, signal: mycomtrade.Signal):
        self.__signal = signal
        self.setText(signal.sid)
        self.set_style()

    def set_style(self):
        self.setStyleSheet("QLabel { color : rgb(%d,%d,%d); }" % self.__signal.rgb)

    def _handle_context_menu(self, point: QPoint):
        context_menu = QMenu()
        action_sig_property = context_menu.addAction("Channel property")
        action_sig_hide = context_menu.addAction("Hide channel")
        chosen_action = context_menu.exec_(self.mapToGlobal(point))
        if chosen_action == action_sig_property:
            self.__do_sig_property()
        elif chosen_action == action_sig_hide:
            self.__do_sig_hide()

    def __do_sig_property(self):
        """Show/set signal properties"""
        if SigPropertiesDialog(self.__signal).execute():
            self.set_style()
            self.parent().parent().cellWidget(self.__signal.i, 1).chart().set_style()  # Warning: 2 x parent

    def __do_sig_hide(self):
        """Hide signal in table"""
        self.parent().parent().hideRow(self.__signal.i)


class AnalogSignalCtrlView(SignalCtrlView):
    def __init__(self, parent: QTableWidget = None):
        super().__init__(parent)


class StatusSignalCtrlView(SignalCtrlView):
    def __init__(self, parent: QTableWidget = None):
        super().__init__(parent)


class SignalChart(QtChart.QChart):
    series: QtChart.QLineSeries
    xaxis: QtChart.QValueAxis
    _signal: mycomtrade.Signal

    def __init__(self, ti: int, parent=None):
        """
        :param ti: Ticks interval, ms
        """
        super().__init__(parent)
        self.legend().hide()
        # self.legend().setVisible(False)
        # self.setMinimumHeight(CHART_MIN_HEIGHT)  # FIXME: dirty hack
        # decorate X-axis
        self.xaxis = QtChart.QValueAxis()
        self.xaxis.setTickType(QtChart.QValueAxis.TicksDynamic)
        self.xaxis.setTickAnchor(0)  # dyn
        self.xaxis.setTickInterval(ti)  # dyn
        self.xaxis.setGridLineVisible(True)
        self.xaxis.setLabelsFont(NOFONT)
        self.xaxis.setLabelsVisible(False)
        self.xaxis.setLineVisible(False)  # hide axis line and ticks
        self.xaxis.setTitleFont(NOFONT)
        self.xaxis.setTitleVisible(False)
        # expand
        self.layout().setContentsMargins(*MARGINS_ZERO)
        self.setContentsMargins(*MARGINS_CHART)
        self.setMargins(QMargins())
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored, QSizePolicy.DefaultType)  # no effect
        # hichlight plot area
        self.setPlotAreaBackgroundVisible(True)
        self.setPlotAreaBackgroundBrush(QBrush(QColor.fromRgb(*PLOTAREA_COLOR)))


class SignalChartView(QtChart.QChartView):
    def __init__(self, ti: int, parent=None):
        """
        :param ti: Ticks interval, ms
        """
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)

    def set_data(self, signal: mycomtrade.Signal):
        self.chart().set_data(signal)


class AnalogSignalChart(SignalChart):
    def __init__(self, ti: int, parent: QTableWidget = None):
        super().__init__(ti, parent)

    def set_data(self, signal: mycomtrade.AnalogSignal):
        self._signal = signal
        self.series = QtChart.QLineSeries()
        for i, t in enumerate(signal.time):
            self.series.append(1000 * (t - signal.meta.trigger_time), signal.value[i])
        self.addSeries(self.series)  # Note: attach after filling up, not B4
        # self.series.attachAxis(self.xaxis)  # Note: attach after adding series to self, not B4
        self.setAxisX(self.xaxis, self.series)
        self.set_style()

    def set_style(self):
        pen: QPen = self.series.pen()
        pen.setWidth(1)
        pen.setStyle((Qt.SolidLine, Qt.DotLine, Qt.DashDotDotLine)[self._signal.line_type.value])
        pen.setColor(QColor.fromRgb(*self._signal.rgb))
        self.series.setPen(pen)


class AnalogSignalChartView(SignalChartView):
    def __init__(self, ti: int, parent: QTableWidget = None):
        super().__init__(ti, parent)
        self.setChart(AnalogSignalChart(ti))


class StatusSignalChartView(QCustomPlot):
    def __init__(self, ti: int, parent: QTableWidget = None):
        super().__init__(parent)
        self.addGraph()  # QCPGraph
        # self.yAxis.setRange(0, 1)  # not helps
        self.__squeeze()
        # xaxis.ticker().setTickCount(len(self.time))  # QCPAxisTicker
        self.xAxis.ticker().setTickCount(20)  # QCPAxisTicker; FIXME: 200ms default
        # decorate
        self.graph().setBrush(QBrush(Qt.Dense4Pattern))

    def __squeeze(self):
        ar = self.axisRect(0)  # QCPAxisRect
        ar.removeAxis(self.xAxis2)
        ar.removeAxis(self.yAxis2)
        ar.setMinimumMargins(QMargins())  # the best
        self.yAxis.setVisible(False)  # or cp.graph().valueAxis()
        self.xAxis.setTickLabels(False)
        self.xAxis.setTicks(False)
        self.xAxis.setPadding(0)

    def set_data(self, signal: mycomtrade.StatusSignal):
        self._signal = signal
        self.graph().setData([1000 * (t - signal.meta.trigger_time) for t in signal.time], signal.value)
        self.xAxis.setRange(1000 * (signal.time[0] - signal.meta.trigger_time), 1000 * (signal.time[-1] - signal.meta.trigger_time))
