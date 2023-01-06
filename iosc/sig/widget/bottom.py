"""Bottom things (X-scroller, time scale)."""
# 1. std
import datetime
# 2. 3rd
from PyQt5.QtCore import QMargins, Qt, pyqtSignal
from PyQt5.QtWidgets import QScrollBar
from QCustomPlot_PyQt5 import QCPItemText
# 4. local
import iosc.const
from iosc.sig.widget.slick import SlickPanelPlot, SlickPanelWidget


class __PtrLabel(QCPItemText):
    """Base class for bottom labels."""

    _oscwin: 'ComtradeWidget'  # noqa: F821

    def __init__(self, parent: 'TimeStampsPlot'):
        """Init PtrLabel object."""
        super().__init__(parent)
        self._oscwin = parent.parent().parent()
        self.setTextAlignment(Qt.AlignCenter)
        self.setPadding(QMargins(2, 2, 2, 2))
        self.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)
        self.setFont(iosc.const.FONT_TOPBAR)
        self.setColor(iosc.const.COLOR_LABEL_X)  # text
        self.setLayer("tips")

    def _update_ptr(self, i: int):
        """Repaint/__move main ptr value label (%.2f).

        :fixme: draw in front of ticks
        """
        x = self._oscwin.i2x(i)  # from z-point, ms
        # TODO: make function
        self.setText((self._oscwin.osc.trigger_timestamp + datetime.timedelta(milliseconds=x)).time().isoformat())
        self.position.setCoords(x, 0)
        self.parentPlot().replot()


class PtrLabelMain(__PtrLabel):
    """Bottom MainPTr label."""

    def __init__(self, parent: 'TimeStampsPlot'):
        """Init PtrLabelMain object."""
        super().__init__(parent)
        self.setBrush(iosc.const.BRUSH_PTR_MAIN)  # rect
        self.__slot_ptr_move(self._oscwin.main_ptr_i)
        self._oscwin.signal_ptr_moved_main.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, i: int):
        self._update_ptr(i)


class PtrLabelTmp(__PtrLabel):
    """Bottom TmpPtr label."""

    _uid: int

    def __init__(self, parent: 'TimeStampsPlot', uid: int):
        """Init PtrLabelTmp object."""
        super().__init__(parent)
        self._uid = uid
        self.setBrush(iosc.const.BRUSH_PTR_TMP)  # rect
        self.__slot_ptr_move(uid, self._oscwin.tmp_ptr_i[uid])
        self._oscwin.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, uid: int, i: int):
        if uid == self._uid:
            self._update_ptr(i)


class TimeStampsPlot(SlickPanelPlot):
    """Bottom time scale graphics."""

    __zero_ptr_label: QCPItemText
    __main_ptr_label: PtrLabelMain
    _tmp_ptr: dict[int, PtrLabelTmp]

    def __init__(self, parent: 'TimeStampsBar'):
        """Init TimeStampsPlot object."""
        super().__init__(parent)
        self.xAxis.setTickLabels(False)
        # self.xAxis.setTickLabelSide(QCPAxis.lsInside)
        # self.xAxis.setTicks(False)
        self.__set_zero()
        self.__main_ptr_label = PtrLabelMain(self)
        self._tmp_ptr = dict()
        self._oscwin.signal_ptr_add_tmp.connect(self._slot_ptr_add_tmp)
        self._oscwin.signal_ptr_del_tmp.connect(self._slot_ptr_del_tmp)

    def __set_zero(self):
        self.__zero_ptr_label = QCPItemText(self)
        self.__zero_ptr_label.setColor(iosc.const.COLOR_LABEL_Z)  # text
        self.__zero_ptr_label.setTextAlignment(Qt.AlignCenter)
        self.__zero_ptr_label.setFont(iosc.const.FONT_TOPBAR)
        self.__zero_ptr_label.setPadding(QMargins(2, 2, 2, 2))
        self.__zero_ptr_label.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)
        self.__zero_ptr_label.setText(self._oscwin.osc.trigger_timestamp.time().isoformat())

    def _slot_ptr_add_tmp(self, uid: int):
        """Add new TmpPtr."""
        self._tmp_ptr[uid] = PtrLabelTmp(self, uid)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr."""
        self.removeItem(self._tmp_ptr[uid])
        del self._tmp_ptr[uid]
        self.replot()


class TimeStampsBar(SlickPanelWidget):
    """Bottom time scale panel."""

    def __init__(self, parent: 'ComtradeWidget'):  # noqa: F821
        """Init TimeStampsBar object."""
        super().__init__(parent)
        self.plot = TimeStampsPlot(self)
        self._post_init()


class XScroller(QScrollBar):
    """Bottom scrollbar."""

    signal_update_plots = pyqtSignal()

    def __init__(self, parent: 'ComtradeWidget'):  # noqa: F821
        """Init XScroller object.

        :param parent: Subj
        :type parent: ComtradeWidget
        :note: An idea:
        - full width = plot width (px)
        - page size = current col1 width (px)
        """
        super().__init__(Qt.Horizontal, parent)
        parent.signal_x_zoom.connect(self.__slot_update_range)
        parent.timeaxis_bar.plot.signal_width_changed.connect(self.__slot_update_page)

    @property
    def norm_min(self) -> float:
        """:return: Normalized (0..1) left page position."""
        return self.value() / (self.maximum() + self.pageStep())

    @property
    def norm_max(self) -> float:
        """:retrun: Normalized (0..1) right page position."""
        return (self.value() + self.pageStep()) / (self.maximum() + self.pageStep())

    def __update_enabled(self):
        self.setEnabled(self.maximum() > 0)

    def __slot_update_range(self):
        """Update maximum against new x-zoom.

        (x_width_px changed, page (px) - not)
        """
        page = self.pageStep()
        x_width_px = self.parent().x_width_px()
        if (max_new := x_width_px - self.pageStep()) < 0:
            max_new = 0
        v_new = min(
            max_new,
            max(
                0,
                round((self.value() + page / 2) / (self.maximum() + page) * x_width_px - (page / 2))
            )
        )
        self.setMaximum(max_new)
        if v_new != self.value():
            self.setValue(v_new)  # emit signal
        else:
            self.signal_update_plots.emit()
        self.__update_enabled()

    def __slot_update_page(self, new_page: int):
        """Update page against new signal windows width."""
        x_max = self.parent().x_width_px()
        if min(new_page, self.pageStep()) < x_max:
            if new_page > x_max:
                new_page = x_max
            self.setPageStep(new_page)
            v0 = self.value()
            self.setMaximum(self.parent().x_width_px() - new_page)  # WARN: value changed w/o signal emit
            if self.value() == v0:
                self.signal_update_plots.emit()  # Force update plots; plan B: self.valueChanged.emit(self.value())
        self.__update_enabled()
