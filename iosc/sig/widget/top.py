from PyQt5.QtCore import QMargins, Qt
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCustomPlot, QCPItemText, QCPAxis

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


class PtrLabelMain(PtrLabel):
    def __init__(self, parent: QCustomPlot, root: QWidget):
        super().__init__(parent, root)
        self.setBrush(iosc.const.BRUSH_PTR_MAIN)  # rect
        self._root.signal_ptr_moved_main.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, i: int):
        """Repaint/move main ptr value label (%.2f)
        :fixme: draw in front of ticks
        """
        x = self._root.i2x(i)
        self.setText("%.2f" % x)
        self.position.setCoords(x, 0)
        self.parentPlot().replot()


class PtrLabelTmp(PtrLabel):
    _uid: int

    def __init__(self, parent: QCustomPlot, root: QWidget, uid: int):
        super().__init__(parent, root)
        self._uid = uid
        self.setBrush(iosc.const.BRUSH_PTR_TMP)  # rect
        self._root.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, uid: int, i: int):
        """Repaint/move main ptr value label (%.2f)
        :fixme: draw in front of ticks
        """
        if uid == self._uid:
            x = self._root.i2x(i)
            self.setText("%.2f" % x)
            self.position.setCoords(x, 0)
            self.parent().replot()


class TimeAxisWidget(QCustomPlot):
    __root: QWidget
    __main_ptr_label: PtrLabelMain
    _tmp_ptr: dict[int, PtrLabelTmp]

    def __init__(self, osc: mycomtrade.MyComtrade, root: QWidget, parent: CleanScrollArea):
        super().__init__(parent)
        self.__root = root
        self.__main_ptr_label = PtrLabelMain(self, root)
        self._tmp_ptr = dict()
        t0 = osc.raw.trigger_time
        self.xAxis.setRange((osc.raw.time[0] - t0) * 1000, (osc.raw.time[-1] - t0) * 1000)
        self.__squeeze()
        self.__set_style()
        self.__root.signal_xscale.connect(self._slot_chg_width)
        self.__root.signal_ptr_add_tmp.connect(self._slot_ptr_add_tmp)
        self.__root.signal_ptr_del_tmp.connect(self._slot_ptr_del_tmp)

    def __squeeze(self):
        ar = self.axisRect(0)
        ar.setMinimumMargins(QMargins())  # the best
        ar.removeAxis(self.yAxis)
        ar.removeAxis(self.yAxis2)
        ar.removeAxis(self.xAxis2)
        # -xaxis.setTickLabels(False)
        # -xaxis.setTicks(False)
        self.xAxis.setTickLabelSide(QCPAxis.lsInside)
        self.xAxis.grid().setVisible(False)
        self.xAxis.setPadding(0)
        self.setFixedHeight(iosc.const.XSCALE_HEIGHT)

    def __set_style(self):
        # TODO: setLabelFormat("%d")
        self.xAxis.setTickLabelFont(iosc.const.FONT_X)

    def _slot_chg_width(self, _: int, w_new: int):  # dafault: 1117
        self.setFixedWidth(w_new)
        self.xAxis.ticker().setTickCount(iosc.const.TICK_COUNT * self.__root.xzoom)
        self.replot()

    def _slot_ptr_add_tmp(self, uid: int):
        """Add new TmpPtr"""
        self._tmp_ptr[uid] = PtrLabelTmp(self, self.__root, uid)

    def _slot_ptr_del_tmp(self, uid: int):
        """Del TmpPtr"""
        del self._tmp_ptr[uid]
