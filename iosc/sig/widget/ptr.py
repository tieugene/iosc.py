from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import Qt, QMargins, QPointF, pyqtSignal, QObject
from PyQt5.QtGui import QBrush, QColor, QFont, QMouseEvent, QCursor, QPen
from PyQt5.QtWidgets import QWidget, QMenu
from QCustomPlot2 import QCPItemTracer, QCustomPlot, QCPItemStraightLine, QCPItemText, QCPItemRect, QCPGraph
# 4. local
import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.dialog import get_new_omp_width, MsrPtrDialog, LvlPtrDialog


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

    def __init__(self, graph: QCPGraph, root: QWidget):
        super().__init__(graph.parentPlot())
        self._root = root
        self.setGraph(graph)
        self.position.setAxes(graph.parentPlot().xAxis, None)

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
        self.parentPlot().ptr_selected = val

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

    def __init__(self, graph: QCPGraph, root: QWidget):
        super().__init__(graph, root)
        self.setPen(iosc.const.PEN_PTR_OMP)
        self.__pr_ptr = VLine(graph.parentPlot())
        self.__pr_ptr.setPen(iosc.const.PEN_PTR_OMP)
        self.__set_limits()
        self.__slot_ptr_move(self._root.sc_ptr_i, False)
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

    def __slot_ptr_move(self, i: int, replot: bool = True):
        if not self.selected():  # check is not myself
            self.setGraphKey(self._root.i2x(i))
        self.__pr_ptr.move2x(self._root.i2x(i - self._root.omp_width * self._root.tpp))
        if replot:
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


class _TipBase(QCPItemText):
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setFont(QFont('mono', 8))
        self.setPadding(QMargins(2, 2, 2, 2))
        self.setTextAlignment(Qt.AlignCenter)


class _PowerPtr(Ptr):
    """Pointer with tip and rectangle"""
    class _Tip(_TipBase):
        def __init__(self, cp: QCustomPlot):
            super().__init__(cp)
            self.setColor(Qt.black)  # text
            self.setPen(Qt.red)
            self.setBrush(QBrush(QColor(255, 170, 0)))  # rect

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

    def __init__(self, graph: QCPGraph, root: QWidget):
        super().__init__(graph, root)
        self.__old_pos = VLine(graph.parentPlot())
        self.__old_pos.setPen(iosc.const.PEN_PTR_OLD)
        self.__rect = self._Rect(graph.parentPlot())
        self.__tip = self._Tip(graph.parentPlot())
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
    def __init__(self, graph: QCPGraph, root: QWidget):
        super().__init__(graph, root)
        self.setPen(iosc.const.PEN_PTR_MAIN)
        self.slot_ptr_move(self._root.main_ptr_i, False)
        self.signal_ptr_moved.connect(self._root.slot_ptr_moved_main)
        self._root.signal_ptr_moved_main.connect(self.slot_ptr_move)

    def slot_ptr_move(self, i: int, replot: bool = True):
        if not self.selected():  # check is not myself
            self.setGraphKey(self._root.i2x(i))
            if replot:
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

    def __init__(self, graph: QCPGraph, root: QWidget, uid: int):
        super().__init__(graph, root)
        self._uid = uid
        self.setPen(iosc.const.PEN_PTR_TMP)
        self.__slot_ptr_move(uid, self._root.tmp_ptr_i[uid], False)
        self.signal_ptr_moved_tmp.connect(self._root.slot_ptr_moved_tmp)
        # self.signal_ptr_del_tmp.connect(self._root.slot_ptr_del_tmp)
        self.signal_ptr_edit_tmp.connect(self._root.slot_ptr_edit_tmp)
        self._root.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)
        self.signal_rmb_clicked.connect(self.__slot_context_menu)

    def __slot_ptr_move(self, uid: int, i: int, replot: bool = True):
        if not self.selected() and uid == self._uid:  # check is not myself and myself
            self.setGraphKey(self._root.i2x(i))
            if replot:
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
            # self.signal_ptr_del_tmp.emit(self.__uid)


class MsrPtr(Ptr):
    @dataclass
    class State:
        uid: int
        i: int

    class _Tip(_TipBase):
        def __init__(self, cp: QCustomPlot):
            super().__init__(cp)
            self.setColor(Qt.white)  # text
            self.setPositionAlignment(Qt.AlignLeft | Qt.AlignBottom)

    FUNC_ABBR = ("I", "M", "E", "H1", "H2", "H3", "H5")
    __sigraph: QObject
    __uid: int  # uniq id
    __signal: mycomtrade.AnalogSignal
    __func_i: int  # value mode (function) number (in sigfunc.func_list[])
    __tip: _Tip
    signal_ptr_del_msr = pyqtSignal(int)

    def __init__(self, sigraph: QObject, root: QWidget, signal: mycomtrade.AnalogSignal, uid: int, i: int):
        super().__init__(sigraph.graph, root)
        self.__sigraph = sigraph
        self.__uid = uid
        self.__signal = signal
        self.__func_i = root.viewas
        self.__tip = self._Tip(self.graph().parentPlot())
        self.setGraphKey(root.i2x(i))
        self.updatePosition()
        self.__set_color()
        self.__move_tip()
        self._root.msr_ptr_uids.add(uid)
        self.selectionChanged.connect(self.__slot_selection_chg)
        self._root.signal_chged_shift.connect(self.__slot_update_text)
        self._root.signal_chged_pors.connect(self.__slot_update_text)
        self.signal_rmb_clicked.connect(self.__slot_context_menu)

    @property
    def uid(self) -> int:
        return self.__uid

    def __set_color(self):
        pen = QPen(iosc.const.PENSTYLE_PTR_MSR)
        color = QColor.fromRgb(*self.__signal.rgb)
        pen.setColor(color)
        self.setPen(pen)
        self.__tip.setBrush(QBrush(color))  # rect

    def __move_tip(self):
        self.__tip.position.setCoords(self.x, 0)  # FIXME: y = top
        self.__slot_update_text()

    def __slot_selection_chg(self, selection: bool):
        self._switch_cursor(selection)
        self.parentPlot().replot()  # update selection decoration

    def __slot_update_text(self):
        v = self._root.sig2str_i(self.__signal, self.i, self.__func_i)  # was self.position.value()
        m = self.FUNC_ABBR[self.__func_i]
        self.__tip.setText("M%d: %s (%s)" % (self.__uid, v, m))
        self.parentPlot().replot()

    def slot_set_color(self):
        self.__set_color()
        self.parentPlot().replot()

    def mouseMoveEvent(self, event: QMouseEvent, _):
        event.accept()
        x_ms: float = self._mouse2ms(event)
        i_old: int = self.i
        self.setGraphKey(x_ms)
        self.updatePosition()  # mandatory
        if i_old != self.i:
            self.__move_tip()

    def __slot_context_menu(self, pos: QPointF):
        context_menu = QMenu()
        action_edit = context_menu.addAction("Edit...")
        action_del = context_menu.addAction("Delete")
        point = self.parentPlot().mapToGlobal(pos.toPoint())
        chosen_action = context_menu.exec_(point)
        if chosen_action == action_edit:
            self.__edit_self()
        elif chosen_action == action_del:
            self.__sigraph.del_ptr_msr(self)

    def __edit_self(self):
        form = MsrPtrDialog((self.x, self._root.x_min, self._root.x_max, 1000 / self._root.osc.rate, self.__func_i))
        if form.exec_():  # TODO: optimize
            self.setGraphKey(form.f_val.value())
            self.updatePosition()
            self.__func_i = form.f_func.currentIndex()
            self.__move_tip()

    def clean(self):
        """Clean self before deleting"""
        self._root.msr_ptr_uids.remove(self.__uid)
        self.parentPlot().removeItem(self.__tip)

    @property
    def state(self) -> State:
        return self.State(
            uid=self.__uid,
            i=self.i
        )


class LvlPtr(QCPItemStraightLine):
    @dataclass
    class State:
        uid: int
        y: float

    class _Tip(_TipBase):
        def __init__(self, cp: QCustomPlot):
            super().__init__(cp)
            self.setColor(Qt.white)  # text

    __sigraph: QObject
    __root: QWidget
    __signal: mycomtrade.AnalogSignal
    __uid: int  # uniq id
    __tip: _Tip
    __mult: float  # multiplier reduced<>real
    signal_rmb_clicked = pyqtSignal(QPointF)

    def __init__(self, sigraph: QObject, root: QWidget, signal: mycomtrade.AnalogSignal, uid: int, y: float):
        super().__init__(sigraph.graph.parentPlot())
        self.__sigraph = sigraph
        self.__root = root
        self.__signal = signal
        self.__uid = uid
        self.__tip = self._Tip(self.parentPlot())
        # self.setPen(iosc.const.PEN_PTR_OMP)
        self.__set_color()
        self.y_reduced = y
        self.__mult = max(max(max(signal.value), 0), abs(min(0, min(signal.value))))  # multiplier rediced<>real
        self.__slot_update_text()
        self.__root.lvl_ptr_uids.add(self.__uid)
        self.signal_rmb_clicked.connect(self.__slot_context_menu)
        # self.__root.signal_chged_shift.connect(self.__slot_update_text)  # behavior undefined
        self.__root.signal_chged_pors.connect(self.__slot_update_text)

    @property
    def uid(self) -> int:
        return self.__uid

    @property
    def y_reduced(self) -> float:
        return self.point1.coords().y()

    @y_reduced.setter
    def y_reduced(self, y: float):
        """
        :param y:
        :note: for  QCPItemLine: s/point1/start/, s/point2/end/
        """
        self.point1.setCoords(self.__root.x_min, y)
        self.point2.setCoords(self.__root.x_max, y)
        self.__tip.position.setCoords(0, self.y_reduced)  # FIXME: x = ?
        self.__tip.setPositionAlignment(Qt.AlignLeft | (Qt.AlignTop if self.y_reduced > 0 else Qt.AlignBottom))

    @property
    def y_real(self) -> float:
        return self.y_reduced * self.__mult

    @y_real.setter
    def y_real(self, y: float):
        self.y_reduced = y / self.__mult

    def __set_color(self):
        pen = QPen(iosc.const.PENSTYLE_PTR_LVL)
        color = QColor.fromRgb(*self.__signal.rgb)
        pen.setColor(color)
        self.setPen(pen)
        self.__tip.setBrush(QBrush(color))  # rect

    def slot_set_color(self):
        self.__set_color()
        self.parentPlot().replot()

    def __y_pors(self, y: float) -> float:
        """
        Reduce value according go global pors mode
        :param y: Value to redice
        :return: porsed y
        """
        return y * self.__signal.get_mult(self.__root.show_sec)

    def __slot_update_text(self):
        self.__tip.setText("L%d: %s" % (self.__uid, self.__root.sig2str(self.__signal, self.y_real)))
        self.parentPlot().replot()  # TODO: don't to this on total repaint

    def mousePressEvent(self, event: QMouseEvent, _):  # rmb click start
        if event.button() == Qt.RightButton:
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent, _):  # rmb click end
        if event.button() == Qt.RightButton:
            self.signal_rmb_clicked.emit(event.pos())
        else:
            event.ignore()

    def __slot_context_menu(self, pos: QPointF):
        context_menu = QMenu()
        action_edit = context_menu.addAction("Edit...")
        action_del = context_menu.addAction("Delete")
        point = self.parentPlot().mapToGlobal(pos.toPoint())
        chosen_action = context_menu.exec_(point)
        if chosen_action == action_edit:
            self.__edit_self()
        elif chosen_action == action_del:
            self.__sigraph.del_ptr_lvl(self)

    def __edit_self(self):
        # pors all values
        form = LvlPtrDialog((
            self.__y_pors(self.y_real),
            self.__y_pors(min(self.__signal.value)),
            self.__y_pors(max(self.__signal.value))
        ))
        if form.exec_():
            # unpors back
            self.y_real = form.f_val.value() / self.__signal.get_mult(self.__root.show_sec)
            self.__slot_update_text()

    def clean(self):
        self.__root.lvl_ptr_uids.remove(self.__uid)
        self.parentPlot().removeItem(self.__tip)

    @property
    def state(self) -> State:
        return self.State(
            uid=self.__uid,
            y=self.y_reduced
        )
