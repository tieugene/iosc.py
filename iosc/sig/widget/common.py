"""Signal wrappers, commmon things.
TODO: StatusSignalSuit, AnalogSignalSuit.
"""
from typing import Optional, Union

# 2. 3rd
from PyQt5.QtCore import QObject, pyqtSignal, QMargins
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCPGraph, QCPScatterStyle, QCustomPlot

import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.ctrl import BarCtrlWidget, SignalLabel
from iosc.sig.widget.chart import BarPlotWidget


class SignalSuit(QObject):
    __oscwin: 'ComtradeWidget'
    signal: Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal]
    bar: Optional['SignalBar']
    num: Optional[int]
    __label: Optional[SignalLabel]
    __graph: Optional[QCPGraph]
    hidden: bool

    def __init__(self, signal: mycomtrade.Signal, oscwin: 'ComtradeWidget'):
        super().__init__()
        self.__oscwin = oscwin
        self.signal = signal
        self.bar = None
        self.num = None  # signal order number in bar
        self.__label = None
        self.__graph = None
        self.hidden = False
        oscwin.signal_x_zoom.connect(self.__slot_retick)

    def embed(self, bar: 'SignalBar', num: int):
        self.bar = bar
        self.num = num
        self.__label = self.bar.ctrl.sig_add(self)
        self.__graph = self.bar.gfx.sig_add()
        self.__graph.setData(self.bar.table.oscwin.osc.x, self.signal.value, True)
        self.__graph.setPen(QPen(self.signal.color))
        self.__graph.parentPlot().slot_refresh()
        self.__slot_retick()

    def detach(self):
        self.bar.ctrl.sig_del(self.num)
        self.bar.gfx.sig_del(self.__graph)
        self.bar.gfx.plot.replot()
        self.num = None
        self.bar = None

    def set_hidden(self, hide: bool):
        if self.hidden != hide:
            self.__label.setHidden(hide)
            self.__graph.setVisible(not hide)
            self.hidden = hide
            self.bar.update_stealth()

    def __slot_retick(self):
        """Update scatter style on x-zoom change"""
        if self.__graph:
            now = self.__graph.scatterStyle().shape() != QCPScatterStyle.ssNone
            need = self.__oscwin.x_sample_width_px() >= iosc.const.X_SCATTER_MARK
            if now != need:
                self.__graph.setScatterStyle(QCPScatterStyle(
                    QCPScatterStyle.ssPlus if need else QCPScatterStyle.ssNone
                ))
                self.__graph.parentPlot().replot()  # bad solution but ...


class SignalBar(QObject):
    table: 'SignalBarTable'
    row: int
    signals: list[SignalSuit]
    zoom_y: int
    ctrl: BarCtrlWidget
    gfx: BarPlotWidget
    signal_zoom_y_changed = pyqtSignal()

    def __init__(self, table: 'SignalBarTable', row: int = -1):
        super().__init__()
        if not (0 <= row < table.rowCount()):
            row = table.rowCount()
        self.table = table
        self.row = row
        self.signals = list()
        self.zoom_y = 1
        self.ctrl = BarCtrlWidget(self)
        self.gfx = BarPlotWidget(self)
        self.table.bars.insert(self.row, self)
        self.table.insertRow(self.row)
        self.table.setCellWidget(self.row, 0, self.ctrl)
        self.table.setCellWidget(self.row, 1, self.gfx)
        self.table.oscwin.signal_unhide_all.connect(self.__slot_unhide_all)

    def suicide(self):
        del self.table.bars[self.row]
        self.table.removeCellWidget(self.row, 0)
        self.table.removeCellWidget(self.row, 1)
        self.table.removeRow(self.row)
        self.ctrl.close()
        self.gfx.close()
        self.deleteLater()

    @property
    def sig_count(self) -> int:
        return len(self.signals)

    def sig_add(self, ss: SignalSuit):
        ss.embed(self, len(self.signals))
        self.signals.append(ss)
        self.update_stealth()

    def sig_move(self, i: int, other_bar: 'SignalBar'):
        ss = self.signals[i]
        del self.signals[i]
        ss.detach()
        other_bar.sig_add(ss)
        if self.signals:
            for i, ss in enumerate(self.signals):
                ss.num = i
            self.update_stealth()
        else:
            self.suicide()

    def update_stealth(self):
        """Update visibility according to children"""
        hide_me = True
        for ss in self.signals:
            hide_me &= ss.hidden
        if hide_me != self.table.isRowHidden(self.row):
            self.table.setRowHidden(self.row, hide_me)

    def __slot_unhide_all(self):
        for ss in self.signals:
            ss.set_hidden(False)
        if self.table.isRowHidden(self.row):
            self.table.setRowHidden(self.row, False)

    def zoom_dy(self, dy: int):
        """Y-zoom button changed"""
        if dy:
            if 1 <= self.zoom_y + dy <= 1000:
                self.zoom_y += dy
                self.signal_zoom_y_changed.emit()
        elif self.zoom_y > 1:
            self.zoom_y = 1
            self.signal_zoom_y_changed.emit()


class OneBarPlot(QCustomPlot):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        ar = self.axisRect(0)
        ar.setMinimumMargins(QMargins())  # the best
        ar.removeAxis(self.yAxis)
        ar.removeAxis(self.xAxis2)
        ar.removeAxis(self.yAxis2)
        self.xAxis.grid().setVisible(False)
        # self.xAxis.setTickLabels(True)  # default
        # self.xAxis.setTicks(True)  # default
        self.xAxis.setPadding(0)
        self.setFixedHeight(24)
        # self.xAxis.setRange(self._oscwin.osc.x_min, self._oscwin.osc.x_max)

    @property
    def _oscwin(self) -> 'ComtradeWidget':
        return self.parent().parent()

    def slot_rerange(self):
        x_coords = self._oscwin.osc.x
        x_width = self._oscwin.osc.x_size
        self.xAxis.setRange(
            x_coords[0] + self._oscwin.xscroll_bar.norm_min * x_width,
            x_coords[0] + self._oscwin.xscroll_bar.norm_max * x_width,
        )

    def slot_rerange_force(self):
        self.slot_rerange()
        self.replot()
