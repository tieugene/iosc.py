from dataclasses import dataclass
from typing import Optional, Union

from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtGui import QResizeEvent, QMouseEvent, QBrush, QColor, QFont, QPen
from PyQt5.QtWidgets import QScrollArea, QLabel, QWidget, QTableWidget
from QCustomPlot2 import QCustomPlot, QCPScatterStyle, QCPPainter, QCPItemText, QCPGraphData, QCPGraph

import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.ctrl import StatusSignalLabel, AnalogSignalLabel
from iosc.sig.widget.ptr import MainPtr, SCPtr, TmpPtr, MsrPtr, LvlPtr

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


class SignalChartWidget(QCustomPlot):  # FIXME: rename to SignalPlot
    @dataclass
    class State:
        signal: mycomtrade.Signal

    _root: QWidget
    _sibling: Union[StatusSignalLabel, AnalogSignalLabel]
    _signal: Union[mycomtrade.AnalogSignal, mycomtrade.StatusSignal]
    _main_ptr: MainPtr
    _sc_ptr: SCPtr
    _tmp_ptr: dict[int, TmpPtr]
    _ptr_selected: bool

    def __init__(self, signal: Union[mycomtrade.AnalogSignal, mycomtrade.StatusSignal], parent: QScrollArea,
                 root: QWidget, sibling: Union[StatusSignalLabel, AnalogSignalLabel]):
        super().__init__(parent)
        self._root = root
        self._sibling = sibling
        self._sibling.sibling = self
        self._signal = signal
        self.addGraph()
        self._main_ptr = MainPtr(self.graph(), self._root)  # after graph()
        self._sc_ptr = SCPtr(self.graph(), self._root)
        self._tmp_ptr = dict()
        self._ptr_selected = False
        self.__squeeze()
        self.__decorate()
        self._set_data()
        self._set_style()
        self._root.signal_xscale.connect(self._slot_chg_width)
        self._root.signal_ptr_add_tmp.connect(self._slot_ptr_add_tmp)
        self._root.signal_ptr_del_tmp.connect(self._slot_ptr_del_tmp)

    def _set_data(self):
        z_time = self._signal.raw.trigger_time
        x_data = [1000 * (t - z_time) for t in self._signal.time]
        if self._signal.is_bool:
            y_data = self._signal.value
        else:  # normalize analog signals to -1..1
            divider = max(abs(min(self._signal.value)), abs(max(self._signal.value)))
            y_data = [v / divider for v in self._signal.value]
        self.graph().setData(x_data, y_data, True)
        self.xAxis.setRange(
            1000 * (self._signal.time[0] - z_time),
            1000 * (self._signal.time[-1] - z_time)
        )
        if self._signal.is_bool:
            self.yAxis.setRange(iosc.const.SIG_D_YMIN, iosc.const.SIG_D_YMAX)
        else:
            y_range = self.graph().data().valueRange()[0]
            self.yAxis.setRange(
                min(round(y_range.lower), 0) - iosc.const.SIG_A_YPAD,
                max(round(y_range.upper), 0) + iosc.const.SIG_A_YPAD
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
        self.yAxis.setBasePen(iosc.const.PEN_NONE)  # hack
        self.yAxis.grid().setZeroLinePen(iosc.const.PEN_ZERO)
        self.xAxis.grid().setZeroLinePen(iosc.const.PEN_ZERO)

    def _set_style(self):
        ...  # stub

    @property
    def ptr_selected(self) -> bool:
        return self._ptr_selected

    @ptr_selected.setter
    def ptr_selected(self, selected: bool):
        self._ptr_selected = selected

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)  # always .isAcepted() after this
        if event.button() == Qt.LeftButton and not self._ptr_selected:  # check selectable
            i_new = self._root.x2i(self.xAxis.pixelToCoord(event.x()))
            self._root.slot_ptr_moved_main(i_new)  # __move MainPtr here
            super().mousePressEvent(event)  # and select it

    def slot_signal_restyled(self):
        self._set_style()
        self.replot()

    def _slot_chg_width(self, _: int, w_new: int):
        """Changing signal chart real width (px)"""
        self.setFixedWidth(w_new)
        self.xAxis.ticker().setTickCount(iosc.const.TICK_COUNT * self._root.xzoom)  # QCPAxisTicker; TODO: 200ms default
        # self.replot()

    def _slot_ptr_add_tmp(self, ptr_id: int):
        """Add new TmpPtr"""
        self._tmp_ptr[ptr_id] = TmpPtr(self.graph(), self._root, ptr_id)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr"""
        self.removeItem(self._tmp_ptr[uid])
        del self._tmp_ptr[uid]
        self.replot()

    @property
    def state(self) -> State:
        return self.State(
            signal=self._signal
        )

    def restore(self, state: State):
        """Restore signal state:
        - [x] x-width[, x-zoom] (global)
        - [x] x-position (global)
        - [x] MainPtr (global, auto)
        - [x] SCPtr (global, auto)
        - [x] TmpPtr[]
        """
        self._slot_chg_width(0, self._root.chart_width)  # x-width[+x-zoom]
        self.parent().parent().horizontalScrollBar().setValue(self._root.hsb.value())  # x-pos; WARNING: 2 x parent()
        for uid in self._root.tmp_ptr_i.keys():  # TmpPtr[]
            self._slot_ptr_add_tmp(uid)
        self.replot()


class StatusSignalChartWidget(SignalChartWidget):  # FIXME: (QCPGraph)
    def __init__(self, signal: mycomtrade.StatusSignal, parent: QTableWidget, root: QWidget,
                 sibling: StatusSignalLabel):
        super().__init__(signal, parent, root, sibling)

    def _set_style(self):
        brush = QBrush(iosc.const.BRUSH_D)
        brush.setColor(QColor.fromRgb(*self._signal.rgb))
        self.graph().setBrush(brush)

    def slot_vresize(self):
        h_vscroller = self.parent().height()
        if self.height() != (new_height := h_vscroller):
            self.setFixedHeight(new_height)


class ScatterLabel(QCPItemText):
    def __init__(self, num: int, point: QCPGraphData, parent: SignalChartWidget):
        super().__init__(parent)
        self.setPositionAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.setFont(QFont('mono', 8))
        self.setText(str(num))
        self.position.setCoords(point.key, point.value)


class AnalogSignalChartWidget(SignalChartWidget):  # FIXME: (QCPGraph)
    @dataclass
    class State(SignalChartWidget.State):
        v_zoom: int
        v_pos: int
        msr_ptr: list[MsrPtr.State]  # uid, x_idx
        lvl_ptr: list[LvlPtr.State]  # uid, y

    _signal: mycomtrade.AnalogSignal
    __vzoom: int
    __pps: int  # px/sample

    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QScrollArea, root, sibling: AnalogSignalLabel):
        super().__init__(signal, parent, root, sibling)
        self.__vzoom = 1
        self.__pps = 0
        self._root.signal_chged_shift.connect(self.__slot_shift)

    def _set_style(self):
        pen = QPen(PEN_STYLE[self._signal.line_type])
        pen.setColor(QColor.fromRgb(*self._signal.rgb))
        self.graph().setPen(pen)

    def __slot_shift(self):
        self._set_data()
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

    def slot_signal_restyled(self):
        self._set_style()
        for i in range(self.itemCount()):
            item = self.item(i)
            if isinstance(item, MsrPtr):
                item.slot_set_color()
            elif isinstance(item, LvlPtr):
                item.slot_set_color()
        self.replot()

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

    def add_ptr_msr(self, uid: int, i: int):
        MsrPtr(self.graph(), self._root, self._signal, uid, i)  # FIXME: signal graph

    def slot_ptr_del_msr(self, ptr: MsrPtr):
        """Del MsrPtr"""
        self.removeItem(ptr)
        self.replot()

    def add_ptr_lvl(self, uid: int, y: Optional[float] = None):
        if y is None:
            y = max(self._signal.value)
        LvlPtr(self.graph(), self._root, self._signal, uid, y)

    def slot_ptr_del_lvl(self, ptr: LvlPtr):
        """Del LvlPtr"""
        self.removeItem(ptr)
        self.replot()

    @property
    def state(self) -> State:
        msr_ptr = []
        lvl_ptr = []
        for i in range(self.itemCount()):
            item = self.item(i)
            if isinstance(item, MsrPtr):
                msr_ptr.append(item.state)
            elif isinstance(item, LvlPtr):
                lvl_ptr.append(item.state)
        return self.State(
            signal=self._signal,
            v_zoom=self.__vzoom,
            v_pos=self.parent().parent().verticalScrollBar().value(),
            msr_ptr=msr_ptr,
            lvl_ptr=lvl_ptr
        )

    def restore(self, state: State):
        """Restore signal state:
        - [x] v-zoom(self)
        - [x] v-position
        - [x] MsrPtr[]
        - [x] LvlPtr[]
        """
        super().restore(state)
        for s in state.msr_ptr:
            self.add_ptr_msr(s.uid, s.i)
        for s in state.lvl_ptr:
            self.add_ptr_lvl(s.uid, s.y)
        if state.v_zoom > 1:
            self.zoom = state.v_zoom
            self.parent().parent().verticalScrollBar().setValue(state.v_pos)
            # self._sibling.vzoom_sync() FIXME:


class SignalGraph(QCPGraph):
    ...


class StatusSignalGraph(SignalGraph):
    ...


class AnalogSignalGraph(SignalGraph):
    ...
