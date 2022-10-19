import datetime
# 2. 3rd
from PyQt5.QtCore import QMargins, Qt
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCustomPlot, QCPItemText
# 4. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.common import CleanScrollArea


class PtrLabel(QCPItemText):
    _root: QWidget

    def __init__(self, parent: QCustomPlot, root: QWidget):
        super().__init__(parent)
        self._root = root
        self.setTextAlignment(Qt.AlignCenter)
        self.setPadding(QMargins(2, 2, 2, 2))
        self.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)
        self.setFont(iosc.const.FONT_X)
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


class StatusBarWidget(QCustomPlot):
    """:todo: join TimeAxisWidget"""
    __root: QWidget
    zero_timestamp: datetime.datetime
    __zero_ptr_label: QCPItemText
    __main_ptr_label: PtrLabelMain
    _tmp_ptr: dict[int, PtrLabelTmp]

    def __init__(self, osc: mycomtrade.MyComtrade, root: QWidget, parent: CleanScrollArea):
        super().__init__(parent)
        self.__root = root
        self.zero_timestamp = osc.raw.cfg.trigger_timestamp
        self.__zero_ptr_label = QCPItemText(self)
        self.__main_ptr_label = PtrLabelMain(self, root)
        self._tmp_ptr = dict()
        t0 = osc.raw.trigger_time
        self.xAxis.setRange((osc.raw.time[0] - t0) * 1000, (osc.raw.time[-1] - t0) * 1000)
        self.__squeeze()
        self.__set_style()
        self.__zero_ptr_label.setText(self.zero_timestamp.time().isoformat())
        self.__root.signal_xscale.connect(self._slot_chg_width)
        self.__root.signal_ptr_add_tmp.connect(self._slot_ptr_add_tmp)
        self.__root.signal_ptr_del_tmp.connect(self._slot_ptr_del_tmp)

    def __squeeze(self):
        ar = self.axisRect(0)
        ar.setMinimumMargins(QMargins())
        ar.removeAxis(self.yAxis)
        ar.removeAxis(self.yAxis2)
        ar.removeAxis(self.xAxis2)
        self.xAxis.setTickLabels(False)
        self.xAxis.setTicks(False)
        self.xAxis.grid().setVisible(False)
        self.xAxis.setPadding(0)
        self.setFixedHeight(iosc.const.XSCALE_HEIGHT)

    def __set_style(self):
        # zero
        self.__zero_ptr_label.setColor(iosc.const.COLOR_LABEL_Z)  # text
        self.__zero_ptr_label.setTextAlignment(Qt.AlignCenter)
        self.__zero_ptr_label.setFont(iosc.const.FONT_X)
        self.__zero_ptr_label.setPadding(QMargins(2, 2, 2, 2))
        self.__zero_ptr_label.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)

    def _slot_chg_width(self, _: int, w_new: int):  # dafault: 1117
        self.setFixedWidth(w_new)

    def _slot_ptr_add_tmp(self, uid: int):
        """Add new TmpPtr"""
        self._tmp_ptr[uid] = PtrLabelTmp(self, self.__root, uid)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr"""
        self.removeItem(self._tmp_ptr[uid])
        del self._tmp_ptr[uid]
        self.replot()
