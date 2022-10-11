import cmath
import math
from typing import Optional

from PyQt5.QtCore import QMargins, pyqtSignal, Qt, QPoint
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QTableWidget, QVBoxLayout, QHBoxLayout, QMenu
from QCustomPlot2 import QCustomPlot

import iosc.const
from iosc.core import mycomtrade, sigfunc
from iosc.sig.prop import StatusSignalPropertiesDialog, AnalogSignalPropertiesDialog


class ZoomButton(QPushButton):
    def __init__(self, txt: str, parent: QWidget = None):
        super().__init__(txt, parent)
        self.setContentsMargins(QMargins())  # not helps
        self.setFixedWidth(iosc.const.SIG_ZOOM_BTN_WIDTH)
        # self.setFlat(True)
        # TODO: squeeze


class SignalCtrlWidget(QWidget):
    _root: QWidget
    _signal: mycomtrade.Signal
    _f_name: QLabel
    _f_value: QLabel
    _b_side: QWidget
    _b_zoom_in: ZoomButton
    _b_zoom_0: ZoomButton
    _b_zoom_out: ZoomButton
    sibling: Optional[QCustomPlot]
    signal_restyled = pyqtSignal()

    def __init__(self, signal: mycomtrade.Signal, parent: QTableWidget, root: QWidget):
        super().__init__(parent)
        self._signal = signal
        self._root = root
        self.sibling = None
        self.__mk_widgets()
        self.__mk_layout()
        self._set_style()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__slot_context_menu)
        self._root.signal_main_ptr_moved.connect(self.slot_update_value)
        self.slot_update_value()

    def __mk_widgets(self):
        self._f_value = QLabel()
        self._f_name = QLabel()
        self._f_name.setText(self._signal.sid)
        self._b_side = QWidget(self)
        self._b_zoom_in = ZoomButton("+")
        self._b_zoom_0 = ZoomButton("=")
        self._b_zoom_out = ZoomButton("-")
        # initial state
        self._b_zoom_0.setEnabled(False)
        self._b_zoom_out.setEnabled(False)

    def __mk_layout(self):
        self.setContentsMargins(QMargins())
        # left side
        text_side = QWidget(self)
        text_side.setLayout(QVBoxLayout())
        text_side.layout().addWidget(self._f_value)
        text_side.layout().addWidget(self._f_name)
        text_side.layout().setSpacing(0)
        # text_side.layout().setContentsMargins(QMargins())
        # right side
        self._b_side.setLayout(QVBoxLayout())
        self._b_side.layout().addWidget(self._b_zoom_in)
        self._b_side.layout().addWidget(self._b_zoom_0)
        self._b_side.layout().addWidget(self._b_zoom_out)
        self._b_side.layout().setSpacing(0)
        self._b_side.layout().setContentsMargins(QMargins())
        # altogether
        self.setLayout(QHBoxLayout(self))
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(QMargins())
        self.layout().addWidget(text_side)
        self.layout().addWidget(self._b_side)
        self.layout().setStretch(0, 1)
        self.layout().setStretch(1, 0)

    def _set_style(self):
        self.setStyleSheet("QLabel { color : rgb(%d,%d,%d); }" % self._signal.rgb)

    def __slot_context_menu(self, point: QPoint):
        context_menu = QMenu()
        action_sig_property = context_menu.addAction("Channel property")
        action_sig_hide = context_menu.addAction("Hide channel")
        chosen_action = context_menu.exec_(self.mapToGlobal(point))
        if chosen_action == action_sig_hide:
            self.__do_sig_hide()
        elif chosen_action == action_sig_property:
            self._do_sig_property()

    def __do_sig_hide(self):
        """Hide signal in table
        # FIXME: row != signal no
        # TODO: convert to signal call
        """
        self.parent().parent().hideRow(self._signal.i)

    def _do_sig_property(self):
        """Show/set signal properties"""
        ...  # stub

    def whoami(self) -> int:
        """
        :return: Signal no in correspondent signal list
        """
        return self._signal.i

    @property
    def signal(self) -> mycomtrade.Signal:
        return self._signal


class StatusSignalCtrlWidget(SignalCtrlWidget):
    def __init__(self, signal: mycomtrade.StatusSignal, parent: QTableWidget, root):
        super().__init__(signal, parent, root)
        self._b_side.hide()

    def _do_sig_property(self):
        """Show/set signal properties"""
        if StatusSignalPropertiesDialog(self._signal).execute():
            self._set_style()
            self.signal_restyled.emit()

    def slot_update_value(self):
        self._f_value.setText("%d" % self._signal.value[self._root.mptr])


class AnalogSignalCtrlWidget(SignalCtrlWidget):
    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QTableWidget, root: QWidget):
        super().__init__(signal, parent, root)
        self._root.signal_recalc_achannels.connect(self.slot_update_value)
        self._root.signal_shift_achannels.connect(self.slot_update_value)
        self._b_zoom_in.clicked.connect(self.slot_vzoom_in)
        self._b_zoom_0.clicked.connect(self.slot_vzoom_0)
        self._b_zoom_out.clicked.connect(self.slot_vzoom_out)

    def _do_sig_property(self):
        """Show/set signal properties"""
        if AnalogSignalPropertiesDialog(self._signal).execute():
            self._set_style()
            self.signal_restyled.emit()

    def slot_update_value(self):
        func = sigfunc.func_list[self._root.viewas]
        v = func(self._signal.value, self._root.mptr, self._root.tpp)
        if isinstance(v, complex):  # hrm1
            y = abs(v)
        else:
            y = v
        pors_y = y * self._signal.get_mult(self._root.show_sec)
        uu = self._signal.uu_orig
        if abs(pors_y) < 1:
            pors_y *= 1000
            uu = 'm' + uu
        elif abs(pors_y) > 1000:
            pors_y /= 1000
            uu = 'k' + uu
        if isinstance(v, complex):  # hrm1
            self._f_value.setText("%.3f %s / %.3f°" % (pors_y, uu, math.degrees(cmath.phase(v))))
        else:
            self._f_value.setText("%.3f %s" % (pors_y, uu))

    def slot_vzoom_in(self):
        if self.sibling.zoom == 1:
            self._b_zoom_0.setEnabled(True)
            self._b_zoom_out.setEnabled(True)
        self.sibling.zoom += 1

    def slot_vzoom_0(self):
        if self.sibling.zoom > 1:
            self.sibling.zoom = 1
            self._b_zoom_0.setEnabled(False)
            self._b_zoom_out.setEnabled(False)

    def slot_vzoom_out(self):
        if self.sibling.zoom > 1:
            self.sibling.zoom -= 1
            if self.sibling.zoom == 1:
                self._b_zoom_0.setEnabled(False)
                self._b_zoom_out.setEnabled(False)
