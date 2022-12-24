# 2. 3rd
from PyQt5.QtCore import QMargins, Qt, pyqtSignal
from PyQt5.QtGui import QResizeEvent
from QCustomPlot_PyQt5 import QCPItemText, QCPAxis, QCPAxisTickerFixed
# 3. local
import iosc.const
from iosc.sig.widget.common import OneBarPlot


class PtrLabel(QCPItemText):
    _oscwin: 'ComtradeWidget'

    def __init__(self, parent: 'TimeAxisPlot'):
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
        """Repaint/__move main ptr value label (%.2f)
        :fixme: draw in front of ticks
        """
        x = self._oscwin.i2x(i)
        self.setText(self._mk_text(x))
        self.position.setCoords(x, 0)
        self.parentPlot().replot()


class PtrLabelMain(PtrLabel):
    def __init__(self, parent: 'TimeAxisPlot'):
        super().__init__(parent)
        self.setBrush(iosc.const.BRUSH_PTR_MAIN)  # rect
        self.__slot_ptr_move(self._oscwin.main_ptr_i)
        self._oscwin.signal_ptr_moved_main.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, i: int):
        self._update_ptr(i)


class PtrLabelTmp(PtrLabel):
    _uid: int
    _name: str

    def __init__(self, parent: 'TimeAxisPlot', uid: int):
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
        return self._name

    @name.setter
    def name(self, s: str):
        self._name = s

    def __slot_ptr_move(self, uid: int, i: int):
        if uid == self._uid:
            self._update_ptr(i)


class TimeAxisPlot(OneBarPlot):
    __main_ptr_label: PtrLabelMain
    _tmp_ptr: dict[int, PtrLabelTmp]
    signal_width_changed = pyqtSignal(int)

    def __init__(self, parent: 'TopBar'):
        super().__init__(parent)
        self.__main_ptr_label = PtrLabelMain(self)
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
        super().resizeEvent(event)
        if event.oldSize().width() != (w := event.size().width()):
            self.signal_width_changed.emit(w)

    def __slot_retick(self):
        self.xAxis.ticker().setTickStep(iosc.const.X_PX_WIDTH_uS[self._oscwin.x_zoom] / 10)
        self.replot()

    def get_tmp_ptr_name(self, uid: id):
        return self._tmp_ptr[uid].name

    def set_tmp_ptr_name(self, uid: id, name: str):
        self._tmp_ptr[uid].name = name

    def _slot_ptr_add_tmp(self, uid: int):
        """Add new TmpPtr"""
        self._tmp_ptr[uid] = PtrLabelTmp(self, uid)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr"""
        self.removeItem(self._tmp_ptr[uid])
        del self._tmp_ptr[uid]
        self.replot()
