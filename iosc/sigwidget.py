# 2. 3rd
from PyQt5.QtCore import Qt, QPoint, QMargins
from PyQt5.QtGui import QColor, QBrush, QFont, QPen, QMouseEvent
from PyQt5.QtWidgets import QLabel, QMenu, QTableWidget, QWidget
# 3. 4rd
from QCustomPlot2 import QCustomPlot, QCPAxis, QCPItemTracer, QCPItemStraightLine, QCPItemPosition
# 4. local
import const
import mycomtrade
from sigprop import SigPropertiesDialog
# x. const
X_FONT = QFont(*const.XSCALE_FONT)
D_BRUSH = QBrush(Qt.Dense4Pattern)
ZERO_PEN = QPen(QColor('black'))
NO_PEN = QPen(QColor(255, 255, 255, 0))
MAIN_PTR_PEN = QPen(QBrush(QColor('orange')), 2)
OLD_PTR_PEN = QPen(QBrush(QColor('green')), 1, Qt.DotLine)
TICK_COUNT = 20
PEN_STYLE = {
    mycomtrade.ELineType.Solid: Qt.SolidLine,
    mycomtrade.ELineType.Dot: Qt.DotLine,
    mycomtrade.ELineType.DashDot: Qt.DashDotDotLine
}


class TimeAxisView(QCustomPlot):
    def __init__(self, tmin: float, t0: float, tmax, ti: int, parent, root):
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

    def __init__(self, signal: mycomtrade.Signal, parent: QTableWidget, root):
        super().__init__(parent)
        self.__signal = signal
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._handle_context_menu)
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
            self.parent().parent().cellWidget(self.__signal.i, 1).slot_upd_style()  # note: 2 x parent

    def __do_sig_hide(self):
        """Hide signal in table"""
        self.parent().parent().hideRow(self.__signal.i)


class AnalogSignalCtrlView(SignalCtrlView):
    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QTableWidget, root):
        super().__init__(signal, parent, root)


class StatusSignalCtrlView(SignalCtrlView):
    def __init__(self, signal: mycomtrade.StatusSignal, parent: QTableWidget, root):
        super().__init__(signal, parent, root)


class MainPtr(QCPItemTracer):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setGraph(cp.graph())
        self.setPen(MAIN_PTR_PEN)
        self.position.setAxes(cp.xAxis, None)


class OldPtr(QCPItemStraightLine):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setPen(OLD_PTR_PEN)
        self.setVisible(False)

    def move2x(self, x: float):
        """
        :param x:
        :note: for  QCPItemLine: s/point1/start/, s/point2/end/
        """
        self.point1.setCoords(x, 0)
        self.point2.setCoords(x, 1)


class SignalChartView(QCustomPlot):
    _root: QWidget
    _signal: mycomtrade.Signal
    _main_ptr: MainPtr
    _old_ptr: OldPtr
    _ptr_onway: bool

    def __init__(self, signal: mycomtrade.Signal, ti: int, parent: QTableWidget, root):
        super().__init__(parent)
        self._root = root
        # print(root.metaObject().className())
        self._signal = signal
        self._ptr_onway = False
        self.addGraph()  # QCPGraph
        # self.yAxis.setRange(0, 1)  # not helps
        self.__squeeze()
        self.__decorate()
        # xaxis.ticker().setTickCount(len(self.time))  # QCPAxisTicker
        self.__set_data()
        self.__set_style()
        self._main_ptr = MainPtr(self)
        self.xAxis.ticker().setTickCount(TICK_COUNT)  # QCPAxisTicker; FIXME: 200ms default
        self._old_ptr = OldPtr(self)
        self.mousePress.connect(self.__slot_mouse_press)
        self.mouseRelease.connect(self.__slot_mouse_release)
        self.mouseMove.connect(self.__slot_mouse_move)
        self._root.signal_main_ptr_moved_x.connect(self.__slot_main_ptr_moved_x)

    def __squeeze(self):
        ar = self.axisRect(0)  # QCPAxisRect
        ar.setMinimumMargins(QMargins())  # the best
        ar.removeAxis(self.xAxis2)
        ar.removeAxis(self.yAxis2)
        # self.yAxis.setVisible(False)  # or cp.graph().valueAxis()
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

    def __set_data(self):
        z_time = self._signal.raw.trigger_time
        self.graph().setData([1000 * (t - z_time) for t in self._signal.time], self._signal.value, True)
        self.xAxis.setRange(
            1000 * (self._signal.time[0] - z_time),
            1000 * (self._signal.time[-1] - z_time)
        )

    def __set_style(self):
        pen = self.graph().pen()  # QPen
        # pen.setWidth(1)
        pen.setStyle(PEN_STYLE[self._signal.line_type])
        pen.setColor(QColor.fromRgb(*self._signal.rgb))
        self.graph().setPen(pen)

    def __handle_mouse(self, x_px: int):
        """
        Handle mouse pressed[+moved]
        :param x_px: mouse x-position (px)
        """
        x_src = self.xAxis.pixelToCoord(x_px)  # real x-position realtive to graph z-point
        self._main_ptr.setGraphKey(x_src)
        pos = self._main_ptr.position  # coerced x-postion
        self._old_ptr.move2x(x_src)
        # self.label.setText(f"x: {pos.key()}, y: {pos.value()}")
        self.replot()
        # parent: QTableWidget
        self._root.slot_main_ptr_moved_x(pos.key())
        # self.sibling.main_ptr_moved_y(self.position.value())

    def __switch_onway(self, todo: bool):
        # print(("Off", "On")[int(todo)])
        self._ptr_onway = todo
        self._old_ptr.setVisible(todo)

    def __slot_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # TODO: move _old_ptr?
            self.__switch_onway(True)
            self.__handle_mouse(event.x())

    def __slot_mouse_release(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.__switch_onway(False)
            self.replot()

    def __slot_mouse_move(self, event: QMouseEvent):
        if self._ptr_onway:  # or `event.buttons() & Qt.LeftButton`
            self.__handle_mouse(event.x())

    def __slot_main_ptr_moved_x(self, x: float):
        if not self._ptr_onway:  # check is not myself
            self._main_ptr.setGraphKey(x)
            # self._main_ptr.updatePosition()  # not helps
            self.replot()
            # self.sibling.main_ptr_moved_y(self.position.value())

    def slot_upd_style(self):  # TODO: convert to slot
        self.__set_style()
        self.replot()


class AnalogSignalChartView(SignalChartView):
    def __init__(self, signal: mycomtrade.AnalogSignal, ti: int, parent: QTableWidget, root):
        super().__init__(signal, ti, parent, root)
        self.yAxis.setRange(min(signal.value), max(signal.value))


class StatusSignalChartView(SignalChartView):
    def __init__(self, signal: mycomtrade.StatusSignal, ti: int, parent: QTableWidget, root):
        super().__init__(signal, ti, parent, root)
        self.yAxis.setRange(0, 1.6)  # note: from -0.1 if Y0 wanted
        self.graph().setBrush(D_BRUSH)
