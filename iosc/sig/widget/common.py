"""Signal wrappers, commmon things.
TODO: StatusSignalSuit, AnalogSignalSuit.
"""
# 1. std
from enum import IntEnum
from typing import Optional, Union
# 2. 3rd
from PyQt5.QtCore import QObject, pyqtSignal, QMargins, Qt
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCPGraph, QCPScatterStyle, QCustomPlot, QCPRange
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.ctrl import BarCtrlWidget, StatusSignalLabel, AnalogSignalLabel
from iosc.sig.widget.chart import BarPlotWidget
from iosc.sig.widget.dialog import StatusSignalPropertiesDialog, AnalogSignalPropertiesDialog

PEN_STYLE = (Qt.SolidLine, Qt.DotLine, Qt.DashDotDotLine)


class SignalSuit(QObject):
    _oscwin: 'ComtradeWidget'
    signal: Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal]
    bar: Optional['SignalBar']
    num: Optional[int]  # order number in bar
    _label: Optional[Union[StatusSignalLabel, AnalogSignalLabel]]
    _graph: Optional[QCPGraph]
    _hidden: bool
    color: QColor

    def __init__(self, signal: Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal], oscwin: 'ComtradeWidget'):
        super().__init__()
        self._oscwin = oscwin
        self.signal = signal
        self.bar = None
        self.num = None  # signal order number in bar
        self._label = None
        self._graph = None
        self._hidden = False
        self.color = iosc.const.COLOR_SIG_DEFAULT.get(self.signal.raw2.ph.lower(), iosc.const.COLOR_SIG_UNKNOWN)
        oscwin.signal_x_zoom.connect(self.__slot_retick)

    @property
    def hidden(self) -> bool:
        return self._hidden

    @hidden.setter
    def hidden(self, hide: bool):
        if self._hidden != hide:
            self._label.setHidden(hide)
            self._graph.setVisible(not hide)
            self._hidden = hide
            self.bar.update_stealth()

    @property
    def _data_y(self) -> list:
        return []  # stub

    def _set_data(self):
        self._graph.setData(self.bar.table.oscwin.osc.x, self._data_y, True)

    def _set_style(self):
        if self._label:
            self._label.set_color()

    def embed(self, bar: 'SignalBar', num: int):
        self.bar = bar
        self.num = num
        self._label = self.bar.ctrl.sig_add(self)
        self._graph = self.bar.gfx.sig_add()
        self._set_data()
        self._set_style()
        self._graph.parentPlot().slot_refresh()
        self.__slot_retick()

    def detach(self):
        self.bar.ctrl.sig_del(self.num)
        self.bar.gfx.sig_del(self._graph)
        self.bar.gfx.plot.replot()
        self.num = None
        self.bar = None

    def __slot_retick(self):
        """Update scatter style on x-zoom change"""
        if self._graph:
            now = self._graph.scatterStyle().shape() != QCPScatterStyle.ssNone
            need = self._oscwin.x_sample_width_px() >= iosc.const.X_SCATTER_MARK
            if now != need:
                self._graph.setScatterStyle(QCPScatterStyle(
                    QCPScatterStyle.ssPlus if need else QCPScatterStyle.ssNone
                ))
                self._graph.parentPlot().replot()  # bad solution but ...


class StatusSignalSuit(SignalSuit):
    def __init__(self, signal: mycomtrade.StatusSignal, oscwin: 'ComtradeWidget'):
        super().__init__(signal, oscwin)

    @property
    def range_y(self) -> QCPRange:
        """For calculating parent plot y-size"""
        return QCPRange(0.0, 1.0)

    @property
    def _data_y(self) -> list:
        return self.signal.value

    def _set_style(self):
        super()._set_style()
        brush = QBrush(iosc.const.BRUSH_D)
        brush.setColor(self.color)
        self._graph.setBrush(brush)

    def do_sig_property(self):
        """Show/set signal properties"""
        if StatusSignalPropertiesDialog(self).execute():
            self._set_style()
            self._graph.parentPlot().replot()


class AnalogSignalSuit(SignalSuit):
    line_style: int
    __msr_ptr: set
    __lvl_ptr: set

    def __init__(self, signal: mycomtrade.AnalogSignal, oscwin: 'ComtradeWidget'):
        self.line_style = 0
        self.__msr_ptr = set()
        self.__lvl_ptr = set()
        super().__init__(signal, oscwin)

    @property
    def range_y(self) -> QCPRange:
        retvalue = self._graph.data().valueRange()[0]
        if retvalue.lower == retvalue.upper == 0.0:
            retvalue = QCPRange(-1.0, 1.0)
        return retvalue

    @property
    def _data_y(self) -> list:
        divider = max(abs(min(self.signal.value)), abs(max(self.signal.value)))
        if divider == 0.0:
            divider = 1.0
        return [v / divider for v in self.signal.value]

    def _set_style(self):
        super()._set_style()
        pen = QPen(PEN_STYLE[self.line_style])
        pen.setColor(self.color)
        self._graph.setPen(pen)
        for ptr in self.__msr_ptr:
            ptr.slot_set_color()
        for ptr in self.__lvl_ptr:
            ptr.slot_set_color()

    def do_sig_property(self):
        """Show/set signal properties"""
        if AnalogSignalPropertiesDialog(self).execute():
            self._set_style()
            self._graph.parentPlot().replot()


class SignalBar(QObject):
    table: 'SignalBarTable'
    row: int
    signals: list[Union[StatusSignalSuit, AnalogSignalSuit]]
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

    def sig_add(self, ss: Union[StatusSignalSuit, AnalogSignalSuit]):
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
        """Update row visibility according to children hidden state"""
        hide_me = True
        for ss in self.signals:
            hide_me &= ss.hidden
        if hide_me != self.table.isRowHidden(self.row):
            self.table.setRowHidden(self.row, hide_me)

    def __slot_unhide_all(self):
        for ss in self.signals:
            ss.hidden = False
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
    """Parent for top and bottom bars plots"""

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
