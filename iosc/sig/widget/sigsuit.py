"""SignalSuit and successors"""
# 1. std
from typing import Optional, Union, TypeAlias, Dict, Any, List
# 2. 3rd
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QBrush, QPen
from QCustomPlot_PyQt5 import QCPGraph, QCPScatterStyle, QCPRange
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.core.sigfunc import func_list, hrm1, hrm2, hrm3, hrm5
from iosc.sig.widget.ctrl import ABSignalLabel
from iosc.sig.widget.dialog import StatusSignalPropertiesDialog, AnalogSignalPropertiesDialog
from iosc.sig.widget.ptr import MsrPtr, LvlPtr
# x. const
PEN_STYLE = (Qt.SolidLine, Qt.DotLine, Qt.DashDotDotLine)
HRM_N2F = {1: hrm1, 2: hrm2, 3: hrm3, 5: hrm5}


class SignalSuit(QObject):
    """Base signal container class."""

    _signal: mycomtrade.ABSignal
    oscwin: 'ComtradeWidget'  # noqa: F821
    bar: Optional['HDBar']  # noqa: F821
    num: Optional[int]  # order number in bar
    _label: Optional[ABSignalLabel]
    graph: Optional[QCPGraph]
    _hidden: bool
    color: QColor
    signal_chg_color = pyqtSignal(QColor)

    def __init__(self, signal: mycomtrade.ABSignal, oscwin: 'ComtradeWidget'):  # noqa: F821
        """Init SignalSuit object."""
        super().__init__()
        self.oscwin = oscwin
        self._signal = signal
        self.bar = None
        self.num = None  # signal order number in bar
        self._label = None
        self.graph = None
        self._hidden = False
        self.color = iosc.const.COLOR_SIG_DEFAULT.get(self._signal.ph.lower(), iosc.const.COLOR_SIG_UNKNOWN)
        oscwin.signal_x_zoom.connect(self.__slot_retick)

    @property
    def is_bool(self) -> bool:
        """:return: Whether signal is discrete"""
        return self._signal.is_bool

    @property
    def sid(self) -> str:
        """:return: Signal ID (name)"""
        return self._signal.sid

    @property
    def i(self) -> int:
        """:return: Signal order number in osc signal list.
        Used in:
        - ComtradeWidget.cfg_save()  # cvd, hd
        - ComtradeWidget.cfg_restore()  # cvd, hd
        - CDVWindow._do_settings()
        - HDWindow._do_settings()
        """
        return self._signal.i

    @property
    def hidden(self) -> bool:
        """:return: Whether SignalSuit is hidden."""
        return self._hidden

    @hidden.setter
    def hidden(self, hide: bool):
        """Set SignalSuit hidden flag."""
        if self._hidden != hide:
            self._label.setHidden(hide)
            self.graph.setVisible(not hide)
            self._hidden = hide
            self.bar.update_stealth()

    def v_slice(self, i0: int, i1: int) -> List[float | int]:
        """Get slice of signal values from i0-th to i1-th *including*.
        :param i0: Start index
        :param i1: End index
        :return: Signal values in range.

        Used:
        - AGraphItem | / (v_max - v_min)
        - BGraphItem
        """
        return self._signal.values(self.oscwin.shifted)[i0:i1 + 1]

    # @property
    # def range_y(self) -> QCPRange:  # virtual

    # @property
    # def _data_y(self) -> List[float]:  # virtual

    # def sig2str_i(self, i: int) -> str:  # virtual

    def get_label_html(self, with_values: bool = False) -> Optional[str]:
        """HTML-compatible label."""
        if self._label:
            txt = self._label.text().split('\n')
            return '<br/>'.join(txt) if with_values else txt[0]

    def _set_data(self):
        self.graph.setData(self.bar.table.oscwin.osc.x, self._data_y, True)

    def _set_style(self):
        if self._label:
            self._label.set_color()
        self.signal_chg_color.emit(self.color)  # Rx by: CVD

    def embed(self, bar: 'HDBar', num: int):  # noqa: F821
        """Embed SignalSuit into bar."""
        self.bar = bar
        self.num = num
        self._label = self.bar.ctrl.sig_add(self)
        self.graph = self.bar.gfx.graph_add()
        self._set_data()
        self._set_style()
        self.graph.parentPlot().slot_refresh()
        self.__slot_retick()

    def detach(self):
        """Detach SignalSuit from parent bar."""
        self.bar.ctrl.sig_del(self.num)
        self.bar.gfx.graph_del(self.graph)
        self.bar.gfx.plot.replot()
        self.num = None
        self.bar = None

    def __slot_retick(self):
        """Update scatter style on x-zoom change."""
        if self.graph:
            now = self.graph.scatterStyle().shape() != QCPScatterStyle.ssNone
            need = self.oscwin.x_sample_width_px() >= iosc.const.X_SCATTER_MARK
            if now != need:
                self.graph.setScatterStyle(QCPScatterStyle(
                    QCPScatterStyle.ssPlus if need else QCPScatterStyle.ssNone
                ))
                self.graph.parentPlot().replot()  # bad solution but ...

    def set_highlight(self, v: bool):
        """Highlight signal label due 'Find' operation."""
        if self._label:
            if self._label.isSelected() != v:
                self._label.setSelected(v)


class StatusSignalSuit(SignalSuit):
    """Inner Status signal container."""

    def __init__(self, signal: mycomtrade.StatusSignal, oscwin: 'ComtradeWidget'):  # noqa: F821
        """Init StatusSignalSuit object."""
        super().__init__(signal, oscwin)

    @property
    def range_y(self) -> QCPRange:
        """:return: Main and max signal value.

        For calculating parent plot y-size.
        """
        return QCPRange(0.0, 1.0)

    @property
    def _data_y(self) -> List[float]:
        """Used in: self.graph.setData()"""
        return [v * 2 / 3 for v in self._signal.values()]

    def sig2str_i(self, i: int) -> str:
        """:return: string repr of signal in sample #i."""
        return str(self._signal.value(i))

    def _set_style(self):
        super()._set_style()
        brush = QBrush(iosc.const.BRUSH_D)
        brush.setColor(self.color)
        self.graph.setBrush(brush)

    def do_sig_property(self):
        """Show/set signal properties."""
        if StatusSignalPropertiesDialog(self).execute():
            self._set_style()
            self.graph.parentPlot().replot()


class AnalogSignalSuit(SignalSuit):
    """Inner Analog signal container."""

    line_style: int
    msr_ptr: dict[int: list[Optional[MsrPtr], int, int]]  # uid: [obj, i, func_i]
    lvl_ptr: dict[int: list[Optional[LvlPtr], float]]  # uid: [obj, y]

    def __init__(self, signal: mycomtrade.AnalogSignal, oscwin: 'ComtradeWidget'):  # noqa: F821
        """Init AnalogSignalSuit object."""
        self.line_style = 0
        self.msr_ptr = dict()
        self.lvl_ptr = dict()
        super().__init__(signal, oscwin)
        self.oscwin.signal_chged_shift.connect(self.__slot_reload_data)

    @property
    def uu(self) -> str:
        """:return: Signal unit.

        Used in:
        - CVDTable.refresh_signals()
        - AnalogSignalPropertiesDialog.__init__()
        """
        return self._signal.uu

    @property
    def info(self) -> Dict[str, Any]:
        """Misc signal info.

        :return: Dict with signal info.
        Used in:
        - AnalogSignalPropertiesDialog.__init__()
        """
        return {
            'p': self._signal.primary,  # float
            's': self._signal.secondary,  # float
            'pors': self._signal.pors  # str
        }

    @property
    def range_y(self) -> QCPRange:
        """:return: Min and max signal values."""
        retvalue = self.graph.data().valueRange()[0]
        if retvalue.lower == retvalue.upper == 0.0:
            retvalue = QCPRange(-1.0, 1.0)
        return retvalue

    @property
    def _data_y(self) -> List[float]:
        """Used: self.graph.setData()"""
        divider = max(abs(self.v_min), abs(self.v_max))
        if divider == 0.0:
            divider = 1.0
        return [v / divider for v in self._signal.values(self.oscwin.shifted)]

    @property
    def v_min(self) -> float:
        """:return: Min signal value.

        Used:
        - AGraphItem.__init__
        - LvlPtr
        """
        return self._signal.v_min(self.oscwin.shifted)

    @property
    def v_max(self) -> float:
        """:return: Max signal value.

        Used:
        - AGraphItem.__init__
        - LvlPtr
        """
        return self._signal.v_max(self.oscwin.shifted)

    @property
    def pors_mult(self) -> float:
        """:return: Multiplier pri vs sec according to current pors switch.

        Used:
        - LvlPtr
        """
        return self._signal.get_mult(self.oscwin.show_sec)

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
        """Show/set signal properties."""
        if AnalogSignalPropertiesDialog(self).execute():
            self._set_style()
            self.graph.parentPlot().replot()

    def embed(self, bar: 'HDBar', num: int):  # noqa: F821
        """Embed (add) object into bar."""
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
        """Detach object from parent bar."""
        for uid in self.msr_ptr.keys():
            self.__kill_ptr_msr(uid)
        for uid in self.lvl_ptr.keys():
            self.__kill_ptr_lvl(uid)
        super().detach()

    def sig2str(self, y: float) -> str:
        """:return: String repr of signal value.

        Depends on:
        - signal value (datum)
        - pors (global)
        - orig/shifted (global, indirect).
        Used in:
        - LvlPtr.__slot_update_text()
        """
        return self._signal.as_str(y)

    def sig2str_i(self, i: int) -> str:
        """:return: string repr of signal in sample #i.

        Depends on:
        - signal value
        - in index i
        - selected function[func_i]
        - pors (global)
        - [orig/shifted (global, indirect)].
        Used in:
        - AnalogSignalLable._value_str()
        - MsrPtr.__slot_update_text()
        """
        # v = func_list[self.oscwin.viewas](self._signal.value, i, self.oscwin.osc.spp)
        # return self._signal.as_str_full(v, self.oscwin.show_sec)
        return self._signal.as_str_full(
            self._signal.value(i, self.oscwin.shifted, self.oscwin.show_sec, self.oscwin.viewas)
        )

    def hrm(self, hrm_no: int, t_i: int) -> complex:
        """Harmonic #1 of the signal.

        :param hrm_no: Harmonic no (1, 2, 3, 5)
        :param t_i: Point of x-axis
        :return: Complex value of harmonic

        Used:
        - CVD
        - HDBar
        """
        # return HRM_N2F[hrm_no](self._signal.value, t_i, self.oscwin.osc.spp)
        return self._signal.value(t_i, self.oscwin.shifted, self.oscwin.show_sec, HRM_N2F[hrm_no])

    def __slot_reload_data(self):
        self._set_data()
        self._label.slot_update_value()
        self.graph.parentPlot().slot_rerange_y()

    def add_ptr_msr(self, uid: int, i: int, f: Optional[int] = None):
        """Add new MsrPtr.

        Call from ComtradeWidget.
        :param uid: Uniq (throuh app) id
        :param i: X-index
        :param f: Function number
        """
        self.msr_ptr[uid] = [None, i, f if f is not None else self.oscwin.viewas]
        MsrPtr(self, uid)

    def del_ptr_msr(self, uid: int):  # TODO: detach itself at all
        """Del MsrPtr.

        Call from MsrPtr context menu
        """
        self.__kill_ptr_msr(uid)
        del self.msr_ptr[uid]
        self.graph.parentPlot().replot()

    def add_ptr_lvl(self, uid: int, y: Optional[float] = None):
        """Add new LvlPtr to the ss.

        Call from ComtradeWidget.
        """
        # self.lvl_ptr.add(LvlPtr(self, self.oscwin, uid, y or self.range_y.upper))
        self.lvl_ptr[uid] = [None, y or self.range_y.upper]
        LvlPtr(self, uid)

    def del_ptr_lvl(self, uid: int):
        """Del LvlPtr.

        Call from LvlPtr context menu.
        """
        self.__kill_ptr_lvl(uid)
        del self.lvl_ptr[uid]
        self.graph.parentPlot().replot()


ABSignalSuit: TypeAlias = Union[AnalogSignalSuit, StatusSignalSuit]
