from typing import Optional

from PyQt5.QtCore import QMargins, pyqtSignal, Qt, QPoint
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QTableWidget, QVBoxLayout, QHBoxLayout, QMenu, QListWidget, \
    QListWidgetItem
from QCustomPlot2 import QCustomPlot

import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.dialog import StatusSignalPropertiesDialog, AnalogSignalPropertiesDialog


class ZoomButton(QPushButton):
    def __init__(self, txt: str, parent: QWidget = None):
        super().__init__(txt, parent)
        self.setContentsMargins(QMargins())  # not helps
        self.setFixedWidth(iosc.const.SIG_ZOOM_BTN_WIDTH)
        # self.setFlat(True)
        # TODO: squeeze


class ZoomButtonBox(QWidget):
    _b_zoom_in: ZoomButton
    _b_zoom_0: ZoomButton
    _b_zoom_out: ZoomButton
    signal_zoom = pyqtSignal(int)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._b_zoom_in = ZoomButton("+", self)
        self._b_zoom_0 = ZoomButton("=", self)
        self._b_zoom_out = ZoomButton("-", self)
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(QMargins())
        self.layout().addWidget(self._b_zoom_in)
        self.layout().addWidget(self._b_zoom_0)
        self.layout().addWidget(self._b_zoom_out)
        self._b_zoom_0.setEnabled(False)
        self._b_zoom_out.setEnabled(False)
        self._b_zoom_in.clicked.connect(self.__slot_vzoom_in)
        self._b_zoom_0.clicked.connect(self.__slot_vzoom_0)
        self._b_zoom_out.clicked.connect(self.__slot_vzoom_out)

    def __slot_vzoom_in(self):
        self.signal_zoom.emit(1)

    def __slot_vzoom_out(self):
        self.signal_zoom.emit(-1)

    def __slot_vzoom_0(self):
        self.signal_zoom.emit(0)

    def set_enabled(self, z: int):
        self._b_zoom_0.setEnabled(z > 1)
        self._b_zoom_out.setEnabled(z > 1)


class SignalCtrlWidget(QWidget):
    _root: QWidget
    _signal: mycomtrade.Signal
    _t_side: QListWidget
    _b_side: ZoomButtonBox
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
        self.slot_update_value()
        self.customContextMenuRequested.connect(self.__slot_context_menu)  # FIXME: for single signal only
        self._root.signal_ptr_moved_main.connect(self.slot_update_value)

    def __mk_widgets(self):
        self._t_side = QListWidget(self)
        self._t_side.setSelectionMode(self._t_side.NoSelection)  # FIXME: table row selection not works
        self._t_side.addItem(QListWidgetItem())
        self._b_side = ZoomButtonBox(self)

    def __mk_layout(self):
        self.setContentsMargins(QMargins())
        self.setLayout(QHBoxLayout(self))
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(QMargins())
        self.layout().addWidget(self._t_side)
        self.layout().addWidget(self._b_side)
        self.layout().setStretch(0, 1)
        self.layout().setStretch(1, 0)

    def _set_style(self):
        self._t_side.item(0).setForeground(QBrush(QColor(*self._signal.rgb)))

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
        text = "%s\n%d" % (self._signal.sid, self._signal.value[self._root.main_ptr_i])
        self._t_side.item(0).setText(text)


class AnalogSignalCtrlWidget(SignalCtrlWidget):
    def __init__(self, signal: mycomtrade.AnalogSignal, parent: QTableWidget, root: QWidget):
        super().__init__(signal, parent, root)
        self._root.signal_chged_shift.connect(self.slot_update_value)
        self._root.signal_chged_pors.connect(self.slot_update_value)
        self._root.signal_chged_func.connect(self.slot_update_value)
        self._b_side.signal_zoom.connect(self.slot_vzoom)

    def _do_sig_property(self):
        """Show/set signal properties"""
        if AnalogSignalPropertiesDialog(self._signal).execute():
            self._set_style()
            self.signal_restyled.emit()

    def slot_update_value(self):
        """Update ctrl widget value depending on pri/sec and value type"""
        text = "%s\n%s" % (
            self._signal.sid,
            self._root.sig2str_i(self._signal, self._root.main_ptr_i, self._root.viewas)
        )
        self._t_side.item(0).setText(text)

    def vzoom_sync(self):
        self._b_side.set_enabled(self.sibling.zoom)

    def slot_vzoom(self, z: int):
        if z:
            self.sibling.zoom += z
        else:
            self.sibling.zoom = 1
        self.vzoom_sync()
