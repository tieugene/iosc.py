# 2. 3rd
from PyQt5.QtCore import Qt, QPoint, QMargins
from PyQt5.QtGui import QColor, QBrush, QFont, QPen, QMouseEvent
from PyQt5.QtWidgets import QLabel, QMenu, QTableWidget, QWidget, QVBoxLayout
# 3. 4rd
from QCustomPlot2 import QCustomPlot, QCPAxis, QCPItemTracer, QCPItemStraightLine, QCPItemText, QCPItemRect
# 4. local
import const
import mycomtrade
from sigprop import SigPropertiesDialog
# x. const
X_FONT = QFont(*const.XSCALE_FONT)
D_BRUSH = QBrush(Qt.Dense4Pattern)
ZERO_PEN = QPen(Qt.black)
NO_PEN = QPen(QColor(255, 255, 255, 0))
MAIN_PTR_PEN = QPen(QBrush(QColor('orange')), 2)
OLD_PTR_PEN = QPen(QBrush(Qt.green), 1, Qt.DotLine)
TICK_COUNT = 20
PEN_STYLE = {
    mycomtrade.ELineType.Solid: Qt.SolidLine,
    mycomtrade.ELineType.Dot: Qt.DotLine,
    mycomtrade.ELineType.DashDot: Qt.DashDotDotLine
}


class TimeAxisView(QCustomPlot):
    __root: QWidget
    __main_ptr_label: QCPItemText

    def __init__(self, tmin: float, t0: float, tmax, ti: int, parent, root: QWidget):
        super().__init__(parent)
        self.__root = root
        self.__main_ptr_label = QCPItemText(self)
        self.xAxis.setRange((tmin - t0) * 1000, (tmax - t0) * 1000)
        self.xAxis.ticker().setTickCount(TICK_COUNT)  # QCPAxisTicker; FIXME: (ti)
        self.__squeeze()
        self.__set_style()
        self.__root.signal_main_ptr_moved_x.connect(self.__slot_main_ptr_moved_x)  # FIXME: on top of ticks

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

    def __set_style(self):
        # TODO: setLabelFormat("%d")
        self.xAxis.setTickLabelFont(X_FONT)
        self.__main_ptr_label.setColor(Qt.white)  # text
        self.__main_ptr_label.setBrush(QBrush(Qt.red))  # rect
        self.__main_ptr_label.setTextAlignment(Qt.AlignCenter)
        self.__main_ptr_label.setFont(QFont('mono', 8))
        self.__main_ptr_label.setPadding(QMargins(2, 2, 2, 2))
        self.__main_ptr_label.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)

    def __slot_main_ptr_moved_x(self, x: float):
        """Repaint/move main ptr value label (%.2f)"""
        self.__main_ptr_label.setText("%.2f" % x)
        self.__main_ptr_label.position.setCoords(x, 0)
        self.replot()


class SignalCtrlView(QLabel):
    __signal: mycomtrade.Signal
    _f_name: QLabel
    _f_value: QLabel

    def __init__(self, signal: mycomtrade.Signal, parent: QTableWidget, root: QWidget):
        super().__init__(parent)
        self.__signal = signal
        self.__setup_ui()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__slot_context_menu)

    def __setup_ui(self):
        self._f_value = QLabel(self)
        self._f_name = QLabel(self)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._f_name)
        self.layout().addWidget(self._f_value)
        self.__set_style()
        self._f_name.setText(self.__signal.sid)

    def __set_style(self):
        self.setStyleSheet("QLabel { color : rgb(%d,%d,%d); }" % self.__signal.rgb)

    def __slot_context_menu(self, point: QPoint):
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
            self.__set_style()
            self.parent().parent().cellWidget(self.__signal.i, 1).slot_upd_style()  # note: 2 x parent

    def __do_sig_hide(self):
        """Hide signal in table"""
        self.parent().parent().hideRow(self.__signal.i)


class AnalogSignalCtrlView(SignalCtrlView):
    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QTableWidget, root: QWidget):
        super().__init__(signal, parent, root)

    def slot_update_value(self, y: float):
        # TODO: u/m//k, dynamic unit
        self._f_value.setText("%.3f" % y)


class StatusSignalCtrlView(SignalCtrlView):
    def __init__(self, signal: mycomtrade.StatusSignal, parent: QTableWidget, root):
        super().__init__(signal, parent, root)

    def slot_update_value(self, y: float):
        self._f_value.setText("%d" % y)


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
    _sibling: SignalCtrlView
    _signal: mycomtrade.Signal
    _main_ptr: MainPtr
    _main_ptr_tip: QCPItemText
    _main_ptr_rect: QCPItemRect
    _old_ptr: OldPtr
    _ptr_onway: bool

    def __init__(self, signal: mycomtrade.Signal, ti: int, parent: QTableWidget, root: QWidget,
                 sibling: SignalCtrlView):
        super().__init__(parent)
        self._root = root
        self._sibling = sibling
        self._signal = signal
        self._main_ptr_tip = QCPItemText(self)
        self._main_ptr_rect = QCPItemRect(self)
        self._old_ptr = OldPtr(self)
        self._ptr_onway = False
        self.addGraph()
        self._main_ptr = MainPtr(self)  # after graph()
        # self.yAxis.setRange(0, 1)  # not helps
        self.__set_data()
        self.__squeeze()
        self.__decorate()
        self.__set_style()
        self.__switch_onway(False)
        self.xAxis.ticker().setTickCount(TICK_COUNT)  # QCPAxisTicker; FIXME: 200ms default
        self.mousePress.connect(self.__slot_mouse_press)
        self.mouseRelease.connect(self.__slot_mouse_release)
        self.mouseMove.connect(self.__slot_mouse_move)
        self._root.signal_main_ptr_moved_x.connect(self.__slot_main_ptr_moved_x)

    def __set_data(self):
        z_time = self._signal.raw.trigger_time
        self.graph().setData([1000 * (t - z_time) for t in self._signal.time], self._signal.value, True)
        self.xAxis.setRange(
            1000 * (self._signal.time[0] - z_time),
            1000 * (self._signal.time[-1] - z_time)
        )

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
        # bk on orange in red rect, oblique
        self._main_ptr_tip.setColor(Qt.black)  # text
        self._main_ptr_tip.setPen(Qt.red)
        self._main_ptr_tip.setBrush(QBrush(QColor('orange')))  # rect
        self._main_ptr_tip.setTextAlignment(Qt.AlignCenter)
        self._main_ptr_tip.setFont(QFont('mono', 8))
        self._main_ptr_tip.setPadding(QMargins(2, 2, 2, 2))
        self._main_ptr_tip.setPositionAlignment(Qt.AlignLeft | Qt.AlignBottom)

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
        :todo: chk pos changed
        """
        x_src = self.xAxis.pixelToCoord(x_px)  # real x-position realtive to graph z-point
        self._main_ptr.setGraphKey(x_src)
        pos = self._main_ptr.position  # coerced x-postion
        x_dst = pos.key()
        self._old_ptr.move2x(x_src)
        # refresh tips
        self._main_ptr_tip.setText("%.2f" % x_dst)
        self._main_ptr_tip.position.setCoords(x_dst, 0)
        # go
        self.replot()
        self._root.slot_main_ptr_moved_x(x_dst)
        self._sibling.slot_update_value(pos.value())

    def __switch_onway(self, todo: bool):
        # print(("Off", "On")[int(todo)])
        self._ptr_onway = todo
        self._old_ptr.setVisible(todo)
        self._main_ptr_tip.setVisible(todo)
        self._main_ptr_rect.setVisible(todo)

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
            self._sibling.slot_update_value(self._main_ptr.position.value())

    def slot_upd_style(self):
        self.__set_style()
        self.replot()


class AnalogSignalChartView(SignalChartView):
    def __init__(self, signal: mycomtrade.AnalogSignal, ti: int, parent: QTableWidget, root,
                 sibling: AnalogSignalCtrlView):
        super().__init__(signal, ti, parent, root, sibling)
        self.yAxis.setRange(min(signal.value), max(signal.value))


class StatusSignalChartView(SignalChartView):
    def __init__(self, signal: mycomtrade.StatusSignal, ti: int, parent: QTableWidget, root: QWidget,
                 sibling: SignalCtrlView):
        super().__init__(signal, ti, parent, root, sibling)
        self.yAxis.setRange(0, 1.6)  # note: from -0.1 if Y0 wanted
        self.graph().setBrush(D_BRUSH)
