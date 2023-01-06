"""SignalBar"""
# 1. std
from typing import List, Optional, Union
# 2. 3rd
from PyQt5.QtCore import QObject, pyqtSignal
# 3. local
import iosc.const
from iosc.sig.widget.chart import BarPlotWidget
from iosc.sig.widget.sigsuit import SignalSuit, StatusSignalSuit, AnalogSignalSuit, ABSignalSuit
from iosc.sig.widget.ctrl import BarCtrlWidget


class SignalBar(QObject):
    """Inner signal bar container."""

    table: 'SignalBarTable'  # noqa: F821
    row: int
    signals: List[ABSignalSuit]
    zoom_y: int
    ctrl: BarCtrlWidget
    gfx: BarPlotWidget
    signal_zoom_y_changed = pyqtSignal()

    def __init__(self, table: 'SignalBarTable', row: int = -1):  # noqa: F821
        """Init SignalBar object."""
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
        """:return: Bar is hidden."""
        return self.table.isRowHidden(self.row)

    @hidden.setter
    def hidden(self, h: bool):
        """Set bar hidden."""
        if self.hidden != h:
            self.table.setRowHidden(self.row, h)

    @property
    def height(self) -> int:
        """:return: Bar height, px."""
        return self.table.rowHeight(self.row)

    @height.setter
    def height(self, h: int):
        """Set bar height, px."""
        if self.height != h:
            self.table.setRowHeight(self.row, h)

    @property
    def sig_count(self) -> int:
        """:return: SignalSuit count."""
        return len(self.signals)

    def is_bool(self, w_hidden: bool = False) -> Optional[bool]:
        """:return: Whether bar contains status signals only."""
        if self.signals:
            retvalue = True
            for ss in self.signals:
                if not ss.hidden or w_hidden:
                    retvalue &= ss.signal.is_bool
            return retvalue

    def suicide(self):
        """Self destruction."""
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
        """Add SignalSuit suit to self."""
        is_bool_b4 = self.is_bool(True)
        ss.embed(self, len(self.signals))
        self.signals.append(ss)
        if is_bool_b4 is None:  # 1st signal
            self.height = iosc.const.BAR_HEIGHT_D if ss.signal.is_bool else iosc.const.BAR_HEIGHT_A_DEFAULT
        elif is_bool_b4 and not ss.signal.is_bool:  # Analog join to status-only
            self.height = iosc.const.BAR_HEIGHT_A_DEFAULT
        # else: do nothing
        self.update_stealth()

    def sig_move(self, i: int, other_bar: 'HDBar'):  # noqa: F821
        """Move SignalSuit from self to other bar."""
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
        """Update row visibility according to children hidden state."""
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

    def find_signal(self, text: str) -> Optional[SignalSuit]:
        """Try to find signal by substring @ name."""
        for ss in self.signals:
            if (not ss.hidden) and (text in ss.signal.sid):
                return ss


SignalBarList = List[SignalBar]  # custom type
