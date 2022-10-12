from PyQt5.QtCore import Qt, QMargins, QPointF
from PyQt5.QtGui import QBrush, QColor, QFont, QMouseEvent, QCursor
from PyQt5.QtWidgets import QWidget, QInputDialog
from QCustomPlot2 import QCPItemTracer, QCustomPlot, QCPItemStraightLine, QCPItemText, QCPItemRect
# 4. local
import iosc.const


class Ptr(QCPItemTracer):
    __cursor: QCursor
    _root: QWidget

    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp)
        self._root = root
        self.setGraph(cp.graph())
        self.position.setAxes(cp.xAxis, None)
        self.selectionChanged.connect(self.__sel_chg)

    def __sel_chg(self, selected: bool):
        if selected:
            self.__cursor = self._root.cursor()
            cur = iosc.const.PTR_CURSOR
        else:
            cur = self.__cursor
        self._root.setCursor(cur)


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
    class _PRPtr(QCPItemStraightLine):
        """OMP PR (previous state) pointer"""

        def __init__(self, cp: QCustomPlot):
            super().__init__(cp)
            self.setPen(iosc.const.OMP_PTR_PEN)

        def move2x(self, x: float):
            self.point1.setCoords(x, 0)
            self.point2.setCoords(x, 1)

    __pr_ptr: _PRPtr
    __x_limit: tuple[float, float]

    """OMP SC (Short Circuit) pointer."""
    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp, root)
        self.setPen(iosc.const.OMP_PTR_PEN)
        self.__pr_ptr = self._PRPtr(cp)
        self.__set_limits()
        self._root.signal_sc_ptr_moved.connect(self.__slot_sc_ptr_moved)

    def __set_limits(self):
        """Set limits for moves"""
        i_z = self._root.x2i(0.0)
        self.__x_limit = (
            self._root.i2x(i_z + 1),
            self._root.i2x(i_z + self._root.omp_width * self._root.tpp - 1)
        )

    @property
    def i(self) -> int:
        """Index of value in current self position"""
        return self._root.x2i(self.position.key())

    def __slot_sc_ptr_moved(self):
        if not self.selected():  # check is not myself
            self.setGraphKey(self._root.sc_ptr_x)
        self.__pr_ptr.move2x(self._root.i2x(self._root.sc_ptr_i - self._root.omp_width * self._root.tpp))
        self.parentPlot().replot()

    def mousePressEvent(self, event: QMouseEvent, _):
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
        :note: self.mouseMoveEvent() unusable because points to click position
        """
        if not self.selected():  # protection against 2click
            event.ignore()
            return
        event.accept()
        x_ms: float = self.parentPlot().xAxis.pixelToCoord(event.pos().x())  # ms, realative to z-point
        if not (self.__x_limit[0] <= x_ms <= self.__x_limit[1]):
            return
        i_old: int = self.i
        self.setGraphKey(x_ms)
        self.updatePosition()  # mandatory
        if i_old != (i_new := self.i):
            self._root.slot_sc_ptr_moved_i(i_new)  # replot after PR moving

    def mouseDoubleClickEvent(self, event: QMouseEvent, _):
        event.accept()
        new_omp_width, ok = QInputDialog.getInt(
            self._root,
            "Distance between PR and SC",
            "Main frequency periods number",
            self._root.omp_width,
            1,
            10
        )
        if ok and new_omp_width != self._root.omp_width:
            self._root.omp_width = new_omp_width
