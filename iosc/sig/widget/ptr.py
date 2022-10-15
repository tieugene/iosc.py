from typing import Optional

from PyQt5.QtCore import Qt, QMargins, QPointF, pyqtSignal, QPoint
from PyQt5.QtGui import QBrush, QColor, QFont, QMouseEvent, QCursor
from PyQt5.QtWidgets import QWidget, QInputDialog, QMenu
from QCustomPlot2 import QCPItemTracer, QCustomPlot, QCPItemStraightLine, QCPItemText, QCPItemRect
# 4. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.dialog import get_new_omp_width, TmpPtrDialog, MsrPtrDialog


class VLine(QCPItemStraightLine):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)

    def move2x(self, x: float):
        """
        :param x:
        :note: for  QCPItemLine: s/point1/start/, s/point2/end/
        """
        self.point1.setCoords(x, 0)
        self.point2.setCoords(x, 1)

    @property
    def x(self):
        return self.point1.coords().x()


class Ptr(QCPItemTracer):
    __cursor: QCursor
    _root: QWidget
    signal_ptr_moved = pyqtSignal(int)
    signal_rmb_clicked = pyqtSignal(QPointF)

    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp)
        self._root = root
        self.setGraph(cp.graph())
        self.position.setAxes(cp.xAxis, None)

    def mousePressEvent(self, event: QMouseEvent, _):
        if event.button() == Qt.LeftButton:
            event.accept()
            self.selection = True
        elif event.button() == Qt.RightButton:
            event.accept()  # for signal_rmb_clicked
        else:
            event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent, _):
        if event.button() == Qt.LeftButton:
            if self.selection:
                event.accept()
                self.selection = False
        elif event.button() == Qt.RightButton:
            self.signal_rmb_clicked.emit(event.pos())
        else:
            event.ignore()

    @property
    def selection(self) -> bool:
        return self.selected()

    @selection.setter
    def selection(self, val: bool):
        self.setSelected(val)
        self.parent().ptr_selected = val

    @property
    def x(self) -> float:
        """Current x-position (ms)"""
        return self.position.key()

    @property
    def i(self) -> int:
        """Index of value in current self position"""
        return self._root.x2i(self.x)

    def _switch_cursor(self, selected: bool):
        if selected:
            self.__cursor = self._root.cursor()
            cur = iosc.const.CURSOR_PTR
        else:
            cur = self.__cursor
        self._root.setCursor(cur)

    def _mouse2ms(self, event: QMouseEvent) -> float:
        """Get mouse position as ms"""
        return self.parentPlot().xAxis.pixelToCoord(event.pos().x())  # ms, realative to z-point


class SCPtr(Ptr):
    """OMP SC (Short Circuit) pointer."""
    __pr_ptr: VLine
    __x_limit: tuple[float, float]

    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp, root)
        self.setPen(iosc.const.PEN_PTR_OMP)
        self.__pr_ptr = VLine(cp)
        self.__pr_ptr.setPen(iosc.const.PEN_PTR_OMP)
        self.__set_limits()
        self.selectionChanged.connect(self.__selection_chg)
        self.signal_ptr_moved.connect(self._root.slot_ptr_moved_sc)
        self._root.signal_ptr_moved_sc.connect(self.__slot_ptr_move)

    def __set_limits(self):
        """Set limits for moves"""
        i_z = self._root.x2i(0.0)
        self.__x_limit = (
            self._root.i2x(i_z + 1),
            self._root.i2x(i_z + self._root.omp_width * self._root.tpp - 1)
        )

    def __selection_chg(self, selection: bool):
        self._switch_cursor(selection)
        self.parentPlot().replot()  # update selection decoration

    def __slot_ptr_move(self, i: int):
        if not self.selected():  # check is not myself
            self.setGraphKey(self._root.i2x(i))
        self.__pr_ptr.move2x(self._root.i2x(i - self._root.omp_width * self._root.tpp))
        self.parentPlot().replot()

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
        x_ms: float = self._mouse2ms(event)  # ms, realative to z-point
        # TODO: convert to index then do the job
        if not (self.__x_limit[0] <= x_ms <= self.__x_limit[1]):
            return
        i_old: int = self.i
        self.setGraphKey(x_ms)
        self.updatePosition()  # mandatory
        if i_old != (i_new := self.i):
            self.signal_ptr_moved.emit(i_new)  # replot will be after PR moving

    def mouseDoubleClickEvent(self, event: QMouseEvent, _):
        event.accept()
        if new_omp_width := get_new_omp_width(self._root, self._root.omp_width):
            self._root.omp_width = new_omp_width


class _PowerPtr(Ptr):
    """Pointer with tip and rectangle"""
    class _Tip(QCPItemText):
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

    class _Rect(QCPItemRect):
        def __init__(self, cp: QCustomPlot):
            super().__init__(cp)
            self.setPen(QColor(255, 170, 0, 128))
            self.setBrush(QColor(255, 170, 0, 128))

        def set2x(self, x: float):
            """Set starting point"""
            yaxis = self.parentPlot().yAxis
            self.topLeft.setCoords(x, yaxis.pixelToCoord(0) - yaxis.pixelToCoord(iosc.const.RECT_PTR_HEIGHT))

        def stretc2x(self, x: float):
            self.bottomRight.setCoords(x, 0)

    __old_pos: VLine
    __rect: _Rect
    __tip: _Tip

    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp, root)
        self.__old_pos = VLine(cp)
        self.__old_pos.setPen(iosc.const.PEN_PTR_OLD)
        self.__rect = self._Rect(cp)
        self.__tip = self._Tip(cp)
        self.__switch_tips(False)
        self.selectionChanged.connect(self.__selection_chg)

    def __switch_tips(self, todo: bool):
        # print(("Off", "On")[int(todo)])
        self.__old_pos.setVisible(todo)
        self.__tip.setVisible(todo)
        self.__rect.setVisible(todo)

    def __selection_chg(self, selection: bool):
        self._switch_cursor(selection)
        if selection:
            x = self.x
            self.__old_pos.move2x(x)
            self.__rect.set2x(x)
        else:
            self.__switch_tips(False)
        self.parentPlot().replot()  # selection update

    def _handle_mouse_move_event(self, event: QMouseEvent) -> Optional[int]:
        if not self.selected():  # protection against something
            event.ignore()
            return
        event.accept()
        x_ms: float = self._mouse2ms(event)
        # TODO: convert to index then do the job
        i_old: int = self.i
        self.setGraphKey(x_ms)
        self.updatePosition()  # mandatory
        if i_old != (i_new := self.i):
            if not self.__old_pos.visible():  # show tips on demand
                self.__switch_tips(True)
            self.__tip.move2x(x_ms, self.__old_pos.x)
            self.__rect.stretc2x(x_ms)
            self.parentPlot().replot()
            return i_new


class MainPtr(_PowerPtr):
    def __init__(self, cp: QCustomPlot, root: QWidget):
        super().__init__(cp, root)
        self.setPen(iosc.const.PEN_PTR_MAIN)
        self.signal_ptr_moved.connect(self._root.slot_ptr_moved_main)
        self._root.signal_ptr_moved_main.connect(self.__slot_ptr_move)

    def __slot_ptr_move(self, i: int):
        if not self.selected():  # check is not myself
            self.setGraphKey(self._root.i2x(i))
            self.parentPlot().replot()

    def mouseMoveEvent(self, event: QMouseEvent, pos: QPointF):
        """
        :param event:
        :param pos: Where mouse was pressed (looks like fixed)
        :note: self.mouseMoveEvent() unusable because points to click position
        """
        if (i_new := self._handle_mouse_move_event(event)) is not None:
            self.signal_ptr_moved.emit(i_new)


class TmpPtr(_PowerPtr):
    _uid: int
    signal_ptr_moved_tmp = pyqtSignal(int, int)
    # signal_ptr_del_tmp = pyqtSignal(int)
    signal_ptr_edit_tmp = pyqtSignal(int)

    def __init__(self, cp: QCustomPlot, root: QWidget, uid: int):
        super().__init__(cp, root)
        self._uid = uid
        self.setPen(iosc.const.PEN_PTR_TMP)
        self.signal_ptr_moved_tmp.connect(self._root.slot_ptr_moved_tmp)
        # self.signal_ptr_del_tmp.connect(self._root.slot_ptr_del_tmp)
        self.signal_ptr_edit_tmp.connect(self._root.slot_ptr_edit_tmp)
        self._root.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)
        self.signal_rmb_clicked.connect(self.__slot_context_menu)

    def __slot_ptr_move(self, uid: int, i: int):
        if not self.selected() and uid == self._uid:  # check is not myself and myself
            self.setGraphKey(self._root.i2x(i))
            self.parentPlot().replot()

    def mouseMoveEvent(self, event: QMouseEvent, pos: QPointF):
        """
        :param event:
        :param pos: Where mouse was pressed (looks like fixed)
        :note: self.mouseMoveEvent() unusable because points to click position
        """
        if (i_new := self._handle_mouse_move_event(event)) is not None:
            self.signal_ptr_moved_tmp.emit(self._uid, i_new)

    def __slot_context_menu(self, pos: QPointF):
        context_menu = QMenu()
        action_edit = context_menu.addAction("Edit...")
        action_del = context_menu.addAction("Delete")
        point = self.parentPlot().mapToGlobal(pos.toPoint())
        chosen_action = context_menu.exec_(point)
        if chosen_action == action_edit:
            self.signal_ptr_edit_tmp.emit(self._uid)
        elif chosen_action == action_del:
            self._root.slot_ptr_del_tmp(self._uid)
            # self.signal_ptr_del_tmp.emit(self._uid)


class MsrPtr(Ptr):

    class _Tip(QCPItemText):
        def __init__(self, cp: QCustomPlot):
            super().__init__(cp)
            self.setFont(QFont('mono', 8))
            self.setPadding(QMargins(2, 2, 2, 2))
            self.setTextAlignment(Qt.AlignCenter)
            self.setColor(Qt.white)  # text
            self.setPositionAlignment(Qt.AlignLeft | Qt.AlignBottom)
            self.setBrush(QBrush(Qt.black))  # rect

    FUNC_ABBR = ("I", "M", "E", "H1", "H2", "H3", "H5")
    _uid: int  # uniq id of xMsrPtr
    _signal: mycomtrade.AnalogSignal
    _func_i: int  # value mode (function) number (in sigfunc.func_list[])
    _tip: _Tip
    signal_ptr_del_msr = pyqtSignal(int)

    def __init__(self, cp: QCustomPlot, root: QWidget, signal: mycomtrade.AnalogSignal, uid: int):
        super().__init__(cp, root)
        self._uid = uid
        self._signal = signal
        self._func_i = root.viewas
        self._tip = self._Tip(cp)
        self.setPen(iosc.const.PEN_PTR_MSR)  # FIXME:
        self.setGraphKey(self._root.main_ptr_x)
        self.updatePosition()
        self._move_tip()
        self.selectionChanged.connect(self.__selection_chg)
        self.signal_rmb_clicked.connect(self.__slot_context_menu)

    def __selection_chg(self, selection: bool):
        self._switch_cursor(selection)
        self.parentPlot().replot()  # update selection decoration

    def _update_text(self):
        v = self._root.sig2str(self._signal, self.i, self._func_i)  # was self.position.value()
        m = self.FUNC_ABBR[self._func_i]
        self._tip.setText("M%d: %s (%s)" % (self._uid, v, m))

    def _move_tip(self):
        self._tip.position.setCoords(self.x, 0)  # FIXME: y = top
        self._update_text()
        self.parentPlot().replot()

    def mouseMoveEvent(self, event: QMouseEvent, _):
        event.accept()
        x_ms: float = self._mouse2ms(event)
        i_old: int = self.i
        self.setGraphKey(x_ms)
        self.updatePosition()  # mandatory
        if i_old != self.i:
            self._move_tip()

    def __slot_context_menu(self, pos: QPointF):
        context_menu = QMenu()
        action_edit = context_menu.addAction("Edit...")
        action_del = context_menu.addAction("Delete")
        point = self.parentPlot().mapToGlobal(pos.toPoint())
        chosen_action = context_menu.exec_(point)
        if chosen_action == action_edit:
            self._edit_self()
        elif chosen_action == action_del:
            self._del_self()

    def _del_self(self):
        self._root.slot_ptr_del_msr(self._uid)
        self.parentPlot().removeItem(self._tip)
        self.parentPlot().slot_ptr_del_msr(self)  # dirty hack

    def _edit_self(self):
        v = self.x
        v_min = self._root.i2x(0)
        v_max = self._root.i2x(self._root.i_max)
        v_step = 1  # TODO: calc
        form = MsrPtrDialog((v, v_min, v_max, v_step))
        if form.exec_():
            ...
