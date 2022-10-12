from PyQt5.QtCore import Qt, QMargins, QPointF
from PyQt5.QtGui import QBrush, QColor, QFont, QMouseEvent
from PyQt5.QtWidgets import QWidget
from QCustomPlot2 import QCPItemTracer, QCustomPlot, QCPItemStraightLine, QCPItemText, QCPItemRect
# 4. local
import iosc.const


class Ptr(QCPItemTracer):
    _root: QWidget

    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp)
        self._root = root
        self.setGraph(cp.graph())
        self.position.setAxes(cp.xAxis, None)
        # cp.setCursor(QCursor(Qt.CrossCursor))


class MainPtr(Ptr):
    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp, root)
        self.setPen(iosc.const.MAIN_PTR_PEN)


class OldPtr(QCPItemStraightLine):
    __x: float

    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setPen(iosc.const.OLD_PTR_PEN)
        self.setVisible(False)

    def move2x(self, x: float):
        """
        :param x:
        :note: for  QCPItemLine: s/point1/start/, s/point2/end/
        """
        self.__x = x
        self.point1.setCoords(x, 0)
        self.point2.setCoords(x, 1)

    @property
    def x(self):
        return self.__x


class MainPtrTip(QCPItemText):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setColor(Qt.black)  # text
        self.setPen(Qt.red)
        self.setBrush(QBrush(QColor(255, 170, 0)))  # rect
        self.setTextAlignment(Qt.AlignCenter)
        self.setFont(QFont('mono', 8))
        self.setPadding(QMargins(2, 2, 2, 2))

    def move2x(self, x: float, x_old: float):
        dx = x - x_old
        self.setPositionAlignment((Qt.AlignLeft if dx > 0 else Qt.AlignRight) | Qt.AlignBottom)
        self.position.setCoords(x, 0)
        self.setText("%.2f" % dx)


class MainPtrRect(QCPItemRect):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setPen(QColor(255, 170, 0, 128))
        self.setBrush(QColor(255, 170, 0, 128))

    def set2x(self, x: float):
        """Set starting point"""
        yaxis = self.parentPlot().yAxis
        self.topLeft.setCoords(x, yaxis.pixelToCoord(0) - yaxis.pixelToCoord(iosc.const.PTR_RECT_HEIGHT))

    def stretc2x(self, x: float):
        self.bottomRight.setCoords(x, 0)


class SCPtr(Ptr):
    """OMP SC (Short Circuit) pointer.
    :note: self.mouseMoveEvent() unusable because points to click position
    """
    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp, root)
        self.setPen(iosc.const.OMP_PTR_PEN)
        self._root.signal_sc_ptr_moved.connect(self.__slot_sc_ptr_moved)

    def mousePressEvent(self, event: QMouseEvent, details):
        event.accept()
        self.setSelected(True)

    def mouseReleaseEvent(self, event: QMouseEvent, pos: QPointF):
        event.accept()
        self.setSelected(False)
        self.parentPlot().replot()  # update selection decoration

    def mouseMoveEvent(self, event: QMouseEvent, pos: QPointF):
        """
        :param event:
        :param pos: Where mouse was pressed (looks like fixed)
        """
        event.accept()
        x_px: int = event.pos().x()  # 710x - px, relative to QCP width
        x_ms: float = self.parentPlot().xAxis.pixelToCoord(x_px)  # ms, realtive to z-point
        x_old_ms: float = self.position.key()  # ms, current postition (was x_dst_0)
        self.setGraphKey(x_ms)
        self.updatePosition()  # mandatory
        x_new_ms: float = self.position.key()  # ms, new position (was x_dst)
        if x_old_ms != x_new_ms:  # FIXME: cmp value indexes
            self.parentPlot().replot()
            self._root.slot_sc_ptr_moved_x(x_new_ms)

    def __slot_sc_ptr_moved(self):
        if not self.selected():  # check is not myself
            self.setGraphKey(self._root.sc_ptr_x)
            self.parentPlot().replot()
