import datetime
# 2. 3rd
from PyQt5.QtCore import QMargins, Qt
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCustomPlot, QCPItemText
# 4. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.common import OneBarPlot


class PtrLabel(QCPItemText):
    _root: QWidget

    def __init__(self, parent: QCustomPlot, root: QWidget):
        super().__init__(parent)
        self._root = root
        self.setTextAlignment(Qt.AlignCenter)
        self.setPadding(QMargins(2, 2, 2, 2))
        self.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)
        self.setFont(iosc.const.FONT_TOPBAR)
        self.setColor(iosc.const.COLOR_LABEL_X)  # text

    def _update_ptr(self, i: int):
        """Repaint/__move main ptr value label (%.2f)
        :fixme: draw in front of ticks
        """
        x = self._root.i2x(i)  # from z-point, ms
        self.setText((self.parent().zero_timestamp + datetime.timedelta(milliseconds=x)).time().isoformat())
        self.position.setCoords(x, 0)
        self.parentPlot().replot()


class PtrLabelMain(PtrLabel):
    def __init__(self, parent: QCustomPlot, root: QWidget):
        super().__init__(parent, root)
        self.setBrush(iosc.const.BRUSH_PTR_MAIN)  # rect
        self.__slot_ptr_move(root.main_ptr_i)
        self._root.signal_ptr_moved_main.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, i: int):
        self._update_ptr(i)


class PtrLabelTmp(PtrLabel):
    _uid: int

    def __init__(self, parent: QCustomPlot, root: QWidget, uid: int):
        super().__init__(parent, root)
        self._uid = uid
        self.setBrush(iosc.const.BRUSH_PTR_TMP)  # rect
        self.__slot_ptr_move(uid, root.tmp_ptr_i[uid])
        self._root.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, uid: int, i: int):
        if uid == self._uid:
            self._update_ptr(i)


class TimeStampsPlot(OneBarPlot):
    """:todo: join TimeAxisPlot"""
    # __root: QWidget
    __zero_ptr_label: QCPItemText
    __main_ptr_label: PtrLabelMain
    _tmp_ptr: dict[int, PtrLabelTmp]

    def __init__(self, parent: 'TimeStampsBar'):
        super().__init__(parent)
        self.xAxis.setTickLabels(False)
        # self.xAxis.setTicks(False)
        self.__set_zero()
        # self.__main_ptr_label = PtrLabelMain(self, root)
        # self._tmp_ptr = dict()
        # self.__root.signal_ptr_add_tmp.connect(self._slot_ptr_add_tmp)
        # self.__root.signal_ptr_del_tmp.connect(self._slot_ptr_del_tmp)

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
        self._tmp_ptr[uid] = PtrLabelTmp(self, self.__root, uid)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr"""
        self.removeItem(self._tmp_ptr[uid])
        del self._tmp_ptr[uid]
        self.replot()
