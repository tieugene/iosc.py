from typing import Optional, Union

from PyQt5.QtCore import QMargins, pyqtSignal, Qt, QPoint, QObject
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QTableWidget, QVBoxLayout, QHBoxLayout, QMenu, QListWidget, \
    QListWidgetItem
from QCustomPlot2 import QCustomPlot

import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.dialog import StatusSignalPropertiesDialog, AnalogSignalPropertiesDialog, SignalPropertiesDialog


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


class SignalLabel(QListWidgetItem):
    _prop_dlg_cls: SignalPropertiesDialog
    _signal: Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal]
    _root: QWidget
    sibling: Optional[QObject]  # SignalGraph
    # signal_restyled = pyqtSignal()  # N/A

    def __init__(self, signal: Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal], root: QWidget,
                 parent: QWidget = None):
        super().__init__(parent)
        self._signal = signal
        self._root = root
        self._set_style()
        self.slot_update_value()
        self._root.signal_ptr_moved_main.connect(self.slot_update_value)

    @property
    def _value_str(self) -> str:
        return ''  # stub

    @property
    def signal(self) -> Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal]:
        return self._signal

    @property
    def whoami(self) -> int:
        """
        :return: Signal number in correspondent signal list
        """
        return self._signal.i

    def _set_style(self):
        self.setForeground(QBrush(QColor(*self._signal.rgb)))

    def do_sig_property(self):
        """Show/set signal properties"""
        if self._prop_dlg_cls(self._signal).execute():
            self._set_style()
            self.sibling.slot_signal_restyled()

    def do_hide(self):
        """Hide signal in table
        # FIXME: row != signal no
        # TODO: convert to signal call
        """
        self.setHidden(True)
        # TODO: hide chart

    def slot_update_value(self):
        """Update ctrl widget value"""
        self.setText("%s\n%s" % (self._signal.sid, self._value_str))


class StatusSignalLabel(SignalLabel):
    _prop_dlg_cls = StatusSignalPropertiesDialog

    def __init__(self, signal: mycomtrade.StatusSignal, root: QWidget, parent: QWidget = None):
        super().__init__(signal, root, parent)

    @property
    def _value_str(self) -> str:
        """String representation of current value"""
        return str(self._signal.value[self._root.main_ptr_i])


class AnalogSignalLabel(SignalLabel):
    _prop_dlg_cls = AnalogSignalPropertiesDialog

    def __init__(self, signal: mycomtrade.AnalogSignal, root: QWidget, parent: QWidget = None):
        super().__init__(signal, root, parent)
        self._root.signal_chged_shift.connect(self.slot_update_value)
        self._root.signal_chged_pors.connect(self.slot_update_value)
        self._root.signal_chged_func.connect(self.slot_update_value)

    @property
    def _value_str(self) -> str:
        return self._root.sig2str_i(self._signal, self._root.main_ptr_i, self._root.viewas)


class SignalLabelList(QListWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setSelectionMode(self.SingleSelection)  # FIXME: table row selection not works
        self.setDragEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__slot_context_menu)
        self.itemClicked.connect(self.__slot_item_clicked)

    def __slot_item_clicked(self, _):
        """Deselect item on mouse up"""
        self.clearSelection()

    def __slot_context_menu(self, point: QPoint):
        if not (item := self.itemAt(point)):
            return
        context_menu = QMenu()
        action_sig_property = context_menu.addAction("Channel property")
        action_sig_hide = context_menu.addAction("Hide channel")
        chosen_action = context_menu.exec_(self.mapToGlobal(point))
        if chosen_action == action_sig_hide:
            self.__do_sig_hide(item)
        elif chosen_action == action_sig_property:
            item.do_sig_property()

    def __do_sig_hide(self, item: SignalLabel):
        item.do_hide()
        hide_me = True
        for i in range(self.count()):
            hide_me &= self.item(i).isHidden()
        if hide_me:  # self>SignalCtrlWidget>QWidget>SignalListTable
            self.parent().parent().parent().hideRow(item.signal.i)  # FIXME: works for init state only


class SignalCtrlWidget(QWidget):
    _root: QWidget
    _t_side: SignalLabelList
    _b_side: ZoomButtonBox
    sibling: Optional[QCustomPlot]  # SignalChartWidget

    def __init__(self, root: QWidget, parent: QTableWidget):
        super().__init__(parent)
        self._root = root
        self.__mk_widgets()
        self.__mk_layout()
        self._b_side.hide()
        self._b_side.signal_zoom.connect(self.slot_vzoom)

    @property
    def table(self) -> QTableWidget:
        """Return parent table"""
        return self.parent().parent()

    @property
    def row(self) -> int:
        """Get row of parent table"""
        parent_table = self.table
        for i in range(parent_table.rowCount()):
            if parent_table.cellWidget(i, 0) == self:
                return i

    def __mk_widgets(self):
        self._t_side = SignalLabelList(self)
        self._b_side = ZoomButtonBox(self)

    def __mk_layout(self):
        self.setContentsMargins(QMargins())
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(QMargins())
        layout.addWidget(QLabel(iosc.const.C0_TEXT))  # TODO: Drag anchor (tmp hack)
        layout.addWidget(self._t_side)
        layout.addWidget(self._b_side)
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        self.setLayout(layout)

    def __chk_zoom_buttons(self):
        """Hide/Show zoom buttons depending on signals"""
        show = False
        for i in range(self._t_side.count()):
            show |= not self._t_side.item(i).signal.is_bool
        self._b_side.setVisible(show)

    def add_signal(self, signal: mycomtrade.Signal) -> Union[StatusSignalLabel, AnalogSignalLabel]:
        lbl = StatusSignalLabel(signal, self._root) if signal.is_bool else AnalogSignalLabel(signal, self._root)
        self._t_side.addItem(lbl)
        self.__chk_zoom_buttons()
        return lbl

    def del_siglabel(self, label: SignalLabel):
        todel = self._t_side.takeItem(self._t_side.row(label))
        del todel

    @property
    def sig_count(self) -> int:
        return self._t_side.count()

    def vzoom_sync(self):
        self._b_side.set_enabled(self.sibling.zoom)

    def slot_vzoom(self, z: int):
        if z:
            self.sibling.zoom += z
        else:
            self.sibling.zoom = 1
        self.vzoom_sync()
