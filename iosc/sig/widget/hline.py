from typing import Union

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QFrame


class HLine(QFrame):
    __parent: Union['BarCtrlWidget', 'BarPlotWidget']

    def __init__(self, parent: Union['BarCtrlWidget', 'BarPlotWidget']):
        super().__init__()
        self.__parent = parent
        self.setGeometry(QRect(0, 0, 0, 0))  # size is not the matter
        self.setFrameShape(QFrame.HLine)
        self.setCursor(Qt.SplitVCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        """accepted() == True, y() = Δy."""
        (b := self.__parent.bar).table.setRowHeight(b.row, b.table.rowHeight(b.row) + event.y())
