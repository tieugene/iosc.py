from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtGui import QResizeEvent, QMouseEvent, QBrush, QColor, QFont, QPen
from PyQt5.QtWidgets import QScrollArea, QLabel, QWidget, QTableWidget
from QCustomPlot2 import QCustomPlot, QCPScatterStyle, QCPPainter, QCPItemText, QCPGraphData, QCP

import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.ctrl import SignalCtrlWidget, AnalogSignalCtrlWidget
from iosc.sig.widget.ptr import MainPtr, OldPtr, MainPtrTip, MainPtrRect, SCPtr

PEN_STYLE = {
    mycomtrade.ELineType.Solid: Qt.SolidLine,
    mycomtrade.ELineType.Dot: Qt.DotLine,
    mycomtrade.ELineType.DashDot: Qt.DashDotDotLine
}


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


class SignalChartWidget(QCustomPlot):
    _root: QWidget
    _sibling: SignalCtrlWidget
    _signal: mycomtrade.Signal
    _main_ptr: MainPtr
    _old_ptr: OldPtr
    _main_ptr_tip: MainPtrTip
    _main_ptr_rect: MainPtrRect
    _main_ptr_onway: bool
    _sc_ptr: SCPtr
    _sc_ptr_onway: bool

    def __init__(self, signal: mycomtrade.Signal, parent: QScrollArea, root: QWidget,
                 sibling: SignalCtrlWidget):
        super().__init__(parent)
        self._root = root
        self._sibling = sibling
        self._sibling.sibling = self
        self._signal = signal
        self._main_ptr_onway = False
        self._sc_ptr_onway = False
        self._old_ptr = OldPtr(self)
        self._main_ptr_tip = MainPtrTip(self)
        self._main_ptr_rect = MainPtrRect(self)
        self.addGraph()
        self._main_ptr = MainPtr(self, self._root)  # after graph()
        self._sc_ptr = SCPtr(self, self._root)
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
        # self.setInteractions(QCP.Interactions(QCP.iSelectItems))  # select on click=mousePressed+mouseReleased
        # tmp disabled
        # self.mousePress.connect(self.__slot_mouse_press)
        # self.mouseMove.connect(self.__slot_mouse_move)
        # self.mouseRelease.connect(self.__slot_mouse_release)
        self._sibling.signal_restyled.connect(self.__slot_signal_restyled)
        self._root.signal_xscale.connect(self._slot_chg_width)
        self._root.signal_main_ptr_moved.connect(self.__slot_main_ptr_moved)

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
        self.yAxis.setBasePen(iosc.const.NO_PEN)  # hack
        self.yAxis.grid().setZeroLinePen(iosc.const.ZERO_PEN)
        self.xAxis.grid().setZeroLinePen(iosc.const.ZERO_PEN)

    def _set_style(self):
        ...  # stub

    def __handle_mouse(self, x_px: int, click: bool):
        """
        Handle mouse pressed[+moved]
        :param x_px: mouse x-position (px)
        """
        x_src = self.xAxis.pixelToCoord(x_px)  # real x-position (ms) realtive to graph z-point in graph units
        x_dst_0: float = self._main_ptr.position.key()  # don't save pos (== &); self.graphKey()
        self._main_ptr.setGraphKey(x_src)
        self._main_ptr.updatePosition()  # mandatory
        pos = self._main_ptr.position  # coerced x-postion (QCustomPlot2.QCPItemPosition)
        x_dst = pos.key()
        mptr_jumped = x_dst_0 != x_dst  # Don't do that!
        if click:  # mouse pressed => set old ptr coords, rect start coord
            self._old_ptr.move2x(x_dst)
            self._main_ptr_rect.set2x(x_dst)
            self._main_ptr_onway = True
        elif mptr_jumped:  # mouse moved & pressed & main_ptr_i jumped
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
        if self._main_ptr_onway:  # or `event.buttons() & Qt.LeftButton`
            self.__handle_mouse(event.x(), False)

    def __slot_mouse_release(self, event: QMouseEvent):
        """Hide all, reset tmp vars"""
        if event.button() == Qt.LeftButton:
            self._main_ptr_onway = False
            self.__switch_tips(False)
            self.replot()

    def __slot_main_ptr_moved(self):
        if not self._main_ptr_onway:  # check is not myself
            self._main_ptr.setGraphKey(self._root.main_ptr_x)
            self.replot()

    def __slot_signal_restyled(self):
        self._set_style()
        self.replot()

    def _slot_chg_width(self, _: int, w_new: int):
        """Changing signal chart real width (px)"""
        self.setFixedWidth(w_new)
        self.xAxis.ticker().setTickCount(iosc.const.TICK_COUNT * self._root.xzoom)  # QCPAxisTicker; TODO: 200ms default
        # self.replot()


class StatusSignalChartWidget(SignalChartWidget):
    def __init__(self, signal: mycomtrade.StatusSignal, parent: QTableWidget, root: QWidget,
                 sibling: SignalCtrlWidget):
        super().__init__(signal, parent, root, sibling)
        self.yAxis.setRange(iosc.const.SIG_D_YMIN, iosc.const.SIG_D_YMAX)

    def _set_style(self):
        brush = QBrush(iosc.const.D_BRUSH)
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
    def __init__(self, num: int, point: QCPGraphData, parent: SignalChartWidget):
        super().__init__(parent)
        self.setPositionAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.setFont(QFont('mono', 8))
        self.setText(str(num))
        self.position.setCoords(point.key, point.value)


class AnalogSignalChartWidget(SignalChartWidget):
    __vzoom: int
    __pps: int  # px/sample
    # __myscatter: NumScatterStyle

    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QScrollArea, root, sibling: AnalogSignalCtrlWidget):
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
        ypad = (ymax - ymin) * iosc.const.SIG_A_YPAD
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
            if pps < iosc.const.X_SCATTER_MARK:
                shape = QCPScatterStyle(QCPScatterStyle.ssNone)
            else:
                shape = QCPScatterStyle(QCPScatterStyle.ssPlus)
            self.graph().setScatterStyle(QCPScatterStyle(shape))
            # <dirtyhack>
            if self.__pps < iosc.const.X_SCATTER_NUM <= pps:
                # self.graph().setScatterStyle(self.__myscatter)
                for i, d in enumerate(self.graph().data()):
                    ScatterLabel(i, d, self)
            elif self.__pps >= iosc.const.X_SCATTER_NUM > pps:
                for i in reversed(range(self.itemCount())):
                    if isinstance(self.item(i), ScatterLabel):
                        self.removeItem(i)
            # </dirtyhack>
            self.__pps = pps
            self.replot()
