"""Osc window top things (time scale with dependencies)."""
# 2. 3rd
from PyQt5.QtCore import QMargins, Qt, pyqtSignal
from PyQt5.QtGui import QResizeEvent
from QCustomPlot_PyQt5 import QCPItemText, QCPAxis, QCPAxisTickerFixed
# 3. local
import iosc.const
from iosc.sig.widget.slick import SlickPanelPlot, SlickPanelWidget


class __PtrLabel(QCPItemText):
    """Base class for ptr's top labels."""

    _oscwin: 'ComtradeWidget'  # noqa: F821

    def __init__(self, parent: 'TimeAxisPlot'):
        """Init __PtrLabel object."""
        super().__init__(parent)
        self._oscwin = parent.parent().parent()
        self.setTextAlignment(Qt.AlignCenter)
        self.setPadding(QMargins(2, 2, 2, 2))
        self.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)
        self.setFont(iosc.const.FONT_TOPBAR)
        self.setColor(iosc.const.COLOR_LABEL_X)  # text
        self.setLayer("tips")

    def _mk_text(self, x: float):
        return "%.2f" % x

    def _update_ptr(self, i: int):
        """Repaint/__move main ptr value label (%.2f).

        :fixme: draw in front of ticks
        """
        x = self._oscwin.i2x(i)
        self.setText(self._mk_text(x))
        self.position.setCoords(x, 0)
        self.parentPlot().replot()


class PtrLabelMain(__PtrLabel):
    """Top MainPtr label."""

    def __init__(self, parent: 'TimeAxisPlot'):
        """Init PtrLabelMain object."""
        super().__init__(parent)
        self.setBrush(iosc.const.BRUSH_PTR_MAIN)  # rect
        self._update_ptr(self._oscwin.main_ptr_i)
        self._oscwin.signal_ptr_moved_main.connect(self._update_ptr)


class PtrLabelSC(__PtrLabel):
    """Top SCPtr labels base."""

    def __init__(self, parent: 'TimeAxisPlot'):
        """Init PtrLabelOMP object."""
        super().__init__(parent)
        self.setBrush(iosc.const.BRUSH_PTR_OMP)  # rect
        self._update_ptr(self._oscwin.omp_ptr.i_sc)
        self._oscwin.signal_ptr_moved_sc.connect(self._update_ptr)

    def _mk_text(self, x: float):
        return "SC: %.2f" % x


class PtrLabelPR(__PtrLabel):
    """Top PRPtr labels base."""

    def __init__(self, parent: 'TimeAxisPlot'):
        """Init PtrLabelPR object."""
        super().__init__(parent)
        self.setBrush(iosc.const.BRUSH_PTR_OMP)  # rect
        self._update_ptr(self._oscwin.omp_ptr.i_pr)
        self._oscwin.signal_ptr_moved_pr.connect(self._update_ptr)

    def _mk_text(self, x: float):
        return "PR: %.2f" % x


class PtrLabelTmp(__PtrLabel):
    """Top TmpPtr label."""

    _uid: int
    _name: str

    def __init__(self, parent: 'TimeAxisPlot', uid: int):
        """Init PtrLabelTmp object."""
        super().__init__(parent)
        self._uid = uid
        self._name = ''
        self.setBrush(iosc.const.BRUSH_PTR_TMP)  # rect
        self.__slot_ptr_move(uid, self._oscwin.tmp_ptr_i[uid])
        self._oscwin.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)

    def _mk_text(self, x: float):
        return "%s: %.2f" % (self._name if self._name else "T%d" % self._uid, x)

    @property
    def name(self) -> str:
        """:return: Top TmpPtr label."""
        return self._name

    @name.setter
    def name(self, s: str):
        """Set top TmpPtr label."""
        self._name = s

    def __slot_ptr_move(self, uid: int, i: int):
        if uid == self._uid:
            self._update_ptr(i)


class TimeAxisPlot(SlickPanelPlot):
    """Top time scale graphics."""

    __main_ptr_label: PtrLabelMain
    __sc_ptr_label: PtrLabelSC
    __pr_ptr_label: PtrLabelPR
    _tmp_ptr: dict[int, PtrLabelTmp]
    signal_width_changed = pyqtSignal(int)

    def __init__(self, parent: 'TopBar'):  # noqa: F821
        """Init TimeAxisPlot object."""
        super().__init__(parent)
        self.__main_ptr_label = PtrLabelMain(self)
        if parent.parent().omp_ptr:
            self.__sc_ptr_label = PtrLabelSC(self)
            self.__pr_ptr_label = PtrLabelPR(self)
        self._tmp_ptr = dict()
        # self.xAxis.setTickLabels(True)  # default
        # self.xAxis.setTicks(True)  # default
        self.xAxis.setTickLabelSide(QCPAxis.lsInside)
        self.xAxis.setTicker(QCPAxisTickerFixed())
        self.xAxis.setTickLabelFont(iosc.const.FONT_TOPBAR)
        self.__slot_retick()
        self._oscwin.signal_x_zoom.connect(self.__slot_retick)
        self._oscwin.signal_ptr_add_tmp.connect(self._slot_ptr_add_tmp)
        self._oscwin.signal_ptr_del_tmp.connect(self._slot_ptr_del_tmp)

    def resizeEvent(self, event: QResizeEvent):
        """Inherited."""
        super().resizeEvent(event)
        if event.oldSize().width() != (w := event.size().width()):
            self.signal_width_changed.emit(w)

    def __slot_retick(self):
        self.xAxis.ticker().setTickStep(iosc.const.X_PX_WIDTH_uS[self._oscwin.x_zoom] / 10)
        self.replot()

    def get_tmp_ptr_name(self, uid: id):
        """:return: TmpPtr label."""
        return self._tmp_ptr[uid].name

    def set_tmp_ptr_name(self, uid: id, name: str):
        """Set MtpPtr label."""
        self._tmp_ptr[uid].name = name

    def _slot_ptr_add_tmp(self, uid: int):
        """Add new TmpPtr."""
        self._tmp_ptr[uid] = PtrLabelTmp(self, uid)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr."""
        self.removeItem(self._tmp_ptr[uid])
        del self._tmp_ptr[uid]
        self.replot()


class TimeAxisBar(SlickPanelWidget):
    """Top time scale."""

    plot: TimeAxisPlot  # rewrite

    def __init__(self, parent: 'ComtradeWidget'):  # noqa: F821
        """Init TimeAxisBar object."""
        super().__init__(parent)
        self._label.setText(self.tr("ms"))
        self.plot = TimeAxisPlot(self)
        self._post_init()
