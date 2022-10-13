import datetime

from PyQt5.QtCore import QMargins, Qt
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCustomPlot, QCPItemText

import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.common import CleanScrollArea


class StatusBarWidget(QCustomPlot):
    """:todo: join TimeAxisWidget"""
    __root: QWidget
    __zero_timestamp: datetime.datetime
    __zero_ptr_label: QCPItemText
    __main_ptr_label: QCPItemText

    def __init__(self, osc: mycomtrade.MyComtrade, root: QWidget, parent: CleanScrollArea):
        super().__init__(parent)
        self.__root = root
        self.__zero_timestamp = osc.raw.cfg.trigger_timestamp
        self.__zero_ptr_label = QCPItemText(self)
        self.__main_ptr_label = QCPItemText(self)
        t0 = osc.raw.trigger_time
        self.xAxis.setRange((osc.raw.time[0] - t0) * 1000, (osc.raw.time[-1] - t0) * 1000)
        self.__squeeze()
        self.__set_style()
        self.__zero_ptr_label.setText(self.__zero_timestamp.time().isoformat())
        self.__slot_main_ptr_moved(root.main_ptr_i)
        self.__root.signal_ptr_moved_main.connect(self.__slot_main_ptr_moved)
        self.__root.signal_xscale.connect(self._slot_chg_width)

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
        # main_ptr_i
        self.__main_ptr_label.setColor(iosc.const.COLOR_LABEL_X)  # text
        self.__main_ptr_label.setBrush(iosc.const.BRUSH_PTR_MAIN)  # rect
        self.__main_ptr_label.setTextAlignment(Qt.AlignCenter)
        self.__main_ptr_label.setFont(iosc.const.FONT_X)
        self.__main_ptr_label.setPadding(QMargins(2, 2, 2, 2))
        self.__main_ptr_label.setPositionAlignment(Qt.AlignHCenter)  # | Qt.AlignTop (default)

    def __slot_main_ptr_moved(self, i: int):
        """Repaint/move main ptr value label"""
        x = self.__root.i2x(i)  # from z-point, ms
        self.__main_ptr_label.setText((self.__zero_timestamp + datetime.timedelta(milliseconds=x)).time().isoformat())
        self.__main_ptr_label.position.setCoords(x, 0)
        self.replot()

    def _slot_chg_width(self, _: int, w_new: int):  # dafault: 1117
        self.setFixedWidth(w_new)
