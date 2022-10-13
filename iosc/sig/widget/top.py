from PyQt5.QtCore import QMargins, Qt
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCustomPlot, QCPItemText, QCPAxis

import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.common import CleanScrollArea


class TimeAxisWidget(QCustomPlot):
    __root: QWidget
    __main_ptr_label: QCPItemText

    def __init__(self, osc: mycomtrade.MyComtrade, root: QWidget, parent: CleanScrollArea):
        super().__init__(parent)
        self.__root = root
        self.__main_ptr_label = QCPItemText(self)
        t0 = osc.raw.trigger_time
        self.xAxis.setRange((osc.raw.time[0] - t0) * 1000, (osc.raw.time[-1] - t0) * 1000)
        self.__squeeze()
        self.__set_style()
        self.__slot_main_ptr_moved()
        self.__root.signal_ptr_moved_main.connect(self.__slot_main_ptr_moved)
        self.__root.signal_xscale.connect(self._slot_chg_width)

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
        self.xAxis.setTickLabelFont(iosc.const.X_FONT)
        self.__main_ptr_label.setColor(iosc.const.X_LABEL_COLOR)  # text
        self.__main_ptr_label.setBrush(iosc.const.X_LABEL_BRUSH)  # rect
        self.__main_ptr_label.setTextAlignment(Qt.AlignCenter)
        self.__main_ptr_label.setFont(iosc.const.X_FONT)
        self.__main_ptr_label.setPadding(QMargins(2, 2, 2, 2))
        self.__main_ptr_label.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)

    def __slot_main_ptr_moved(self):
        """Repaint/move main ptr value label (%.2f)
        :fixme: draw in front of ticks
        """
        x = self.__root.main_ptr_x
        self.__main_ptr_label.setText("%.2f" % x)
        self.__main_ptr_label.position.setCoords(x, 0)
        self.replot()

    def _slot_chg_width(self, _: int, w_new: int):  # dafault: 1117
        self.setFixedWidth(w_new)
        self.xAxis.ticker().setTickCount(iosc.const.TICK_COUNT * self.__root.xzoom)
        self.replot()
