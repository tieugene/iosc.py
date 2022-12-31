"""Horizontal line (bar resize anchor)."""
# 1. std
from typing import Union
# 2. 3rd
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QFrame


class HLine(QFrame):
    """Horizontal line for bar Y-resize."""

    __parent: Union['BarCtrlWidget', 'BarPlotWidget']  # noqa: F821

    def __init__(self, parent: Union['BarCtrlWidget', 'BarPlotWidget']):  # noqa: F821
        """Init HLine object."""
        super().__init__()
        self.__parent = parent
        self.setGeometry(QRect(0, 0, 0, 0))  # size is not the matter
        self.setFrameShape(QFrame.HLine)
        self.setCursor(Qt.SplitVCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Inherited.

        accepted() == True, y() = Δy.
        """
        (b := self.__parent.bar).table.setRowHeight(b.row, b.table.rowHeight(b.row) + event.y())
