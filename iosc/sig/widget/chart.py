# 1. std
from enum import IntEnum
# 2. 3rd
from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtWidgets import QLabel, QWidget, QScrollBar, QGridLayout
from QCustomPlot2 import QCustomPlot, QCPGraph, QCPAxisTickerFixed
# 3. local
import iosc.const
from iosc.sig.widget.hline import HLine


class EScatter(IntEnum):
    N = 0  # none
    P = 1  # plus sign
    D = 2  # digit


class BarPlotWidget(QWidget):
    class YZLabel(QLabel):
        def __init__(self, parent: 'BarPlotWidget'):
            super().__init__(parent)
            self.setStyleSheet("QLabel { background-color : red; color : rgba(255,255,255,255) }")
            self.__slot_zoom_changed()
            parent.bar.signal_zoom_y_changed.connect(self.__slot_zoom_changed)

        def __slot_zoom_changed(self):
            z = self.parent().bar.zoom_y
            if z == 1:
                self.hide()
            else:
                if self.isHidden():
                    self.show()
                self.setText(f"×{z}")
                self.adjustSize()

    class YScroller(QScrollBar):
        """Main idea:
        - Constant predefined width (in units; max)
        - Dynamic page (max..min for x1..xMax)
        """

        def __init__(self, parent: 'BarPlotWidget'):
            super().__init__(Qt.Vertical, parent)
            self.__slot_zoom_changed()
            parent.bar.signal_zoom_y_changed.connect(self.__slot_zoom_changed)

        @property
        def y_norm_min(self) -> float:
            """Normalized (0..1) minimal window position"""
            return 1 - (self.value() + self.pageStep()) / iosc.const.Y_SCROLL_HEIGHT

        @property
        def y_norm_max(self) -> float:
            """Normalized (0..1) maximal window position"""
            return 1 - self.value() / iosc.const.Y_SCROLL_HEIGHT

        @property
        def range_norm(self):
            return self.y_norm_min, self.y_norm_max

        def __slot_zoom_changed(self):
            z = self.parent().bar.zoom_y
            if z == 1:
                self.setPageStep(iosc.const.Y_SCROLL_HEIGHT)
                self.setMaximum(0)
                self.setValue(0)  # note: exact in this order
                self.setEnabled(False)
            else:
                v0 = self.value()
                p0 = self.pageStep()
                p1 = round(iosc.const.Y_SCROLL_HEIGHT / z)
                self.setPageStep(p1)
                self.setMaximum(iosc.const.Y_SCROLL_HEIGHT - p1)
                self.setValue(v0 + round((p0 - p1) / 2))
                self.setEnabled(True)

    class BarPlot(QCustomPlot):
        def __init__(self, parent: 'BarPlotWidget'):
            super().__init__(parent)
            self.__squeeze()
            self.__decorate()
            # self.yAxis.setRange(*self.__y_range)  # not helps
            # self.slot_rerange_y()  # not helps
            # x_coords = parent.bar.table.oscwin.x_coords
            # self.xAxis.setRange(x_coords[0], x_coords[-1])
            parent.bar.table.oscwin.xscroll_bar.valueChanged.connect(self.__slot_rerange_x_force)
            parent.bar.table.oscwin.xscroll_bar.signal_update_plots.connect(self.__slot_rerange_x)
            parent.bar.table.oscwin.signal_x_zoom.connect(self.__slot_retick)

        @property
        def __y_range(self) -> tuple[float, float]:
            mi = ma = 0.0  # min, max
            for ss in self.parent().bar.signals:
                r = ss.range_y
                mi = min(round(r.lower, 2), mi)
                ma = max(round(r.upper, 2), ma)
            return mi, ma

        def __squeeze(self):
            ar = self.axisRect(0)  # QCPAxisRect
            ar.setMinimumMargins(QMargins())  # the best
            ar.removeAxis(self.xAxis2)
            ar.removeAxis(self.yAxis2)
            # y
            # self.yAxis.setVisible(False)  # or cp.graph().valueAxis()
            self.yAxis.setTickLabels(False)
            self.yAxis.setTicks(False)
            self.yAxis.setPadding(0)
            self.yAxis.ticker().setTickCount(1)  # the only z-line
            # x
            self.xAxis.setTicker(QCPAxisTickerFixed())
            self.xAxis.setTickLabels(False)
            self.xAxis.setTicks(False)
            self.xAxis.setPadding(0)
            self.__slot_retick()

        def __decorate(self):
            self.yAxis.setBasePen(iosc.const.PEN_NONE)  # hack
            self.yAxis.grid().setZeroLinePen(iosc.const.PEN_ZERO)
            self.xAxis.grid().setZeroLinePen(iosc.const.PEN_ZERO)

        def slot_rerange_y(self):
            """Refresh plot on YScroller move.
            FIXME: something bad 1st time
            """
            ys: BarPlotWidget.YScroller = self.parent().ys
            y_range = self.__y_range
            y_width = y_range[1] - y_range[0]
            ys_range = ys.range_norm
            self.yAxis.setRange(
                y_range[0] + y_width * ys_range[0],
                y_range[0] + y_width * ys_range[1]
            )
            # self.yAxis.setRange(ys_range[0] - iosc.const.SIG_A_YPAD, ys_range[1] + iosc.const.SIG_A_YPAD)
            self.replot()

        def __slot_rerange_x(self):
            oscwin = self.parent().bar.table.oscwin
            x_coords = oscwin.osc.x
            x_width = oscwin.osc.x_size
            self.xAxis.setRange(
                x_coords[0] + oscwin.xscroll_bar.norm_min * x_width,
                x_coords[0] + oscwin.xscroll_bar.norm_max * x_width,
            )

        def __slot_rerange_x_force(self):
            self.__slot_rerange_x()
            self.replot()

        def __slot_retick(self):
            self.xAxis.ticker().setTickStep(iosc.const.X_PX_WIDTH_uS[self.parent().bar.table.oscwin.x_zoom] / 10)
            self.replot()

        def slot_refresh(self):
            """Refresh plot after bar/signal moves"""
            self.__slot_rerange_x()
            self.__slot_retick()

    bar: 'SignalBar'
    ys: YScroller
    yzlabel: YZLabel
    plot: BarPlot

    def __init__(self, bar: 'SignalBar'):
        super().__init__()
        self.bar = bar
        self.ys = self.YScroller(self)
        self.yzlabel = self.YZLabel(self)
        self.plot = BarPlotWidget.BarPlot(self)
        layout = QGridLayout()
        layout.addWidget(self.plot, 0, 0)
        layout.addWidget(self.ys, 0, 1)
        layout.addWidget(HLine(self), 1, 0, 1, -1)
        self.setLayout(layout)
        self.layout().setContentsMargins(QMargins())
        self.layout().setSpacing(0)
        self.ys.valueChanged.connect(self.plot.slot_rerange_y)

    def sig_add(self) -> QCPGraph:
        return self.plot.addGraph()

    def sig_del(self, gr: QCPGraph):
        self.plot.removeGraph(gr)


'''
# FIXME:
class SignalGraph(QObject):  # FIXME: == common.SignalSuit
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
            """
            if self.__pps < iosc.const.X_SCATTER_NUM <= pps:
                # self.graph().setScatterStyle(self.__myscatter)
                for i, d in enumerate(self.graph().data()):
                    ScatterLabel(i, d, self)
            elif self.__pps >= iosc.const.X_SCATTER_NUM > pps:
                for i in reversed(range(self.itemCount())):
                    if isinstance(self.item(i), ScatterLabel):
                        self.removeItem(i)
            """
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
'''
