import datetime
# 2. 3rd
from PyQt5.QtCore import QMargins, Qt
from QCustomPlot2 import QCPItemText
# 4. local
import iosc.const
from iosc.sig.widget.common import OneBarPlot


class PtrLabel(QCPItemText):
    _oscwin: 'ComtradeWidget'

    def __init__(self, parent: 'TimeStampsPlot'):
        super().__init__(parent)
        self._oscwin = parent.parent().parent()
        self.setTextAlignment(Qt.AlignCenter)
        self.setPadding(QMargins(2, 2, 2, 2))
        self.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)
        self.setFont(iosc.const.FONT_TOPBAR)
        self.setColor(iosc.const.COLOR_LABEL_X)  # text
        self.setLayer("tips")

    def _update_ptr(self, i: int):
        """Repaint/__move main ptr value label (%.2f)
        :fixme: draw in front of ticks
        """
        x = self._oscwin.i2x(i)  # from z-point, ms
        self.setText((self._oscwin.osc.raw.cfg.trigger_timestamp + datetime.timedelta(milliseconds=x)).time().isoformat())
        self.position.setCoords(x, 0)
        self.parentPlot().replot()


class PtrLabelMain(PtrLabel):
    def __init__(self, parent: 'TimeStampsPlot'):
        super().__init__(parent)
        self.setBrush(iosc.const.BRUSH_PTR_MAIN)  # rect
        self.__slot_ptr_move(self._oscwin.main_ptr_i)
        self._oscwin.signal_ptr_moved_main.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, i: int):
        self._update_ptr(i)


class PtrLabelTmp(PtrLabel):
    _uid: int

    def __init__(self, parent: 'TimeStampsPlot', uid: int):
        super().__init__(parent)
        self._uid = uid
        self.setBrush(iosc.const.BRUSH_PTR_TMP)  # rect
        self.__slot_ptr_move(uid, self._oscwin.tmp_ptr_i[uid])
        self._oscwin.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, uid: int, i: int):
        if uid == self._uid:
            self._update_ptr(i)


class TimeStampsPlot(OneBarPlot):
    __zero_ptr_label: QCPItemText
    __main_ptr_label: PtrLabelMain
    _tmp_ptr: dict[int, PtrLabelTmp]

    def __init__(self, parent: 'TimeStampsBar'):
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
        self.__zero_ptr_label.setText(self._oscwin.osc.raw.cfg.trigger_timestamp.time().isoformat())

    def _slot_ptr_add_tmp(self, uid: int):
        """Add new TmpPtr"""
        self._tmp_ptr[uid] = PtrLabelTmp(self, uid)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr"""
        self.removeItem(self._tmp_ptr[uid])
        del self._tmp_ptr[uid]
        self.replot()
