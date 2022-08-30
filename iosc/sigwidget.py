# 2. 3rd
from PyQt5.QtCore import Qt, QPoint, QMargins
from PyQt5.QtGui import QColor, QBrush, QFont, QPen
from PyQt5.QtWidgets import QLabel, QMenu, QTableWidget
# 3. 4rd
from QCustomPlot2 import QCustomPlot, QCPAxis
# 4. local
import const
import mycomtrade
from sigprop import SigPropertiesDialog
# x. const
X_FONT = QFont(*const.XSCALE_FONT)
D_BRUSH = QBrush(Qt.Dense4Pattern)
ZERO_PEN = QPen(QColor('black'))
NO_PEN = QPen(QColor(255, 255, 255, 0))
TICK_COUNT = 20
PEN_STYLE = {
    mycomtrade.ELineType.Solid: Qt.SolidLine,
    mycomtrade.ELineType.Dot: Qt.DotLine,
    mycomtrade.ELineType.DashDot: Qt.DashDotDotLine
}


class TimeAxisView(QCustomPlot):
    def __init__(self, tmin: float, t0: float, tmax, ti: int, parent=None):
        super().__init__(parent)
        self.xAxis.setRange((tmin - t0) * 1000, (tmax - t0) * 1000)
        # TODO: setTickInterval(ti)
        # TODO: setLabelFormat("%d")
        self.__squeeze()
        # decorate
        self.xAxis.ticker().setTickCount(TICK_COUNT)  # QCPAxisTicker; FIXME:
        self.xAxis.setTickLabelFont(X_FONT)

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
            self.parent().parent().cellWidget(self.__signal.i, 1).upd_style()  # note: 2 x parent

    def __do_sig_hide(self):
        """Hide signal in table"""
        self.parent().parent().hideRow(self.__signal.i)


class AnalogSignalCtrlView(SignalCtrlView):
    def __init__(self, parent: QTableWidget = None):
        super().__init__(parent)


class StatusSignalCtrlView(SignalCtrlView):
    def __init__(self, parent: QTableWidget = None):
        super().__init__(parent)


class SignalChartView(QCustomPlot):
    _signal: mycomtrade.Signal

    def __init__(self, ti: int, parent: QTableWidget = None):
        super().__init__(parent)
        self.addGraph()  # QCPGraph
        # self.yAxis.setRange(0, 1)  # not helps
        self.__squeeze()
        self.__decorate()
        # xaxis.ticker().setTickCount(len(self.time))  # QCPAxisTicker
        self.xAxis.ticker().setTickCount(TICK_COUNT)  # QCPAxisTicker; FIXME: 200ms default

    def __squeeze(self):
        ar = self.axisRect(0)  # QCPAxisRect
        ar.setMinimumMargins(QMargins())  # the best
        ar.removeAxis(self.xAxis2)
        ar.removeAxis(self.yAxis2)
        #self.yAxis.setVisible(False)  # or cp.graph().valueAxis()
        self.yAxis.setTickLabels(False)
        self.yAxis.setTicks(False)
        self.yAxis.setPadding(0)
        self.yAxis.ticker().setTickCount(1)  # the only z-line
        self.xAxis.setTickLabels(False)
        self.xAxis.setTicks(False)
        self.xAxis.setPadding(0)

    def __decorate(self):
        # self.yAxis.grid().setPen(QPen(QColor(255, 255, 255, 0)))
        self.yAxis.setBasePen(NO_PEN)  # hack
        self.yAxis.grid().setZeroLinePen(ZERO_PEN)
        self.xAxis.grid().setZeroLinePen(ZERO_PEN)


    def _set_style(self):
        pen = self.graph().pen()  # QPen
        # pen.setWidth(1)
        pen.setStyle(PEN_STYLE[self._signal.line_type])
        pen.setColor(QColor.fromRgb(*self._signal.rgb))
        self.graph().setPen(pen)

    def _set_data(self, signal: mycomtrade.StatusSignal):
        self._signal = signal
        self.graph().setData([1000 * (t - signal.meta.trigger_time) for t in signal.time], signal.value)
        self.xAxis.setRange(
            1000 * (signal.time[0] - signal.meta.trigger_time),
            1000 * (signal.time[-1] - signal.meta.trigger_time)
        )
        self._set_style()

    def upd_style(self):
        self._set_style()
        self.replot()


class AnalogSignalChartView(SignalChartView):
    def __init__(self, ti: int, parent: QTableWidget = None):
        super().__init__(ti, parent)

    def set_data(self, signal: mycomtrade.StatusSignal):
        super()._set_data(signal)
        self.yAxis.setRange(min(signal.value), max(signal.value))


class StatusSignalChartView(SignalChartView):
    def __init__(self, ti: int, parent: QTableWidget = None):
        super().__init__(ti, parent)
        # decorate
        self.graph().setBrush(D_BRUSH)

    def set_data(self, signal: mycomtrade.StatusSignal):
        super()._set_data(signal)
        self.yAxis.setRange(0, 1.6)  # note: from -0.1 if Y0 wanted
