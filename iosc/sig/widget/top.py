from PyQt5.QtCore import QMargins, Qt, pyqtSignal
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCustomPlot, QCPItemText, QCPAxis, QCPAxisTickerFixed

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

    def _mk_text(self, x: float):
        return "%.2f" % x

    def _update_ptr(self, i: int):
        """Repaint/__move main ptr value label (%.2f)
        :fixme: draw in front of ticks
        """
        x = self._root.i2x(i)
        self.setText(self._mk_text(x))
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
    _name: str

    def __init__(self, parent: QCustomPlot, root: QWidget, uid: int):
        super().__init__(parent, root)
        self._uid = uid
        self._name = ''
        self.setBrush(iosc.const.BRUSH_PTR_TMP)  # rect
        self.__slot_ptr_move(uid, root.tmp_ptr_i[uid])
        self._root.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)

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
    signal_width_changed = pyqtSignal(int)

    def __init__(self, parent: 'TopBar'):
        super().__init__(parent)
        # self.xAxis.setTickLabels(True)  # default
        # self.xAxis.setTicks(True)  # default
        self.xAxis.setTickLabelSide(QCPAxis.lsInside)
        self.xAxis.setTicker(QCPAxisTickerFixed())
        self.xAxis.setTickLabelFont(iosc.const.FONT_TOPBAR)
        self.__slot_retick()
        self._oscwin.signal_x_zoom.connect(self.__slot_retick)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if event.oldSize().width() != (w := event.size().width()):
            self.signal_width_changed.emit(w)

    def __slot_retick(self):
        self.xAxis.ticker().setTickStep(iosc.const.X_PX_WIDTH_uS[self._oscwin.x_zoom] / 10)
        self.replot()
