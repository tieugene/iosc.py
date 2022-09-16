"""Signal widgets (chart, ctrl panel).
TODO: try __slots__"""
import cmath
import datetime
import math
from typing import Optional
# 2. 3rd
from PyQt5.QtCore import Qt, QPoint, QMargins, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont, QPen, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import QLabel, QMenu, QTableWidget, QWidget, QVBoxLayout, QScrollArea, QHBoxLayout, QPushButton, \
    QScrollBar
# 3. 4rd
from QCustomPlot2 import QCustomPlot, QCPAxis, QCPItemTracer, QCPItemStraightLine, QCPItemText, QCPItemRect, \
    QCPScatterStyle, QCPPainter, QCPGraphData
# 4. local
import mycomtrade
import const
import sigfunc
from sigprop import AnalogSignalPropertiesDialog, StatusSignalPropertiesDialog
# x. const
PEN_STYLE = {
    mycomtrade.ELineType.Solid: Qt.SolidLine,
    mycomtrade.ELineType.Dot: Qt.DotLine,
    mycomtrade.ELineType.DashDot: Qt.DashDotDotLine
}


class HScroller(QScrollBar):
    """Bottom scrollbar"""
    def __init__(self, parent: QWidget):
        """
        :param parent:
        :type parent: ComtradeWidget
        """
        super().__init__(Qt.Horizontal, parent)
        parent.signal_xscale.connect(self._slot_chg_width)

    def slot_col_resize(self, w: int):
        """Recalc scroller parm on aim column resized.
        :param w: New chart column width
        :todo: link to signal
        """
        self.setPageStep(w)
        if (chart_width := self.parent().chart_width) is not None:
            range_new = chart_width - self.pageStep()
            self.setRange(0, range_new)
            if self.value() > range_new:
                self.setValue(range_new)

    def _slot_chg_width(self, w_old: int, w_new: int):
        """Recalc scroller parm on aim column resized.
        :param w_old: Old chart width (px)
        :param w_new: New chart width (px)
        """
        # 1. range
        range_new = w_new - self.pageStep()
        self.setRange(0, range_new)
        if w_old == 0:  # initial => value() == 0
            return
        # 2. start ptr
        b_old = self.value()  # old begin
        if const.X_CENTERED:
            p_half = self.pageStep() / 2  # relative page mid
            b_new = int(round((b_old + p_half) * w_new / w_old - p_half))  # FIXME: glitches with right list scroller
        else:  # plan B (w/o glitches)
            b_new = b_old
        # 3. limit start ptr
        if b_new < 0:
            b_new = 0
        elif b_new > range_new:
            b_new = range_new
        self.setValue(b_new)


class CleanScrollArea(QScrollArea):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


class TimeAxisView(QCustomPlot):
    __root: QWidget
    __main_ptr_label: QCPItemText

    def __init__(self, osc: mycomtrade.MyComtrade, root: QWidget, parent: CleanScrollArea):
        super().__init__(parent)
        self.__root = root
        self.__main_ptr_label = QCPItemText(self)
        t0 = osc.raw.trigger_time
        self.xAxis.setRange((osc.raw.time[0] - t0) * 1000, (osc.raw.time[-1] - t0) * 1000)
        self.__squeeze()
        self.__set_style()
        self.__slot_main_ptr_moved()
        self.__root.signal_main_ptr_moved.connect(self.__slot_main_ptr_moved)
        self.__root.signal_xscale.connect(self._slot_chg_width)

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
        self.setFixedHeight(const.XSCALE_HEIGHT)

    def __set_style(self):
        # TODO: setLabelFormat("%d")
        self.xAxis.setTickLabelFont(const.X_FONT)
        self.__main_ptr_label.setColor(const.X_LABEL_COLOR)  # text
        self.__main_ptr_label.setBrush(const.X_LABEL_BRUSH)  # rect
        self.__main_ptr_label.setTextAlignment(Qt.AlignCenter)
        self.__main_ptr_label.setFont(const.X_FONT)
        self.__main_ptr_label.setPadding(QMargins(2, 2, 2, 2))
        self.__main_ptr_label.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)

    def __slot_main_ptr_moved(self):
        """Repaint/move main ptr value label (%.2f)
        :fixme: draw in front of ticks
        """
        x = self.__root.mptr_x
        self.__main_ptr_label.setText("%.2f" % x)
        self.__main_ptr_label.position.setCoords(x, 0)
        self.replot()

    def _slot_chg_width(self, _: int, w_new: int):  # dafault: 1117
        self.setFixedWidth(w_new)
        self.xAxis.ticker().setTickCount(const.TICK_COUNT * self.__root.xzoom)
        self.replot()


class StatusBarView(QCustomPlot):
    """:todo: join TimeAxisView"""
    __root: QWidget
    __zero_timestamp: datetime.datetime
    __zero_ptr_label: QCPItemText
    __main_ptr_label: QCPItemText

    def __init__(self, osc: mycomtrade.MyComtrade, root: QWidget, parent: CleanScrollArea):
        super().__init__(parent)
        self.__root = root
        self.__zero_timestamp = osc.raw.cfg.trigger_timestamp
        self.__zero_ptr_label = QCPItemText(self)
        self.__main_ptr_label = QCPItemText(self)
        t0 = osc.raw.trigger_time
        self.xAxis.setRange((osc.raw.time[0] - t0) * 1000, (osc.raw.time[-1] - t0) * 1000)
        self.__squeeze()
        self.__set_style()
        self.__zero_ptr_label.setText(self.__zero_timestamp.time().isoformat())
        self.__slot_main_ptr_moved()
        self.__root.signal_main_ptr_moved.connect(self.__slot_main_ptr_moved)
        self.__root.signal_xscale.connect(self._slot_chg_width)

    def __squeeze(self):
        ar = self.axisRect(0)
        ar.setMinimumMargins(QMargins())
        ar.removeAxis(self.yAxis)
        ar.removeAxis(self.yAxis2)
        ar.removeAxis(self.xAxis2)
        self.xAxis.setTickLabels(False)
        self.xAxis.setTicks(False)
        self.xAxis.grid().setVisible(False)
        self.xAxis.setPadding(0)
        self.setFixedHeight(const.XSCALE_HEIGHT)

    def __set_style(self):
        # zero
        self.__zero_ptr_label.setColor(const.Z_LABEL_COLOR)  # text
        self.__zero_ptr_label.setTextAlignment(Qt.AlignCenter)
        self.__zero_ptr_label.setFont(const.X_FONT)
        self.__zero_ptr_label.setPadding(QMargins(2, 2, 2, 2))
        self.__zero_ptr_label.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)
        # mptr
        self.__main_ptr_label.setColor(const.X_LABEL_COLOR)  # text
        self.__main_ptr_label.setBrush(const.X_LABEL_BRUSH)  # rect
        self.__main_ptr_label.setTextAlignment(Qt.AlignCenter)
        self.__main_ptr_label.setFont(const.X_FONT)
        self.__main_ptr_label.setPadding(QMargins(2, 2, 2, 2))
        self.__main_ptr_label.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)

    def __slot_main_ptr_moved(self):
        """Repaint/move main ptr value label"""
        x = self.__root.mptr_x  # from z-point, , ms
        self.__main_ptr_label.setText((self.__zero_timestamp + datetime.timedelta(milliseconds=x)).time().isoformat())
        self.__main_ptr_label.position.setCoords(x, 0)
        self.replot()

    def _slot_chg_width(self, _: int, w_new: int):  # dafault: 1117
        self.setFixedWidth(w_new)


class ZoomButton(QPushButton):
    def __init__(self, txt: str, parent: QWidget = None):
        super().__init__(txt, parent)
        self.setContentsMargins(QMargins())  # not helps
        self.setFixedWidth(const.SIG_ZOOM_BTN_WIDTH)
        # self.setFlat(True)
        # TODO: squeeze


class SignalCtrlView(QWidget):
    _root: QWidget
    _signal: mycomtrade.Signal
    _f_name: QLabel
    _f_value: QLabel
    _b_side: QWidget
    _b_zoom_in: ZoomButton
    _b_zoom_0: ZoomButton
    _b_zoom_out: ZoomButton
    sibling: Optional[QCustomPlot]
    signal_restyled = pyqtSignal()

    def __init__(self, signal: mycomtrade.Signal, parent: QTableWidget, root: QWidget):
        super().__init__(parent)
        self._signal = signal
        self._root = root
        self.sibling = None
        self.__mk_widgets()
        self.__mk_layout()
        self._set_style()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__slot_context_menu)
        self._root.signal_main_ptr_moved.connect(self.slot_update_value)
        self.slot_update_value()

    def __mk_widgets(self):
        self._f_value = QLabel()
        self._f_name = QLabel()
        self._f_name.setText(self._signal.sid)
        self._b_side = QWidget(self)
        self._b_zoom_in = ZoomButton("+")
        self._b_zoom_0 = ZoomButton("=")
        self._b_zoom_out = ZoomButton("-")
        # initial state
        self._b_zoom_0.setEnabled(False)
        self._b_zoom_out.setEnabled(False)

    def __mk_layout(self):
        self.setContentsMargins(QMargins())
        # left side
        text_side = QWidget(self)
        text_side.setLayout(QVBoxLayout())
        text_side.layout().addWidget(self._f_value)
        text_side.layout().addWidget(self._f_name)
        text_side.layout().setSpacing(0)
        # text_side.layout().setContentsMargins(QMargins())
        # right side
        self._b_side.setLayout(QVBoxLayout())
        self._b_side.layout().addWidget(self._b_zoom_in)
        self._b_side.layout().addWidget(self._b_zoom_0)
        self._b_side.layout().addWidget(self._b_zoom_out)
        self._b_side.layout().setSpacing(0)
        self._b_side.layout().setContentsMargins(QMargins())
        # altogether
        self.setLayout(QHBoxLayout(self))
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(QMargins())
        self.layout().addWidget(text_side)
        self.layout().addWidget(self._b_side)
        self.layout().setStretch(0, 1)
        self.layout().setStretch(1, 0)

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
        """Hide signal in table
        # FIXME: row != signal no
        # TODO: convert to signal call
        """
        self.parent().parent().hideRow(self._signal.i)

    def _do_sig_property(self):
        """Show/set signal properties"""
        ...  # stub

    def whoami(self) -> int:
        """
        :return: Signal no in correspondent signal list
        """
        return self._signal.i

    @property
    def signal(self) -> mycomtrade.Signal:
        return self._signal


class StatusSignalCtrlView(SignalCtrlView):
    def __init__(self, signal: mycomtrade.StatusSignal, parent: QTableWidget, root):
        super().__init__(signal, parent, root)
        self._b_side.hide()

    def _do_sig_property(self):
        """Show/set signal properties"""
        if StatusSignalPropertiesDialog(self._signal).execute():
            self._set_style()
            self.signal_restyled.emit()

    def slot_update_value(self):
        self._f_value.setText("%d" % self._signal.value[self._root.mptr])


class AnalogSignalCtrlView(SignalCtrlView):
    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QTableWidget, root: QWidget):
        super().__init__(signal, parent, root)
        self._root.signal_recalc_achannels.connect(self.slot_update_value)
        self._root.signal_shift_achannels.connect(self.slot_update_value)
        self._b_zoom_in.clicked.connect(self.slot_vzoom_in)
        self._b_zoom_0.clicked.connect(self.slot_vzoom_0)
        self._b_zoom_out.clicked.connect(self.slot_vzoom_out)

    def _do_sig_property(self):
        """Show/set signal properties"""
        if AnalogSignalPropertiesDialog(self._signal).execute():
            self._set_style()
            self.signal_restyled.emit()

    def slot_update_value(self):
        func = sigfunc.func_list[self._root.viewas]
        v = func(self._signal.value, self._root.mptr, self._root.tpp)
        if isinstance(v, complex):  # hrm1
            y = abs(v)
        else:
            y = v
        pors_y = y * self._signal.get_mult(self._root.show_sec)
        uu = self._signal.uu_orig
        if abs(pors_y) < 1:
            pors_y *= 1000
            uu = 'm' + uu
        elif abs(pors_y) > 1000:
            pors_y /= 1000
            uu = 'k' + uu
        if isinstance(v, complex):  # hrm1
            self._f_value.setText("%.3f %s / %.3f°" % (pors_y, uu, math.degrees(cmath.phase(v))))
        else:
            self._f_value.setText("%.3f %s" % (pors_y, uu))

    def slot_vzoom_in(self):
        if self.sibling.zoom == 1:
            self._b_zoom_0.setEnabled(True)
            self._b_zoom_out.setEnabled(True)
        self.sibling.zoom += 1

    def slot_vzoom_0(self):
        if self.sibling.zoom > 1:
            self.sibling.zoom = 1
            self._b_zoom_0.setEnabled(False)
            self._b_zoom_out.setEnabled(False)

    def slot_vzoom_out(self):
        if self.sibling.zoom > 1:
            self.sibling.zoom -= 1
            if self.sibling.zoom == 1:
                self._b_zoom_0.setEnabled(False)
                self._b_zoom_out.setEnabled(False)


class SignalScrollArea(QScrollArea):
    __vzoom_factor: QLabel

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.horizontalScrollBar().hide()
        self.__vzoom_factor = QLabel(self)
        self.__vzoom_factor.setVisible(False)
        self.__vzoom_factor.setStyleSheet("QLabel { background-color : red; color : rgba(255,255,255,255) }")

    def resizeEvent(self, event: QResizeEvent):
        event.accept()
        if event.size().height() != event.oldSize().height():
            self.widget().slot_vresize()

    def slot_set_zoom_factor(self, z: int):
        """Set label according to zoom"""
        if z > 1:
            if not self.__vzoom_factor.isVisible():
                self.__vzoom_factor.setVisible(True)
            self.__vzoom_factor.setText(f"x{z}")
            self.__vzoom_factor.adjustSize()
        else:
            self.__vzoom_factor.clear()
            self.__vzoom_factor.setVisible(False)


class MainPtr(QCPItemTracer):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setGraph(cp.graph())
        self.setPen(const.MAIN_PTR_PEN)
        self.position.setAxes(cp.xAxis, None)
        # cp.setCursor(QCursor(Qt.CrossCursor))


class OldPtr(QCPItemStraightLine):
    __x: float

    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setPen(const.OLD_PTR_PEN)
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
        self.topLeft.setCoords(x, yaxis.pixelToCoord(0) - yaxis.pixelToCoord(const.PTR_RECT_HEIGHT))

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

    def __init__(self, signal: mycomtrade.Signal, parent: QScrollArea, root: QWidget,
                 sibling: SignalCtrlView):
        super().__init__(parent)
        self._root = root
        self._sibling = sibling
        self._sibling.sibling = self
        self._signal = signal
        self._ptr_onway = False
        self._old_ptr = OldPtr(self)
        self._main_ptr_tip = MainPtrTip(self)
        self._main_ptr_rect = MainPtrRect(self)
        self.addGraph()
        self._main_ptr = MainPtr(self)  # after graph()
        self._set_data()
        self.__squeeze()
        self.__decorate()
        self._set_style()
        self.__switch_tips(False)
        # ymin = min(self._signal.value)
        # ymax = max(self._signal.value)
        # ypad = (ymax - ymin) * Y_PAD  # == self._signal.value.ptp()
        # self.yAxis.setRange(ymin - ypad, ymax + ypad)  # #76, not helps
        # self.setFixedWidth(1000)
        self.mousePress.connect(self.__slot_mouse_press)
        self.mouseMove.connect(self.__slot_mouse_move)
        self.mouseRelease.connect(self.__slot_mouse_release)
        self._sibling.signal_restyled.connect(self.__slot_signal_restyled)
        self._root.signal_main_ptr_moved.connect(self.__slot_main_ptr_moved)
        self._root.signal_xscale.connect(self._slot_chg_width)

    def _set_data(self):
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
        self.yAxis.setBasePen(const.NO_PEN)  # hack
        self.yAxis.grid().setZeroLinePen(const.ZERO_PEN)
        self.xAxis.grid().setZeroLinePen(const.ZERO_PEN)

    def _set_style(self):
        ...  # stub

    def __handle_mouse(self, x_px: int, click: bool):
        """
        Handle mouse pressed[+moved]
        :param x_px: mouse x-position (px)
        :todo: RTFM QCPAbstractItem.setSelectable(), QCP.setInteraction(), QCP.itemClick
        """
        x_src = self.xAxis.pixelToCoord(x_px)  # real x-position realtive to graph z-point in graaph units
        x_dst_0: float = self._main_ptr.position.key()  # dont save pos (== &); self.graphKey()
        self._main_ptr.setGraphKey(x_src)
        self._main_ptr.updatePosition()  # mandatory
        pos = self._main_ptr.position  # coerced x-postion (QCustomPlot2.QCPItemPosition)
        x_dst = pos.key()
        mptr_jumped = x_dst_0 != x_dst  # Don't do that!
        if click:  # mouse pressed => set old ptr coords, rect start coord
            self._old_ptr.move2x(x_dst)
            self._main_ptr_rect.set2x(x_dst)
            self._ptr_onway = True
        elif mptr_jumped:  # mouse moved & pressed & mptr jumped
            if not self._old_ptr.visible():  # show tips on demand
                self.__switch_tips(True)
            # refresh tips
            self._main_ptr_tip.move2x(x_dst, self._old_ptr.x)
            self._main_ptr_rect.stretc2x(x_dst)
        if mptr_jumped:
            self.replot()
            self._root.slot_main_ptr_moved_x(x_dst)

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

    def __slot_main_ptr_moved(self):
        if not self._ptr_onway:  # check is not myself
            self._main_ptr.setGraphKey(self._root.mptr_x)
            self.replot()

    def __slot_signal_restyled(self):
        self._set_style()
        self.replot()

    def _slot_chg_width(self, _: int, w_new: int):
        """Changing signal chart real width (px)"""
        self.setFixedWidth(w_new)
        self.xAxis.ticker().setTickCount(const.TICK_COUNT * self._root.xzoom)  # QCPAxisTicker; FIXME: 200ms default
        # self.replot()


class StatusSignalChartView(SignalChartView):
    def __init__(self, signal: mycomtrade.StatusSignal, parent: QTableWidget, root: QWidget,
                 sibling: SignalCtrlView):
        super().__init__(signal, parent, root, sibling)
        self.yAxis.setRange(const.SIG_D_YMIN, const.SIG_D_YMAX)

    def _set_style(self):
        brush = QBrush(const.D_BRUSH)
        brush.setColor(QColor.fromRgb(*self._signal.rgb))
        self.graph().setBrush(brush)

    def slot_vresize(self):
        h_vscroller = self.parent().height()
        if self.height() != (new_height := h_vscroller):
            self.setFixedHeight(new_height)


class NumScatterStyle(QCPScatterStyle):
    def __init__(self):
        super().__init__(QCPScatterStyle.ssPlus)
        print("My scatter")

    def drawShape(self, painter: QCPPainter, *__args):
        print("Bingo")


class ScatterLabel(QCPItemText):
    def __init__(self, num: int, point: QCPGraphData, parent: SignalChartView):
        super().__init__(parent)
        self.setPositionAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.setFont(QFont('mono', 8))
        self.setText(str(num))
        self.position.setCoords(point.key, point.value)


class AnalogSignalChartView(SignalChartView):
    __vzoom: int
    __pps: int  # px/sample
    # __myscatter: NumScatterStyle

    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QScrollArea, root, sibling: AnalogSignalCtrlView):
        super().__init__(signal, parent, root, sibling)
        self.__vzoom = 1
        self.__pps = 0
        self.__rerange()
        self._root.signal_shift_achannels.connect(self.__slot_shift)
        # self.__myscatter = NumScatterStyle()

    def _set_style(self):
        pen = QPen(PEN_STYLE[self._signal.line_type])
        pen.setColor(QColor.fromRgb(*self._signal.rgb))
        self.graph().setPen(pen)

    def __rerange(self):
        ymin = min(min(self._signal.value), 0)
        ymax = max(max(self._signal.value), 0)
        ypad = (ymax - ymin) * const.SIG_A_YPAD
        self.yAxis.setRange(ymin - ypad, ymax + ypad)

    def __slot_shift(self):
        self._set_data()
        self.__rerange()
        self.replot()

    @property
    def zoom(self):
        return self.__vzoom

    @zoom.setter
    def zoom(self, z: int):
        if z != self.__vzoom:
            self.__vzoom = z
            self.slot_vresize()
            self.parent().parent().slot_set_zoom_factor(z)  # WTF? x2 parents

    def slot_vresize(self):
        h_vscroller = self.parent().height()
        if self.height() != (new_height := h_vscroller * self.__vzoom):
            self.setFixedHeight(new_height)

    def _slot_chg_width(self, w_old: int, w_new: int):
        super()._slot_chg_width(w_old, w_new)
        pps = int(w_new / len(self._signal.value))
        if self.__pps != pps:
            if pps < const.X_SCATTER_MARK:
                shape = QCPScatterStyle(QCPScatterStyle.ssNone)
            else:
                shape = QCPScatterStyle(QCPScatterStyle.ssPlus)
            self.graph().setScatterStyle(QCPScatterStyle(shape))
            # <dirtyhack>
            if self.__pps < const.X_SCATTER_NUM <= pps:
                # self.graph().setScatterStyle(self.__myscatter)
                for i, d in enumerate(self.graph().data()):
                    ScatterLabel(i, d, self)
            elif self.__pps >= const.X_SCATTER_NUM > pps:
                for i in reversed(range(self.itemCount())):
                    if isinstance(self.item(i), ScatterLabel):
                        self.removeItem(i)
            # </dirtyhack>
            self.__pps = pps
            self.replot()
