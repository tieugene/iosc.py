# 1. std
from enum import IntEnum
# 2. 3rd
from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel, QWidget, QScrollBar, QGridLayout
from QCustomPlot2 import QCustomPlot, QCPGraph, QCPAxisTickerFixed
# 3. local
import iosc.const
from iosc.sig.widget.hline import HLine
from iosc.sig.widget.ptr import MainPtr, TmpPtr, SCPtr


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
        _oscwin: 'ComtradeWidget'
        _main_ptr: MainPtr
        _sc_ptr: SCPtr
        _tmp_ptr: dict[int, TmpPtr]
        ptr_selected: bool

        def __init__(self, parent: 'BarPlotWidget'):
            super().__init__(parent)
            self._oscwin = parent.bar.table.oscwin
            self.__squeeze()
            self.__decorate()
            self.__set_data()
            self._main_ptr = MainPtr(self.graph(0), self._oscwin)  # after graph()
            self._sc_ptr = SCPtr(self.graph(0), self._oscwin)
            self._tmp_ptr = dict()
            self.ptr_selected = False
            # self.yAxis.setRange(*self.__y_range)  # not helps
            # self.slot_rerange_y()  # not helps
            # self.xAxis.setRange(x_coords[0], x_coords[-1])
            self._oscwin.xscroll_bar.valueChanged.connect(self.__slot_rerange_x_force)
            self._oscwin.xscroll_bar.signal_update_plots.connect(self.__slot_rerange_x)
            self._oscwin.signal_x_zoom.connect(self.__slot_retick)
            self._oscwin.signal_ptr_add_tmp.connect(self._slot_ptr_add_tmp)
            self._oscwin.signal_ptr_del_tmp.connect(self._slot_ptr_del_tmp)

        @property
        def __y_range(self) -> tuple[float, float]:
            mi = ma = 0.0  # min, max
            for ss in self.parent().bar.signals:
                r = ss.range_y
                mi = min(round(r.lower, 2), mi)
                ma = max(round(r.upper, 2), ma)
            dm = (ma - mi) * 0.1
            return mi - dm, ma + dm

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

        def __set_data(self):
            """Set data for global xPtrs"""
            self.addGraph()  # main graph
            x_data = self._oscwin.osc.x
            self.graph(0).setData(x_data, [0.0] * len(x_data), True)

        def mousePressEvent(self, event: QMouseEvent):
            super().mousePressEvent(event)  # always .isAcepted() after this
            if event.button() == Qt.LeftButton and not self.ptr_selected:  # check selectable
                i_new = self._oscwin.x2i(self.xAxis.pixelToCoord(event.x()))
                self._oscwin.slot_ptr_moved_main(i_new)  # __move MainPtr here
                super().mousePressEvent(event)  # and select it

        def slot_rerange_y(self):
            """Refresh plot on YScroller move.
            FIXME: something bad 1st time
            """
            y_range = self.__y_range
            y_width = y_range[1] - y_range[0]
            ys_range = self.parent().ys.range_norm
            self.yAxis.setRange(
                y_range[0] + y_width * ys_range[0],
                y_range[0] + y_width * ys_range[1]
            )
            # self.yAxis.setRange(ys_range[0] - iosc.const.SIG_A_YPAD, ys_range[1] + iosc.const.SIG_A_YPAD)
            self.replot()

        def __slot_rerange_x(self):
            x_coords = self._oscwin.osc.x
            x_width = self._oscwin.osc.x_size
            self.xAxis.setRange(
                x_coords[0] + self._oscwin.xscroll_bar.norm_min * x_width,
                x_coords[0] + self._oscwin.xscroll_bar.norm_max * x_width,
            )

        def __slot_rerange_x_force(self):
            self.__slot_rerange_x()
            self.replot()

        def __slot_retick(self):
            self.xAxis.ticker().setTickStep(iosc.const.X_PX_WIDTH_uS[self._oscwin.x_zoom] / 10)
            self.replot()

        def slot_refresh(self):
            """Refresh plot after bar/signal moves"""
            self.__slot_rerange_x()
            self.__slot_retick()

        def _slot_ptr_add_tmp(self, ptr_id: int):
            """Add new TmpPtr"""
            self._tmp_ptr[ptr_id] = TmpPtr(self.graph(0), self._oscwin, ptr_id)

        def _slot_ptr_del_tmp(self, uid: int):
            """Del TmpPtr"""
            self.removeItem(self._tmp_ptr[uid])
            del self._tmp_ptr[uid]
            self.replot()

    bar: 'SignalBar'
    ys: YScroller
    yzlabel: YZLabel
    plot: BarPlot
    hline: HLine

    def __init__(self, bar: 'SignalBar'):
        super().__init__()
        self.bar = bar
        self.ys = self.YScroller(self)
        self.yzlabel = self.YZLabel(self)
        self.plot = BarPlotWidget.BarPlot(self)
        self.hline = HLine(self)
        layout = QGridLayout()
        layout.addWidget(self.plot, 0, 0)
        layout.addWidget(self.ys, 0, 1)
        layout.addWidget(self.hline, 1, 0, 1, -1)
        self.setLayout(layout)
        self.layout().setContentsMargins(QMargins())
        self.layout().setSpacing(0)
        self.ys.valueChanged.connect(self.plot.slot_rerange_y)

    def sig_add(self) -> QCPGraph:
        return self.plot.addGraph()

    def sig_del(self, gr: QCPGraph):
        self.plot.removeGraph(gr)

    def update_statusonly(self):
        """Update some things depending on if bar is status-only:
        - Y-resize widget
        """
        self.hline.setEnabled(not self.bar.is_bool)
