# 2. 3rd
from PyQt5.QtCore import Qt, QPoint, QMargins, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont, QPen, QMouseEvent
from PyQt5.QtWidgets import QLabel, QMenu, QTableWidget, QWidget, QVBoxLayout
# 3. 4rd
from QCustomPlot2 import QCustomPlot, QCPAxis, QCPItemTracer, QCPItemStraightLine, QCPItemText, QCPItemRect
# 4. local
import const
import mycomtrade
from sigprop import AnalogSignalPropertiesDialog, StatusSignalPropertiesDialog

# x. const
X_FONT = QFont(*const.XSCALE_FONT)
D_BRUSH = QBrush(Qt.Dense4Pattern)
ZERO_PEN = QPen(Qt.black)
NO_PEN = QPen(QColor(255, 255, 255, 0))
MAIN_PTR_PEN = QPen(QBrush(QColor('orange')), 2)
OLD_PTR_PEN = QPen(QBrush(Qt.green), 1, Qt.DotLine)
PTR_RECT_HEIGHT = 20
TICK_COUNT = 20
Y_PAD = 0.1  # upper and lower Y-padding; 0.1 == 10%
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
    _root: QWidget
    _signal: mycomtrade.Signal
    _f_name: QLabel
    _f_value: QLabel
    signal_restyled = pyqtSignal()

    def __init__(self, signal: mycomtrade.Signal, parent: QTableWidget, root: QWidget):
        super().__init__(parent)
        self._signal = signal
        self._root = root
        self.__setup_ui()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__slot_context_menu)

    def __setup_ui(self):
        self._f_value = QLabel(self)
        self._f_name = QLabel(self)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._f_name)
        self.layout().addWidget(self._f_value)
        self._set_style()
        self._f_name.setText(self._signal.sid)

    def _set_style(self):
        self.setStyleSheet("QLabel { color : rgb(%d,%d,%d); }" % self._signal.rgb)

    def __slot_context_menu(self, point: QPoint):
        context_menu = QMenu()
        action_sig_property = context_menu.addAction("Channel property")
        action_sig_hide = context_menu.addAction("Hide channel")
        chosen_action = context_menu.exec_(self.mapToGlobal(point))
        if chosen_action == action_sig_hide:
            self.__do_sig_hide()
        elif chosen_action == action_sig_property:
            self._do_sig_property()

    def __do_sig_hide(self):
        """Hide signal in table"""
        self.parent().parent().hideRow(self._signal.i)

    def _do_sig_property(self):
        """Show/set signal properties"""
        ...  # stub


class AnalogSignalCtrlView(SignalCtrlView):
    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QTableWidget, root: QWidget):
        super().__init__(signal, parent, root)

    def _do_sig_property(self):
        """Show/set signal properties"""
        if AnalogSignalPropertiesDialog(self._signal).execute():
            self._set_style()
            self.signal_restyled.emit()

    def slot_update_value(self, y: float):
        """
        :param y: Value to show (orig * a + b)
        """
        real_y = y * self._signal.get_mult(self._root.show_sec)
        uu = self._signal.uu_orig
        if abs(real_y) < 1:
            real_y *= 1000
            uu = 'm' + uu
        elif abs(real_y) > 1000:
            real_y /= 1000
            uu = 'k' + uu
        self._f_value.setText("%.3f %s" % (real_y, uu))


class StatusSignalCtrlView(SignalCtrlView):
    def __init__(self, signal: mycomtrade.StatusSignal, parent: QTableWidget, root):
        super().__init__(signal, parent, root)

    def _do_sig_property(self):
        """Show/set signal properties"""
        if StatusSignalPropertiesDialog(self._signal).execute():
            self._set_style()
            self.signal_restyled.emit()

    def slot_update_value(self, y: float):
        self._f_value.setText("%d" % y)


class MainPtr(QCPItemTracer):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setGraph(cp.graph())
        self.setPen(MAIN_PTR_PEN)
        self.position.setAxes(cp.xAxis, None)
        # cp.setCursor(QCursor(Qt.CrossCursor))


class OldPtr(QCPItemStraightLine):
    __x: float

    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setPen(OLD_PTR_PEN)
        self.setVisible(False)

    def move2x(self, x: float):
        """
        :param x:
        :note: for  QCPItemLine: s/point1/start/, s/point2/end/
        """
        self.__x = x
        self.point1.setCoords(x, 0)
        self.point2.setCoords(x, 1)

    @property
    def x(self):
        return self.__x


class MainPtrTip(QCPItemText):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setColor(Qt.black)  # text
        self.setPen(Qt.red)
        self.setBrush(QBrush(QColor(255, 170, 0)))  # rect
        self.setTextAlignment(Qt.AlignCenter)
        self.setFont(QFont('mono', 8))
        self.setPadding(QMargins(2, 2, 2, 2))

    def move2x(self, x: float, x_old: float):
        dx = x - x_old
        self.setPositionAlignment((Qt.AlignLeft if dx > 0 else Qt.AlignRight) | Qt.AlignBottom)
        self.position.setCoords(x, 0)
        self.setText("%.2f" % dx)


class MainPtrRect(QCPItemRect):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setPen(QColor(255, 170, 0, 128))
        self.setBrush(QColor(255, 170, 0, 128))

    def set2x(self, x: float):
        """Set starting point"""
        yaxis = self.parentPlot().yAxis
        self.topLeft.setCoords(x, yaxis.pixelToCoord(0) - yaxis.pixelToCoord(PTR_RECT_HEIGHT))

    def stretc2x(self, x: float):
        self.bottomRight.setCoords(x, 0)


class SignalChartView(QCustomPlot):
    _root: QWidget
    _sibling: SignalCtrlView
    _signal: mycomtrade.Signal
    _main_ptr: MainPtr
    _old_ptr: OldPtr
    _main_ptr_tip: MainPtrTip
    _main_ptr_rect: MainPtrRect
    _ptr_onway: bool

    def __init__(self, signal: mycomtrade.Signal, ti: int, parent: QTableWidget, root: QWidget,
                 sibling: SignalCtrlView):
        super().__init__(parent)
        self._root = root
        self._sibling = sibling
        self._signal = signal
        self._ptr_onway = False
        self._old_ptr = OldPtr(self)
        self._main_ptr_tip = MainPtrTip(self)
        self._main_ptr_rect = MainPtrRect(self)
        self.addGraph()
        self._main_ptr = MainPtr(self)  # after graph()
        self.__set_data()
        self.__squeeze()
        self.__decorate()
        self._set_style()
        self.__switch_tips(False)
        # ymin = min(self._signal.value)
        # ymax = max(self._signal.value)
        # ypad = (ymax - ymin) * Y_PAD  # == self._signal.value.ptp()
        # self.yAxis.setRange(ymin - ypad, ymax + ypad)  # #76, not helps
        self.xAxis.ticker().setTickCount(TICK_COUNT)  # QCPAxisTicker; FIXME: 200ms default
        self.mousePress.connect(self.__slot_mouse_press)
        self.mouseMove.connect(self.__slot_mouse_move)
        self.mouseRelease.connect(self.__slot_mouse_release)
        self._sibling.signal_restyled.connect(self.__slot_signal_restyled)
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

    def _set_style(self):
        ...  # stub

    def __handle_mouse(self, x_px: int, click: bool):
        """
        Handle mouse pressed[+moved]
        :param x_px: mouse x-position (px)
        :todo: chk pos changed (hint: save `pos` B4)
        """
        x_src = self.xAxis.pixelToCoord(x_px)  # real x-position realtive to graph z-point in graaph units
        x_dst_0: float = self._main_ptr.position.key()  # dont save pos (== &)
        self._main_ptr.setGraphKey(x_src)
        self._main_ptr.updatePosition()  # mandatory
        pos = self._main_ptr.position  # coerced x-postion
        x_dst = pos.key()
        if x_dst_0 != x_dst:  # check MPtr moved
            if click:  # mouse pressed => set old ptr coords, rect start coord
                self._old_ptr.move2x(x_dst)
                self._main_ptr_rect.set2x(x_dst)
                self._ptr_onway = True
            else:  # mouse moved (when pressed)
                if not self._old_ptr.visible():  # show tips on demand
                    self.__switch_tips(True)
                # refresh tips
                self._main_ptr_tip.move2x(x_dst, self._old_ptr.x)
                self._main_ptr_rect.stretc2x(x_dst)
            self.replot()
            self._root.slot_main_ptr_moved_x(x_dst)
            self._sibling.slot_update_value(pos.value())

    def __switch_tips(self, todo: bool):
        # print(("Off", "On")[int(todo)])
        self._old_ptr.setVisible(todo)
        self._main_ptr_tip.setVisible(todo)
        self._main_ptr_rect.setVisible(todo)

    def __slot_mouse_press(self, event: QMouseEvent):
        """
        - check MPtr moved
        - move MPtr
        - set old ptr coords, rect start coord
        - call slots
        :param event:
        """
        if event.button() == Qt.LeftButton:
            # self.__switch_tips(True)
            # self._old_ptr.move2x(self._main_ptr.position.key())
            self.__handle_mouse(event.x(), True)

    def __slot_mouse_move(self, event: QMouseEvent):
        """
        - check MPtr moved
        - move MPtr
        - show old_ptr, tip, rect (if required)
        - refresh tip, rect
        - call slots
        :param event:
        """
        if self._ptr_onway:  # or `event.buttons() & Qt.LeftButton`
            self.__handle_mouse(event.x(), False)

    def __slot_mouse_release(self, event: QMouseEvent):
        """Hide all, reset tmp vars"""
        if event.button() == Qt.LeftButton:
            self._ptr_onway = False
            self.__switch_tips(False)
            self.replot()

    def __slot_main_ptr_moved_x(self, x: float):
        if not self._ptr_onway:  # check is not myself
            self._main_ptr.setGraphKey(x)
            # self._main_ptr.updatePosition()  # not helps
            self.replot()
            self._sibling.slot_update_value(self._main_ptr.position.value())

    def __slot_signal_restyled(self):
        self._set_style()
        self.replot()


class AnalogSignalChartView(SignalChartView):
    def __init__(self, signal: mycomtrade.AnalogSignal, ti: int, parent: QTableWidget, root,
                 sibling: AnalogSignalCtrlView):
        super().__init__(signal, ti, parent, root, sibling)
        self.yAxis.setRange(min(signal.value), max(signal.value))

    def _set_style(self):
        pen = QPen(PEN_STYLE[self._signal.line_type])
        pen.setColor(QColor.fromRgb(*self._signal.rgb))
        self.graph().setPen(pen)


class StatusSignalChartView(SignalChartView):
    def __init__(self, signal: mycomtrade.StatusSignal, ti: int, parent: QTableWidget, root: QWidget,
                 sibling: SignalCtrlView):
        super().__init__(signal, ti, parent, root, sibling)
        self.yAxis.setRange(-0.1, 1.6)  # note: from -0.1 if Y0 wanted

    def _set_style(self):
        brush = QBrush(D_BRUSH)
        brush.setColor(QColor.fromRgb(*self._signal.rgb))
        self.graph().setBrush(brush)
