"""Pointers."""
# 1. std
from typing import Optional
# 2. 3rd
from PyQt5.QtCore import Qt, QMargins, QPointF, pyqtSignal
from PyQt5.QtGui import QBrush, QFont, QMouseEvent, QCursor, QPen
from PyQt5.QtWidgets import QWidget, QMenu, QInputDialog
from QCustomPlot_PyQt5 import QCPItemTracer, QCustomPlot, QCPItemStraightLine, QCPItemText, QCPItemRect, QCPGraph
# 3. local
import iosc.const
from iosc.sig.widget.dialog import MsrPtrDialog, LvlPtrDialog


class VLine(QCPItemStraightLine):
    """Vertical line."""

    def __init__(self, cp: QCustomPlot):
        """Init VLine object."""
        super().__init__(cp)

    def move2x(self, x: float):
        """Move pointer to x-position.

        :param x: Position to move.
        :note: for  QCPItemLine: s/point1/start/, s/point2/end/
        """
        self.point1.setCoords(x, 0)
        self.point2.setCoords(x, 1)

    @property
    def x(self):
        """:return: Pointer x-position (ms)."""
        return self.point1.coords().x()


class Ptr(QCPItemTracer):
    """Pointers base class."""

    __cursor: QCursor
    _oscwin: 'ComtradeWidget'  # noqa: F821
    signal_ptr_moved = pyqtSignal(int)
    signal_rmb_clicked = pyqtSignal(QPointF)

    def __init__(self, graph: QCPGraph, root: 'ComtradeWidget'):  # noqa: F821
        """Init Ptr object."""
        super().__init__(graph.parentPlot())
        self._oscwin = root
        self.setGraph(graph)
        self.position.setAxes(graph.parentPlot().xAxis, None)

    def mousePressEvent(self, event: QMouseEvent, _):
        """Inherited."""
        if event.button() == Qt.LeftButton:
            event.accept()
            self.selection = True
        elif event.button() == Qt.RightButton:
            event.accept()  # for signal_rmb_clicked
        else:
            event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent, _):
        """Inherited."""
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
        """:return: Object is selected."""
        return self.selected()

    @selection.setter
    def selection(self, val: bool):
        """Set object selected."""
        self.setSelected(val)
        self.parentPlot().ptr_selected = val

    @property
    def x(self) -> float:
        """:return: Current x-position (ms)."""
        return self.position.key()

    @property
    def i(self) -> int:
        """:return: Index of current position."""
        return self._oscwin.x2i(self.x)

    def _switch_cursor(self, selected: bool):
        if selected:
            self.__cursor = self._oscwin.cursor()
            cur = iosc.const.CURSOR_PTR_V
        else:
            cur = self.__cursor
        self._oscwin.setCursor(cur)

    def _mouse2ms(self, event: QMouseEvent) -> float:
        """Get mouse position as ms."""
        return self.parentPlot().xAxis.pixelToCoord(event.pos().x())  # ms, realative to z-point


class SCPtr(Ptr):
    """OMP SC (Short Circuit, right) pointer."""

    __pr_ptr: VLine  # Sibling PR (left) pointer

    def __init__(self, graph: QCPGraph, root: QWidget):
        """Init SCPtr object."""
        super().__init__(graph, root)
        self.setPen(iosc.const.PEN_PTR_OMP)
        self.__pr_ptr = VLine(graph.parentPlot())
        self.__pr_ptr.setPen(iosc.const.PEN_PTR_OMP)
        self.__slot_ptr_move(self._oscwin.omp_ptr.i_sc, False)
        self.selectionChanged.connect(self.__selection_chg)
        self.signal_ptr_moved.connect(self._oscwin.slot_ptr_moved_sc)
        self._oscwin.signal_ptr_moved_sc.connect(self.__slot_ptr_move)

    def get_new_omp_width(self, parent: QWidget, old_value: int, max_v: int) -> Optional[int]:
        """:return: New OMP ptrs distance."""
        new_value, ok = QInputDialog.getInt(
            parent,
            self.tr("Distance between PR and SC"),
            self.tr("Main frequency periods number"),
            old_value,
            2,
            max_v
        )
        if ok and new_value != old_value:
            return new_value

    def __selection_chg(self, selection: bool):
        self._switch_cursor(selection)
        self.parentPlot().replot()  # update selection decoration

    def __slot_ptr_move(self, i: int, replot: bool = True):
        if not self.selected():  # check is not myself
            self.setGraphKey(self._oscwin.i2x(i))
        self.__pr_ptr.move2x(self._oscwin.i2x(i - self._oscwin.omp_ptr.w * self._oscwin.osc.spp))
        if replot:
            self.parentPlot().replot()

    def mouseMoveEvent(self, event: QMouseEvent, pos: QPointF):
        """Inherited.

        :param event: Subj
        :param pos: Where mouse was pressed (looks like fixed)
        :note: self.mouseMoveEvent() unusable because points to click position
        """
        if not self.selected():  # protection against 2click
            event.ignore()
            return
        event.accept()
        x_ms: float = self._mouse2ms(event)  # ms, realative to z-point
        if (x_ms < self._oscwin.i2x(self._oscwin.omp_ptr.i_sc_min))\
                or (x_ms > self._oscwin.i2x(self._oscwin.omp_ptr.i_sc_max)):
            return
        i_old = self.i
        self.setGraphKey(x_ms)
        self.updatePosition()  # mandatory
        if self.i != i_old:
            self.signal_ptr_moved.emit(self.i)  # replot will be after PR moving

    def mouseDoubleClickEvent(self, event: QMouseEvent, _):
        """Inherited."""
        event.accept()
        if new_omp_width := self.get_new_omp_width(self._oscwin, self._oscwin.omp_ptr.w, self._oscwin.omp_ptr.w_max):
            self._oscwin.omp_ptr.set_w(new_omp_width)
            self.signal_ptr_moved.emit(self._oscwin.omp_ptr.i_sc)


class _TipBase(QCPItemText):
    """Tip (on way) base class."""
    def __init__(self, cp: QCustomPlot):
        super().__init__(cp)
        self.setFont(QFont('mono', 8))
        self.setPadding(QMargins(2, 2, 2, 2))
        self.setTextAlignment(Qt.AlignCenter)


class _PowerPtr(Ptr):
    """Pointer with tip and rectangle."""

    class _Tip(_TipBase):
        """Pointer tip."""

        def __init__(self, cp: QCustomPlot):
            """Init _Tip object."""
            super().__init__(cp)
            self.setColor(Qt.black)  # text
            self.setPen(Qt.red)
            self.setBrush(iosc.const.BRUSH_TIP)  # rect

        def move2x(self, x: float, x_old: float):
            """Move tip to x-position."""
            dx = x - x_old
            self.setPositionAlignment((Qt.AlignLeft if dx > 0 else Qt.AlignRight) | Qt.AlignBottom)
            self.position.setCoords(x, 0)
            self.setText("%.2f" % dx)

    class _Rect(QCPItemRect):
        """Rectangle between old and new ptr postitions."""

        def __init__(self, cp: QCustomPlot):
            """Init _Rect object."""
            super().__init__(cp)
            self.setPen(iosc.const.COLOR_RECT)
            self.setBrush(iosc.const.COLOR_RECT)

        def set2x(self, x: float):
            """Set starting point."""
            yaxis = self.parentPlot().yAxis
            self.topLeft.setCoords(x, yaxis.pixelToCoord(0) - yaxis.pixelToCoord(iosc.const.RECT_PTR_HEIGHT))

        def stretch2x(self, x: float):
            """Stretch the rect to given position."""
            self.bottomRight.setCoords(x, 0)

    __old_pos: VLine
    __rect: _Rect
    __tip: _Tip

    def __init__(self, graph: QCPGraph, root: QWidget):
        """Init _PowerPtr object."""
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
            self.__tip.move2x(self.x, self.__old_pos.x)
            self.__rect.stretch2x(self.x)
            self.parentPlot().replot()
            return i_new


class MainPtr(_PowerPtr):
    """Main pointer."""

    def __init__(self, graph: QCPGraph, root: 'ComtradeWidget'):  # noqa: F821
        """Init MainPtr object."""
        super().__init__(graph, root)
        self.setPen(iosc.const.PEN_PTR_MAIN)
        self.slot_ptr_move(self._oscwin.main_ptr_i, False)
        # print(self.oscwin.main_ptr_i)
        self.signal_ptr_moved.connect(self._oscwin.slot_ptr_moved_main)
        self._oscwin.signal_ptr_moved_main.connect(self.slot_ptr_move)

    def slot_ptr_move(self, i: int, replot: bool = True):
        """Move local (bar) MainPtr to global main ptr position."""
        if not self.selected():  # check is not myself
            self.setGraphKey(self._oscwin.i2x(i))
            if replot:
                self.parentPlot().replot()

    def mouseMoveEvent(self, event: QMouseEvent, pos: QPointF):
        """Inherited.

        :param event: Subj
        :param pos: Where mouse was pressed (looks like fixed)
        :note: self.mouseMoveEvent() unusable because points to click position
        """
        if (i_new := self._handle_mouse_move_event(event)) is not None:
            self.signal_ptr_moved.emit(i_new)


class TmpPtr(_PowerPtr):
    """Temporary pointer."""

    _uid: int
    signal_ptr_moved_tmp = pyqtSignal(int, int)
    # signal_ptr_del_tmp = pyqtSignal(int)
    signal_ptr_edit_tmp = pyqtSignal(int)

    def __init__(self, graph: QCPGraph, root: QWidget, uid: int):
        """Init TmpPtr object."""
        super().__init__(graph, root)
        self._uid = uid
        self.setPen(iosc.const.PEN_PTR_TMP)
        self.__slot_ptr_move(uid, self._oscwin.tmp_ptr_i[uid], False)
        self.signal_ptr_moved_tmp.connect(self._oscwin.slot_ptr_moved_tmp)
        # self.signal_ptr_del_tmp.connect(self.oscwin.slot_ptr_del_tmp)
        self.signal_ptr_edit_tmp.connect(self._oscwin.slot_ptr_edit_tmp)
        self._oscwin.signal_ptr_moved_tmp.connect(self.__slot_ptr_move)
        self.signal_rmb_clicked.connect(self.__slot_context_menu)

    def __slot_ptr_move(self, uid: int, i: int, replot: bool = True):
        if not self.selected() and uid == self._uid:  # check is not myself and myself
            self.setGraphKey(self._oscwin.i2x(i))
            if replot:
                self.parentPlot().replot()

    def mouseMoveEvent(self, event: QMouseEvent, pos: QPointF):
        """Inherited.

        :param event: Subj
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
            self._oscwin.slot_ptr_del_tmp(self._uid)
            # self.signal_ptr_del_tmp.emit(self.__uid)


class MsrPtr(Ptr):
    """Measure pointer."""

    class _Tip(_TipBase):
        def __init__(self, cp: QCustomPlot):
            super().__init__(cp)
            self.setColor(Qt.white)  # text
            self.setPositionAlignment(Qt.AlignLeft | Qt.AlignBottom)

    FUNC_ABBR = ("I", "M", "E", "H1", "H2", "H3", "H5")
    __ss: 'AnalogSignalSuit'  # noqa: F821
    __uid: int  # uniq id
    __func_i: int  # value mode (function) number (in sigfunc.func_list[])
    __tip: _Tip
    signal_ptr_del_msr = pyqtSignal(int)

    def __init__(self, ss: 'AnalogSignalSuit', uid: int):  # noqa: F821
        """Init MsrPtr object."""
        super().__init__(ss.graph, ss.oscwin)
        self.__ss = ss
        self.__uid = uid
        self.__func_i = self.__ss.msr_ptr[uid][2]
        self.__tip = self._Tip(ss.graph.parentPlot())
        self.setGraphKey(self._oscwin.i2x(self.__ss.msr_ptr[uid][1]))
        self.updatePosition()
        self.__set_color()
        self.__move_tip()
        self.__ss.msr_ptr[uid][0] = self  # embed self into parent ss
        self._oscwin.msr_ptr_uids.add(uid)
        self.selectionChanged.connect(self.__slot_selection_chg)
        self._oscwin.signal_chged_shift.connect(self.__slot_update_text)
        self._oscwin.signal_chged_pors.connect(self.__slot_update_text)
        self.signal_rmb_clicked.connect(self.__slot_context_menu)

    @property
    def uid(self) -> int:
        """:return: Pointer uniq id."""
        return self.__uid

    def __set_color(self):
        pen = QPen(iosc.const.PENSTYLE_PTR_MSR)
        color = self.__ss.color
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
        v = self.__ss.sig2str_i(self.i)  # was self.position.value()
        m = self.FUNC_ABBR[self._oscwin.viewas]
        self.__tip.setText("M%d: %s (%s)" % (self.__uid, v, m))
        self.parentPlot().replot()

    def slot_set_color(self):
        """Set pointer color."""
        self.__set_color()
        self.parentPlot().replot()

    def mouseMoveEvent(self, event: QMouseEvent, _):
        """Inherited."""
        event.accept()
        x_ms: float = self._mouse2ms(event)
        i_old: int = self.i
        self.setGraphKey(x_ms)
        self.updatePosition()  # mandatory
        if i_old != self.i:
            self.__move_tip()

    def __slot_context_menu(self, pos: QPointF):
        context_menu = QMenu()
        action_edit = context_menu.addAction(self.tr("Edit..."))
        action_del = context_menu.addAction(self.tr("Delete"))
        point = self.parentPlot().mapToGlobal(pos.toPoint())
        chosen_action = context_menu.exec_(point)
        if chosen_action == action_edit:
            self.__edit_self()
        elif chosen_action == action_del:
            self.__ss.del_ptr_msr(self.__uid)

    def __edit_self(self):
        form = MsrPtrDialog((
            self.x,
            self._oscwin.osc.x_min,
            self._oscwin.osc.x_max, 1000 / self._oscwin.osc.rate,
            self.__func_i
        ))
        if form.exec_():  # TODO: optimize
            self.setGraphKey(form.f_val.value())
            self.updatePosition()
            self.__func_i = form.f_func.currentIndex()
            self.__move_tip()

    def suicide(self):
        """Clean self before deleting."""
        # flush self data
        self.__ss.msr_ptr[self.__uid][2] = self.__func_i
        self.__ss.msr_ptr[self.__uid][1] = self.i
        self.parentPlot().removeItem(self.__tip)
        self.parentPlot().removeItem(self)
        self._oscwin.msr_ptr_uids.remove(self.__uid)
        self.__ss.msr_ptr[self.__uid][0] = None


class LvlPtr(QCPItemStraightLine):
    """Level pointer."""

    class _Tip(_TipBase):
        def __init__(self, cp: QCustomPlot):
            super().__init__(cp)
            self.setColor(Qt.white)  # text

    __cursor: QCursor
    __ss: 'AnalogSignalSuit'  # noqa: F821
    __oscwin: 'ComtradeWidget'  # noqa: F821
    __uid: int  # uniq id
    __tip: _Tip
    __y_rel: float  # 0..1 (Ymin..Ymax)
    # __mult: float  # multiplier reduced<>real
    signal_rmb_clicked = pyqtSignal(QPointF)

    def __init__(self, ss: 'AnalogSignalSuit', uid: int):  # noqa: F821
        """Init LvlPtr object."""
        super().__init__(ss.graph.parentPlot())
        self.__ss = ss
        self.__uid = uid
        self.__oscwin = ss.oscwin
        self.__tip = self._Tip(self.parentPlot())
        # self.setPen(iosc.const.PEN_PTR_OMP)
        self.__y_rel = self.__ss.lvl_ptr[self.__uid][1]
        self.__ss.lvl_ptr[self.__uid][0] = self
        self.__oscwin.lvl_ptr_uids.add(self.__uid)
        self.__set_color()
        self.__slot_move()
        self.selectionChanged.connect(self.__selection_chg)
        self.signal_rmb_clicked.connect(self.__slot_context_menu)
        self.__oscwin.signal_chged_shift.connect(self.__slot_move)  # behavior undefined
        self.__oscwin.signal_chged_pors.connect(self.__slot_update_text)

    @property
    def selection(self) -> bool:
        """:return: Whether the pointer is selected."""
        return self.selected()

    @selection.setter
    def selection(self, val: bool):
        """[De]Select the pointer."""
        self.setSelected(val)
        self.parentPlot().ptr_selected = val

    @property
    def uid(self) -> int:
        """:return: Pinter uinq id."""
        return self.__uid

    def get_y_rel(self) -> float:
        """Get relative (Ymin..Ymax) ptr position, 0..1."""
        return self.__y_rel

    def __get_y_scr(self) -> float:
        """Convert relative value into screen y-coord.

        Used:
        - .__slot_move()
        """
        return (a_min := self.__ss.a_v_min()) + self.__y_rel * (self.__ss.a_v_max() - a_min)

    def __set_y_scr(self, v: float):
        """Convert screen y-coord into relative value.

        Used:
        - .mouseMoveEvent()
        """
        self.__y_rel = (v - (a_min := self.__ss.a_v_min())) / (self.__ss.a_v_max() - a_min)

    def get_y_nat(self) -> float:
        """Get natural (real) signal value in the level.

        Used:
        - .__edit_self()
        - .__slot_update_text()
        - AGraphItem.__init__()
        :todo: * self.__ss.a_div()
        """
        return self.__y_pors((v_min := self.__ss.v_min) + self.__y_rel * (self.__ss.v_max - v_min))

    def __y_pors(self, v: float) -> float:
        """Reduce value according go global pors mode.

        :param v: Value to PorS
        :return: PorS'ed v
        """
        return v * self.__ss.pors_mult

    def __slot_move(self):
        """Move ptr to screen y-coord."""
        y = self.__get_y_scr()
        self.point1.setCoords(self.__oscwin.osc.x_min, y)
        self.point2.setCoords(self.__oscwin.osc.x_max, y)
        self.__tip.position.setCoords(0, y)  # FIXME: x = ?
        self.__tip.setPositionAlignment(Qt.AlignLeft | (Qt.AlignTop if y > 0 else Qt.AlignBottom))
        self.__slot_update_text()

    def __slot_update_text(self):
        self.__tip.setText("L%d: %s" % (self.__uid, self.__ss.sig2str(self.get_y_nat())))
        self.parentPlot().replot()  # TODO: don't to this on total repaint

    def __set_color(self):
        pen = QPen(iosc.const.PENSTYLE_PTR_LVL)
        color = self.__ss.color
        pen.setColor(color)
        self.setPen(pen)
        self.__tip.setBrush(QBrush(color))  # rect

    def slot_set_color(self):
        """Update ptr color."""
        self.__set_color()
        self.parentPlot().replot()

    def mousePressEvent(self, event: QMouseEvent, _):
        """Inherited."""
        if event.button() == Qt.LeftButton:
            event.accept()
            self.selection = True
        elif event.button() == Qt.RightButton:
            event.accept()  # for signal_rmb_clicked
        else:
            event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent, _):
        """Inherited."""
        if event.button() == Qt.LeftButton:
            if self.selection:
                event.accept()
                self.selection = False
        elif event.button() == Qt.RightButton:
            self.signal_rmb_clicked.emit(event.pos())
        else:
            event.ignore()

    def mouseMoveEvent(self, event: QMouseEvent, pos: QPointF):
        """Inherited.

        :param event: Subj
        :param pos: Where mouse was pressed (mousePressEvent), not changing each step; unusual
        :note: self.mouseMoveEvent() unusable because points to click position
        """
        if not self.selected():  # protection against 2click
            event.ignore()
            return
        event.accept()
        y_reduced_new = self.parentPlot().yAxis.pixelToCoord(event.pos().y())
        if self.__ss.a_v_min() <= y_reduced_new <= self.__ss.a_v_max():
            self.__set_y_scr(y_reduced_new)
            self.__slot_move()

    def __switch_cursor(self, selected: bool):
        if selected:
            self.__cursor = self.__oscwin.cursor()
            cur = iosc.const.CURSOR_PTR_H
        else:
            cur = self.__cursor
        self.__oscwin.setCursor(cur)

    def __selection_chg(self, selection: bool):
        self.__switch_cursor(selection)
        self.parentPlot().replot()  # update selection decoration

    def __slot_context_menu(self, pos: QPointF):
        context_menu = QMenu()
        action_edit = context_menu.addAction(self.tr("Edit..."))
        action_del = context_menu.addAction(self.tr("Delete"))
        point = self.parentPlot().mapToGlobal(pos.toPoint())
        chosen_action = context_menu.exec_(point)
        if chosen_action == action_edit:
            self.__edit_self()
        elif chosen_action == action_del:
            self.__ss.del_ptr_lvl(self.__uid)

    def __edit_self(self):
        # pors all values
        form = LvlPtrDialog((
            self.get_y_nat(),
            self.__y_pors(self.__ss.v_min),
            self.__y_pors(self.__ss.v_max)
        ))
        if form.exec_():
            # unpors back
            self.__y_rel = (form.f_val.value() - form.f_val.minimum()) / (form.f_val.maximum() - form.f_val.minimum())
            self.__slot_move()

    def suicide(self):
        """Self destroy."""
        self.__ss.lvl_ptr[self.__uid][1] = self.get_y_rel()
        self.parentPlot().removeItem(self.__tip)
        self.parentPlot().removeItem(self)
        self.__oscwin.lvl_ptr_uids.remove(self.__uid)
        self.__ss.lvl_ptr[self.__uid][0] = None
