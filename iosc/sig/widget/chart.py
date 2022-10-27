# 1. std
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional
# 2. 3rd
from PyQt5.QtCore import Qt, QMargins, QObject
from PyQt5.QtGui import QResizeEvent, QMouseEvent, QBrush, QColor, QFont, QPen
from PyQt5.QtWidgets import QScrollArea, QLabel, QWidget
from QCustomPlot2 import QCustomPlot, QCPScatterStyle, QCPItemText, QCPGraphData, QCPGraph, QCPRange, QCPPainter
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.ctrl import StatusSignalLabel, AnalogSignalLabel, SignalLabel, SignalCtrlWidget
from iosc.sig.widget.ptr import MainPtr, SCPtr, TmpPtr, MsrPtr, LvlPtr
# x. const
PEN_STYLE = {
    mycomtrade.ELineType.Solid: Qt.SolidLine,
    mycomtrade.ELineType.Dot: Qt.DotLine,
    mycomtrade.ELineType.DashDot: Qt.DashDotDotLine
}


class EScatter(IntEnum):
    N = 0  # none
    P = 1  # plus sign
    D = 2  # digit


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
        if self.widget() and event.size().height() != event.oldSize().height():
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
    class State:  # TODO: include signals
        v_zoom: int
        v_pos: int

    _osc: mycomtrade.Comtrade
    _sibling: SignalCtrlWidget
    _root: QWidget
    _sigraph: set  # [Union[StatusSignalGraph, AnalogSignalGraph]]
    _main_ptr: MainPtr
    _sc_ptr: SCPtr
    _tmp_ptr: dict[int, TmpPtr]
    _ptr_selected: bool
    __vzoom: int
    __scat_style: EScatter  # px/sample

    def __init__(self, osc: mycomtrade.Comtrade, sibling: SignalCtrlWidget, root: QWidget, parent: QScrollArea):
        super().__init__(parent)
        self._osc = osc
        self._sibling = sibling
        self._sibling.sibling = self
        self._root = root
        self._ptr_selected = False
        self.__vzoom = 1
        self.__scat_style = EScatter.N
        self._sigraph = set()
        self.__squeeze()
        self.__decorate()
        self.__set_data()
        self._main_ptr = MainPtr(self.graph(0), self._root)  # after graph()
        self._sc_ptr = SCPtr(self.graph(0), self._root)
        self._tmp_ptr = dict()
        for uid in self._root.tmp_ptr_i.keys():  # TmpPtr[]
            self._slot_ptr_add_tmp(uid)
        self._root.signal_chged_shift.connect(self.__slot_shift)
        self._root.signal_xscale.connect(self._slot_chg_width)
        self._root.signal_ptr_add_tmp.connect(self._slot_ptr_add_tmp)
        self._root.signal_ptr_del_tmp.connect(self._slot_ptr_del_tmp)

    @property
    def sigraph(self):
        return self._sigraph

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

    def __set_data(self):
        """Set data for xPtr"""
        self.addGraph()  # main graph
        z_time = self._osc.trigger_time
        x_data = [1000 * (t - z_time) for t in self._osc.time]
        y_data = [0.0] * len(x_data)
        self.graph(0).setData(x_data, y_data, True)
        self.xAxis.setRange(
            1000 * (self._osc.time[0] - z_time),
            1000 * (self._osc.time[-1] - z_time)
        )

    def __re_range_y(self):
        """Update Y-range on demand"""
        mi = ma = 0.0
        for sg in self._sigraph:
            r = sg.range_y
            mi = min(round(r.lower, 2), mi)
            ma = max(round(r.upper, 2), ma)
        self.yAxis.setRange(mi - iosc.const.SIG_A_YPAD, ma + iosc.const.SIG_A_YPAD)

    def add_signal(self, signal: mycomtrade.Signal, sibling: SignalLabel):  # -> SignalGraph
        gr = self.addGraph()
        if signal.is_bool:
            sigraph = StatusSignalGraph(gr, signal, sibling, self._root, self)
        else:
            sigraph = AnalogSignalGraph(gr, signal, sibling, self._root, self)
            sigraph.refresh_scatter(self.__scat_style)
        self._sigraph.add(sigraph)
        self.__re_range_y()
        return sigraph

    def del_sigraph(self, sigraph: QObject):
        ...  # TODO: rm graph
        sigraph.clean()
        self.removeGraph(sigraph.graph)
        self._sigraph.remove(sigraph)
        self.__re_range_y()
        self.replot()

    @property
    def sig_count(self) -> int:
        return len(self._sigraph)

    def __slot_shift(self):
        for sg in self._sigraph:
            sg.refresh_data()
        self.__re_range_y()
        self.replot()

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

    def _slot_chg_width(self, _: int, w_new: int):
        """Changing signal chart real width (px)"""
        self.setFixedWidth(w_new)
        self.xAxis.ticker().setTickCount(iosc.const.TICK_COUNT * self._root.xzoom)  # QCPAxisTicker; TODO: 200ms default
        pps = int(w_new / len(self._osc.time))
        if pps < iosc.const.X_SCATTER_MARK:
            scat_style = EScatter.N
        elif pps < iosc.const.X_SCATTER_NUM:
            scat_style = EScatter.P
        else:
            scat_style = EScatter.D
        if self.__scat_style != scat_style:
            self.__scat_style = scat_style
            do_refresh = False
            for sg in self._sigraph:
                if not sg.signal.is_bool:
                    do_refresh |= sg.refresh_scatter(scat_style)
            if do_refresh:
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
        if self.height() != (new_height := h_vscroller * self.__vzoom):  # FIXME: ~~* vzoom~~ if bin only
            self.setFixedHeight(new_height)

    def _slot_ptr_add_tmp(self, ptr_id: int):
        """Add new TmpPtr"""
        self._tmp_ptr[ptr_id] = TmpPtr(self.graph(0), self._root, ptr_id)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr"""
        self.removeItem(self._tmp_ptr[uid])
        del self._tmp_ptr[uid]
        self.replot()

    @property
    def state(self) -> State:
        return self.State(
            v_zoom=self.__vzoom,
            v_pos=self.parent().parent().verticalScrollBar().value(),
        )

    def restore(self, state: State):
        """Restore signal state:
        - [x] MainPtr (global, auto)
        - [x] SCPtr (global, auto)
        - [x] TmpPtr[] (global, auto)
        - [x] x-width[, x-zoom] (global)
        - [x] x-position (global)
        - [?] v-zoom(self)
        - [?] v-position
        :todo: signals included
        """
        self._slot_chg_width(0, self._root.chart_width)  # x-width[+x-zoom]
        self.parent().parent().horizontalScrollBar().setValue(self._root.hsb.value())  # x-pos; WARNING: 2 x parent()
        self.__vzoom = state.v_zoom
        self.parent().parent().verticalScrollBar().setValue(state.v_pos)
        self.replot()


class SignalGraph(QObject):
    """QCPGraph wrapper to represent one signal"""
    @dataclass
    class State:
        signal: mycomtrade.Signal

    _graph: QCPGraph
    _signal: mycomtrade.Signal
    _sibling: SignalLabel
    _root: QWidget

    def __init__(self, graph: QCPGraph, signal: mycomtrade.Signal, sibling: SignalLabel, root: QWidget,
                 parent: SignalChartWidget):
        super().__init__(parent)
        self._graph = graph
        self._signal = signal
        self._sibling = sibling
        sibling.sibling = self
        self._root = root
        self._root.sig_no2widget[int(self._signal.is_bool)][self._signal.i] = self
        self._set_data()
        self._set_style()

    @property
    def graph(self) -> QCPGraph:
        return self._graph

    @property
    def signal(self) -> mycomtrade.Signal:
        return self._signal

    def _set_data(self):
        z_time = self._signal.raw.trigger_time
        x_data = [1000 * (t - z_time) for t in self._signal.time]
        self._graph.setData(x_data, self._data_y, True)

    @property
    def _data_y(self) -> list:
        return []  # stub

    def refresh_data(self):
        ...

    def _set_style(self):
        ...  # stub

    def slot_signal_restyled(self):
        self._set_style()
        self._graph.parentPlot().replot()

    def clean(self):
        """Clean up before deleting"""
        self._root.sig_no2widget[int(self._signal.is_bool)][self._signal.i] = None

    @property
    def state(self) -> State:
        return self.State(
            signal=self._signal
        )

    def restore(self, _: State):
        ...  # stub


class StatusSignalGraph(SignalGraph):
    _signal: mycomtrade.StatusSignal
    _sibling: StatusSignalLabel

    def __init__(self, graph: QCPGraph, signal: mycomtrade.Signal, sibling: SignalLabel, root: QWidget,
                 parent: SignalChartWidget):
        super().__init__(graph, signal, sibling, root, parent)

    @property
    def _data_y(self) -> list:
        return self._signal.value

    @property
    def range_y(self) -> QCPRange:
        return QCPRange(0.0, 1.0)

    def _set_style(self):
        brush = QBrush(iosc.const.BRUSH_D)
        brush.setColor(QColor.fromRgb(*self._signal.rgb))
        self._graph.setBrush(brush)


class AnalogSignalGraph(SignalGraph):
    @dataclass
    class State(SignalGraph.State):
        msr_ptr: list[MsrPtr.State]  # uid, x_idx
        lvl_ptr: list[LvlPtr.State]  # uid, y

    class ScatterLabel(QCPItemText):
        def __init__(self, num: int, point: QCPGraphData, parent: QCustomPlot):
            super().__init__(parent)
            self.setPositionAlignment(Qt.AlignBottom | Qt.AlignHCenter)
            self.setFont(QFont('mono', 8))
            self.setText(str(num))
            self.position.setCoords(point.key, point.value)

    class DigitScatterStyle(QCPScatterStyle):
        def __init__(self):
            super().__init__(QCPScatterStyle.ssCircle)
        # def drawShape(self, painter: QCPPainter, *__args):  # not works
        #     print(len(__args))
        #     super().drawShape(painter, *__args)

    _signal: mycomtrade.AnalogSignal
    _sibling: AnalogSignalLabel
    __scat_style: EScatter
    __msr_ptr: set
    __lvl_ptr: set

    def __init__(self, graph: QCPGraph, signal: mycomtrade.Signal, sibling: SignalLabel, root: QWidget,
                 parent: SignalChartWidget):
        self.__scat_style = EScatter.N
        self.__msr_ptr = set()
        self.__lvl_ptr = set()
        super().__init__(graph, signal, sibling, root, parent)

    @property
    def _data_y(self) -> list:
        divider = max(abs(min(self._signal.value)), abs(max(self._signal.value)))
        if divider == 0.0:
            divider = 1.0
        return [v / divider for v in self._signal.value]

    @property
    def range_y(self) -> QCPRange:
        retvalue = self._graph.data().valueRange()[0]
        if retvalue.lower == retvalue.upper == 0.0:
            retvalue = QCPRange(-1.0, 1.0)
        return retvalue

    def refresh_data(self):
        self._set_data()

    def _set_style(self):
        pen = QPen(PEN_STYLE[self._signal.line_type])
        pen.setColor(QColor.fromRgb(*self._signal.rgb))
        self._graph.setPen(pen)
        for ptr in self.__msr_ptr:
            ptr.slot_set_color()
        for ptr in self.__lvl_ptr:
            ptr.slot_set_color()
        self._graph.parentPlot().replot()

    def refresh_scatter(self, scat_style: EScatter) -> bool:
        if self.__scat_style != scat_style:
            if scat_style < EScatter.P:
                shape = QCPScatterStyle(QCPScatterStyle.ssNone)
            elif scat_style < EScatter.D:
                shape = QCPScatterStyle(QCPScatterStyle.ssPlus)
            else:
                shape = self.DigitScatterStyle()
            self._graph.setScatterStyle(shape)
            # <dirtyhack>
            '''
            if self.__pps < iosc.const.X_SCATTER_NUM <= pps:
                # self.graph().setScatterStyle(self.__myscatter)
                for i, d in enumerate(self.graph().data()):
                    ScatterLabel(i, d, self)
            elif self.__pps >= iosc.const.X_SCATTER_NUM > pps:
                for i in reversed(range(self.itemCount())):
                    if isinstance(self.item(i), ScatterLabel):
                        self.removeItem(i)
            '''
            # </dirtyhack>
            self.__scat_style = scat_style
            return True

    def add_ptr_msr(self, uid: int, i: int):
        """Add new MsrPtr"""
        self.__msr_ptr.add(MsrPtr(self, self._root, self._signal, uid, i))

    def del_ptr_msr(self, ptr: MsrPtr):
        """Del MsrPtr"""
        ptr.clean()
        self.__msr_ptr.remove(ptr)
        self._graph.parentPlot().removeItem(ptr)
        self._graph.parentPlot().replot()

    def add_ptr_lvl(self, uid: int, y: Optional[float] = None):
        self.__lvl_ptr.add(LvlPtr(self, self._root, self._signal, uid, y or self.range_y.upper))

    def del_ptr_lvl(self, ptr: LvlPtr):
        """Del LvlPtr"""
        ptr.clean()
        self.__lvl_ptr.remove(ptr)
        self._graph.parentPlot().removeItem(ptr)
        self._graph.parentPlot().replot()

    def clean(self):
        """Clean up before deleting"""
        super().clean()
        for ptr in reversed(tuple(self.__msr_ptr)):
            self.del_ptr_msr(ptr)
        for ptr in reversed(tuple(self.__lvl_ptr)):
            self.del_ptr_lvl(ptr)

    @property
    def state(self) -> State:
        return self.State(
            signal=self._signal,
            msr_ptr=[ptr.state for ptr in self.__msr_ptr],
            lvl_ptr=[ptr.state for ptr in self.__lvl_ptr]
        )

    def restore(self, state: State):
        """Restore signal state:
        - [x] MsrPtr[]
        - [x] LvlPtr[]
        """
        for s in state.msr_ptr:
            self.add_ptr_msr(s.uid, s.i)
        for s in state.lvl_ptr:
            self.add_ptr_lvl(s.uid, s.y)
