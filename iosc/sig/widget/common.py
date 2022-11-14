"""Signal wrappers, commmon things."""
import cmath
import math
# 1. std
from typing import Optional, Union
# 2. 3rd
from PyQt5.QtCore import QObject, pyqtSignal, QMargins, Qt
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCPGraph, QCPScatterStyle, QCustomPlot, QCPRange
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.core.sigfunc import func_list
from iosc.sig.widget.ctrl import BarCtrlWidget, StatusSignalLabel, AnalogSignalLabel
from iosc.sig.widget.chart import BarPlotWidget
from iosc.sig.widget.dialog import StatusSignalPropertiesDialog, AnalogSignalPropertiesDialog
from iosc.sig.widget.ptr import MsrPtr, LvlPtr

PEN_STYLE = (Qt.SolidLine, Qt.DotLine, Qt.DashDotDotLine)


class SignalSuit(QObject):
    oscwin: 'ComtradeWidget'
    signal: Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal]
    bar: Optional['SignalBar']
    num: Optional[int]  # order number in bar
    _label: Optional[Union[StatusSignalLabel, AnalogSignalLabel]]
    graph: Optional[QCPGraph]
    _hidden: bool
    color: QColor

    def __init__(self, signal: Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal], oscwin: 'ComtradeWidget'):
        super().__init__()
        self.oscwin = oscwin
        self.signal = signal
        self.bar = None
        self.num = None  # signal order number in bar
        self._label = None
        self.graph = None
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
            self.graph.setVisible(not hide)
            self._hidden = hide
            self.bar.update_stealth()

    @property
    def _data_y(self) -> list:
        return []  # stub

    def _set_data(self):
        self.graph.setData(self.bar.table.oscwin.osc.x, self._data_y, True)

    def _set_style(self):
        if self._label:
            self._label.set_color()

    def embed(self, bar: 'SignalBar', num: int):
        self.bar = bar
        self.num = num
        self._label = self.bar.ctrl.sig_add(self)
        self.graph = self.bar.gfx.graph_add()
        self._set_data()
        self._set_style()
        self.graph.parentPlot().slot_refresh()
        self.__slot_retick()

    def detach(self):
        self.bar.ctrl.sig_del(self.num)
        self.bar.gfx.graph_del(self.graph)
        self.bar.gfx.plot.replot()
        self.num = None
        self.bar = None

    def __slot_retick(self):
        """Update scatter style on x-zoom change"""
        if self.graph:
            now = self.graph.scatterStyle().shape() != QCPScatterStyle.ssNone
            need = self.oscwin.x_sample_width_px() >= iosc.const.X_SCATTER_MARK
            if now != need:
                self.graph.setScatterStyle(QCPScatterStyle(
                    QCPScatterStyle.ssPlus if need else QCPScatterStyle.ssNone
                ))
                self.graph.parentPlot().replot()  # bad solution but ...


class StatusSignalSuit(SignalSuit):
    def __init__(self, signal: mycomtrade.StatusSignal, oscwin: 'ComtradeWidget'):
        super().__init__(signal, oscwin)

    @property
    def range_y(self) -> QCPRange:
        """For calculating parent plot y-size"""
        return QCPRange(0.0, 1.0)

    @property
    def _data_y(self) -> list:
        return [v * 2 / 3 for v in self.signal.value]

    def _set_style(self):
        super()._set_style()
        brush = QBrush(iosc.const.BRUSH_D)
        brush.setColor(self.color)
        self.graph.setBrush(brush)

    def do_sig_property(self):
        """Show/set signal properties"""
        if StatusSignalPropertiesDialog(self).execute():
            self._set_style()
            self.graph.parentPlot().replot()


class AnalogSignalSuit(SignalSuit):
    line_style: int
    msr_ptr: dict[int: list[Optional[MsrPtr], int, int]]  # uid: [obj, i, func_i]
    lvl_ptr: dict[int: list[Optional[LvlPtr], float]]  # uid: [obj, y]

    def __init__(self, signal: mycomtrade.AnalogSignal, oscwin: 'ComtradeWidget'):
        self.line_style = 0
        self.msr_ptr = dict()
        self.lvl_ptr = dict()
        super().__init__(signal, oscwin)
        self.oscwin.signal_chged_shift.connect(self.__slot_reload_data)

    @property
    def range_y(self) -> QCPRange:
        retvalue = self.graph.data().valueRange()[0]
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
        self.graph.setPen(pen)
        for v in self.msr_ptr.values():
            if ptr := v[0]:
                ptr.slot_set_color()
        for v in self.lvl_ptr.values():
            if ptr := v[0]:
                ptr.slot_set_color()

    def do_sig_property(self):
        """Show/set signal properties"""
        if AnalogSignalPropertiesDialog(self).execute():
            self._set_style()
            self.graph.parentPlot().replot()

    def embed(self, bar: 'SignalBar', num: int):
        super().embed(bar, num)
        for uid in self.msr_ptr.keys():
            MsrPtr(self, uid)
        for uid in self.lvl_ptr.keys():
            LvlPtr(self, uid)

    def __kill_ptr_msr(self, uid: int):
        if ptr := self.msr_ptr[uid][0]:
            ptr.suicide()
            del ptr  # or ptr.deleteLater()

    def __kill_ptr_lvl(self, uid: int):
        if ptr := self.lvl_ptr[uid][0]:
            ptr.suicide()
            del ptr  # or ptr.deleteLater()

    def detach(self):
        for uid in self.msr_ptr.keys():
            self.__kill_ptr_msr(uid)
        for uid in self.lvl_ptr.keys():
            self.__kill_ptr_lvl(uid)
        super().detach()

    def sig2str(self, y: float) -> str:
        """Return string repr of signal dependong on:
         - signal value
         - pors (global)
         - orig/shifted (global, indirect)"""
        pors_y = y * self.signal.get_mult(self.oscwin.show_sec)
        uu = self.signal.uu_orig
        if abs(pors_y) < 1:
            pors_y *= 1000
            uu = 'm' + uu
        elif abs(pors_y) > 1000:
            pors_y /= 1000
            uu = 'k' + uu
        return "%.3f %s" % (pors_y, uu)

    def sig2str_i(self, i: int) -> str:  # FIXME: to AnaloSignalSuit
        """Return string repr of signal dependong on:
         - signal value
         - in index i
         - selected function[func_i]
         - pors (global)
         - orig/shifted (global, indirect)"""
        func = func_list[self.oscwin.viewas]
        v = func(self.signal.value, i, self.oscwin.osc.spp)
        if isinstance(v, complex):  # hrm1
            y = abs(v)
        else:
            y = v
        y_str = self.sig2str(y)
        if isinstance(v, complex):  # hrm1
            return "%s / %.3f°" % (y_str, math.degrees(cmath.phase(v)))
        else:
            return y_str

    def __slot_reload_data(self):
        self._set_data()
        self._label.slot_update_value()
        self.graph.parentPlot().slot_rerange_y()

    def add_ptr_msr(self, uid: int, i: int):
        """Add new MsrPtr.
        Call from ComtradeWidget."""
        self.msr_ptr[uid] = [None, i, self.oscwin.viewas]
        MsrPtr(self, uid)

    def del_ptr_msr(self, uid: int):  # TODO: detach itself at all
        """Del MsrPtr.
        Call from MsrPtr context menu"""
        self.__kill_ptr_msr(uid)
        del self.msr_ptr[uid]
        self.graph.parentPlot().replot()

    def add_ptr_lvl(self, uid: int, y: Optional[float] = None):
        """Add new LvlPtr to the ss.
        Call from ComtradeWidget."""
        # self.lvl_ptr.add(LvlPtr(self, self.oscwin, uid, y or self.range_y.upper))
        self.lvl_ptr[uid] = [None, y or self.range_y.upper]
        LvlPtr(self, uid)

    def del_ptr_lvl(self, uid: int):
        """Del LvlPtr.
        Call from LvlPtr context menu."""
        self.__kill_ptr_lvl(uid)
        del self.lvl_ptr[uid]
        self.graph.parentPlot().replot()


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

    @property
    def hidden(self) -> bool:
        return self.table.isRowHidden(self.row)

    @hidden.setter
    def hidden(self, h: bool):
        if self.hidden != h:
            self.table.setRowHidden(self.row, h)

    @property
    def height(self) -> int:
        return self.table.rowHeight(self.row)

    @height.setter
    def height(self, h: int):
        if self.height != h:
            self.table.setRowHeight(self.row, h)

    @property
    def sig_count(self) -> int:
        return len(self.signals)

    def is_bool(self, w_hidden: bool = False) -> Optional[bool]:
        """Whether bar contains status signals only"""
        if self.signals:
            retvalue = True
            for ss in self.signals:
                if not ss.hidden or w_hidden:
                    retvalue &= ss.signal.is_bool
            return retvalue

    def suicide(self):
        del self.table.bars[self.row]
        self.table.removeCellWidget(self.row, 0)
        self.table.removeCellWidget(self.row, 1)
        self.table.removeRow(self.row)
        self.ctrl.close()
        self.gfx.close()
        self.deleteLater()

    def zoom_dy(self, dy: int):
        """Y-zoom button changed.
        Call from BarCtrlWidget.ZoomButtonBox.
        :param dy: -1=decrease, 1=increase, 0=reset to 1
        """
        if dy:
            if 1 <= self.zoom_y + dy <= 1000:
                self.zoom_y += dy
                self.signal_zoom_y_changed.emit()
        elif self.zoom_y > 1:
            self.zoom_y = 1
            self.signal_zoom_y_changed.emit()

    def sig_add(self, ss: Union[StatusSignalSuit, AnalogSignalSuit]):
        is_bool_b4 = self.is_bool(True)
        ss.embed(self, len(self.signals))
        self.signals.append(ss)
        if is_bool_b4 is None:  # 1st signal
            self.height = iosc.const.BAR_HEIGHT_D if ss.signal.is_bool else iosc.const.BAR_HEIGHT_A_DEFAULT
        elif is_bool_b4 and not ss.signal.is_bool:  # Analog join to status-only
            self.height = iosc.const.BAR_HEIGHT_A_DEFAULT
        # else: do nothing
        self.update_stealth()

    def sig_move(self, i: int, other_bar: 'SignalBar'):
        ss = self.signals[i]
        del self.signals[i]
        ss.detach()
        other_bar.sig_add(ss)
        if self.signals:
            for i, ss in enumerate(self.signals):
                ss.num = i
            if self.is_bool(True):
                self.zoom_dy(0)  # reset y-zoom for status-only bar
                self.height = iosc.const.BAR_HEIGHT_D
            self.update_stealth()
        else:
            self.suicide()

    def update_stealth(self):
        """Update row visibility according to children hidden state"""
        hide_me = True
        for ss in self.signals:
            hide_me &= ss.hidden
        self.hidden = hide_me
        if not hide_me:
            self.__update_statusonly()
            self.gfx.plot.slot_rerange_y()

    def __slot_unhide_all(self):
        for ss in self.signals:
            ss.hidden = False

    def __update_statusonly(self):
        # if not self.isHidden():
        self.ctrl.update_statusonly()
        self.gfx.update_statusonly()
        # TODO: update row height


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
        # self.xAxis.setRange(self.oscwin.osc.x_min, self.oscwin.osc.x_max)
        self.addLayer("tips")  # default 6 layers (from bottom (0)): background>grid>main>axes>legend>overlay

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
