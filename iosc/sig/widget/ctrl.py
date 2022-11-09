from typing import Union

from PyQt5.QtCore import QMargins, pyqtSignal, Qt, QPoint, QRect, QMimeData
from PyQt5.QtGui import QBrush, QColor, QMouseEvent, QPixmap, QFontMetrics, QPainter, QPen, QDrag
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QVBoxLayout, QMenu, QListWidget, \
    QListWidgetItem, QFrame, QGridLayout

import iosc.const
from iosc.core import mycomtrade
from iosc.sig.widget.hline import HLine
from iosc.sig.widget.dialog import StatusSignalPropertiesDialog, AnalogSignalPropertiesDialog, SignalPropertiesDialog


class SignalLabel(QListWidgetItem):
    _prop_dlg_cls: SignalPropertiesDialog
    ss: 'SignalSuit'
    # sibling: Optional[QObject]  # SignalGraph
    # signal_restyled = pyqtSignal()  # N/A

    def __init__(self, ss: 'SignalSuit', parent: 'BarCtrlWidget.SignalLabelList' = None):
        super().__init__(parent)
        self.ss = ss
        self._set_style()
        self.slot_update_value()
        # self.ss.bar.table.oscwin.signal_ptr_moved_main.connect(self.slot_update_value)

    @property
    def _value_str(self) -> str:
        return ''  # stub

    @property
    def signal(self) -> Union[mycomtrade.StatusSignal, mycomtrade.AnalogSignal]:
        return self.ss.signal

    @property
    def whoami(self) -> int:
        """
        :return: Signal number in correspondent signal list
        """
        return self.ss.signal.i

    def _set_style(self):
        self.setForeground(QBrush(QColor(*self.ss.signal.rgb)))

    def do_sig_property(self):
        """Show/set signal properties"""
        if self._prop_dlg_cls(self.ss.signal).execute():
            self._set_style()
            # self.sibling.slot_signal_restyled()

    def do_hide(self):
        """Hide signal in table
        # FIXME: row != signal no
        # TODO: convert to signal call
        """
        self.setHidden(True)
        # TODO: hide chart

    def slot_update_value(self):
        """Update ctrl widget value"""
        self.setText("%s\n%s" % (self.ss.signal.sid, self._value_str))


class StatusSignalLabel(SignalLabel):
    _prop_dlg_cls = StatusSignalPropertiesDialog

    def __init__(self, ss: 'SignalSuit', parent: 'BarCtrlWidget.SignalLabelList' = None):
        super().__init__(ss, parent)

    @property
    def _value_str(self) -> str:
        """String representation of current value"""
        return str(self.ss.signal.value[self.ss.bar.table.oscwin.main_ptr_i])


class AnalogSignalLabel(SignalLabel):
    _prop_dlg_cls = AnalogSignalPropertiesDialog

    def __init__(self, ss: 'SignalSuit', parent: 'BarCtrlWidget.SignalLabelList' = None):
        super().__init__(ss, parent)
        # self.ss.bar.table.oscwin.signal_chged_shift.connect(self.slot_update_value)
        # self.ss.bar.table.oscwin.signal_chged_pors.connect(self.slot_update_value)
        # self.ss.bar.table.oscwin.signal_chged_func.connect(self.slot_update_value)

    @property
    def _value_str(self) -> str:
        return self.ss.bar.table.oscwin.sig2str_i(
            self.ss.signal,
            self.ss.bar.table.oscwin.main_ptr_i,
            self.ss.bar.table.oscwin.viewas
        )


class BarCtrlWidget(QWidget):
    class Anchor(QLabel):
        def __init__(self, parent: 'BarCtrlWidget'):
            super().__init__(parent)
            self.setText('↕')
            self.setCursor(Qt.PointingHandCursor)

        def mousePressEvent(self, _: QMouseEvent):
            self.__start_drag()

        def __start_drag(self):
            def _mk_icon() -> QPixmap:
                __txt = self.parent().bar.signals[0].signal.name
                br = QFontMetrics(iosc.const.FONT_DND).boundingRect(__txt)  # sig0 = 1, -11, 55, 14
                __pix = QPixmap(br.width() + 2, br.height() + 2)  # TODO: +4
                __pix.fill(Qt.transparent)
                __painter = QPainter(__pix)
                __painter.setFont(iosc.const.FONT_DND)
                __painter.setPen(QPen(Qt.black))
                __painter.drawRect(0, 0, br.width() + 1, br.height() + 1)
                __painter.drawText(br.x(), -br.y(), __txt)
                return __pix

            def _mk_mime() -> QMimeData:
                bar: 'SignalBar' = self.parent().bar
                return bar.table.mimeData([bar.table.item(bar.row, 0)])

            drag = QDrag(self)
            drag.setPixmap(_mk_icon())
            drag.setMimeData(_mk_mime())
            # drag.setHotSpot(event.pos())
            drag.exec_(Qt.MoveAction, Qt.MoveAction)

    class SignalLabelList(QListWidget):
        def __init__(self, parent: 'BarCtrlWidget'):
            super().__init__(parent)
            self.setDragEnabled(True)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollMode(self.ScrollPerPixel)
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.__slot_context_menu)
            self.itemClicked.connect(self.__slot_item_clicked)

        def __slot_item_clicked(self, _):
            """Deselect item on mouse up"""
            self.clearSelection()

        def __slot_context_menu(self, point: QPoint):
            item: SignalLabel = self.itemAt(point)
            if not item:
                return
            context_menu = QMenu()
            action_sig_hide = context_menu.addAction("Hide")
            chosen_action = context_menu.exec_(self.mapToGlobal(point))
            if chosen_action == action_sig_hide:
                item.ss.set_hidden(True)

        @property
        def selected_row(self) -> int:
            return self.selectedIndexes()[0].row()

        def startDrag(self, supported_actions: Union[Qt.DropActions, Qt.DropAction]):
            def _mk_icon() -> QPixmap:
                __txt = self.currentItem().ss.signal.name
                br = QFontMetrics(iosc.const.FONT_DND).boundingRect(__txt)  # sig0 = 1, -11, 55, 14
                __pix = QPixmap(br.width() + 1, br.height() + 1)
                __pix.fill(Qt.transparent)
                __painter = QPainter(__pix)
                __painter.setFont(iosc.const.FONT_DND)
                __painter.setPen(QPen(Qt.black))
                __painter.drawText(br.x(), -br.y(), __txt)
                return __pix

            def _mk_mime() -> QMimeData:
                return self.mimeData([self.currentItem()])

            drag = QDrag(self)
            drag.setPixmap(_mk_icon())
            drag.setMimeData(_mk_mime())
            drag.exec_(Qt.MoveAction, Qt.MoveAction)

    class ZoomButtonBox(QWidget):
        class ZoomButton(QPushButton):
            def __init__(self, txt: str, parent: 'ZoomButtonBox'):
                super().__init__(txt, parent)
                self.setContentsMargins(QMargins())  # not helps
                self.setFixedWidth(16)
                self.setFlat(True)
                self.setCursor(Qt.PointingHandCursor)

        __b_zoom_in: ZoomButton
        __b_zoom_0: ZoomButton
        __b_zoom_out: ZoomButton

        def __init__(self, parent: 'BarCtrlWidget'):
            super().__init__(parent)
            self.__b_zoom_in = self.ZoomButton("+", self)
            self.__b_zoom_0 = self.ZoomButton("⚬", self)
            self.__b_zoom_out = self.ZoomButton("-", self)
            self.setLayout(QVBoxLayout())
            self.layout().setSpacing(0)
            self.layout().setContentsMargins(QMargins())
            self.layout().addWidget(self.__b_zoom_in)
            self.layout().addWidget(self.__b_zoom_0)
            self.layout().addWidget(self.__b_zoom_out)
            self.__update_buttons()
            self.__b_zoom_in.clicked.connect(self.__slot_zoom_in)
            self.__b_zoom_0.clicked.connect(self.__slot_zoom_0)
            self.__b_zoom_out.clicked.connect(self.__slot_zoom_out)

        def __slot_zoom_in(self):
            self.__slot_zoom(1)

        def __slot_zoom_out(self):
            self.__slot_zoom(-1)

        def __slot_zoom_0(self):
            self.__slot_zoom(0)

        def __slot_zoom(self, dy: int):
            self.parent().bar.zoom_dy(dy)
            self.__update_buttons()

        def __update_buttons(self):
            z = self.parent().bar.zoom_y
            self.__b_zoom_in.setEnabled(z < 1000)
            self.__b_zoom_0.setEnabled(z > 1)
            self.__b_zoom_out.setEnabled(z > 1)

    class VLine(QFrame):
        __oscwin: 'ComtradeWidget'

        def __init__(self, oscwin: 'ComtradeWidget'):
            super().__init__()
            self.__oscwin = oscwin
            self.setGeometry(QRect(0, 0, 0, 0))  # size is not the matter
            self.setFrameShape(QFrame.VLine)
            self.setCursor(Qt.SplitHCursor)

        def mouseMoveEvent(self, event: QMouseEvent):
            """accepted() == True, x() = Δx."""
            self.__oscwin.resize_col_ctrl(event.x())

    bar: 'SignalBar'
    anc: Anchor
    lst: SignalLabelList
    zbx: ZoomButtonBox

    def __init__(self, bar: 'SignalBar'):
        super().__init__()  # parent will be QWidget
        self.bar = bar
        self.anc = self.Anchor(self)
        self.lst = self.SignalLabelList(self)
        self.zbx = self.ZoomButtonBox(self)
        # layout
        layout = QGridLayout()
        layout.addWidget(self.anc, 0, 0)
        layout.addWidget(self.lst, 0, 1)
        layout.addWidget(self.zbx, 0, 2)
        layout.addWidget(self.VLine(self.bar.table.oscwin), 0, 3)
        layout.addWidget(HLine(self), 1, 0, 1, -1)
        self.setLayout(layout)
        self.layout().setContentsMargins(QMargins())
        self.layout().setSpacing(0)

    def sig_add(self, ss: 'SignalSuit') -> Union[StatusSignalLabel, AnalogSignalLabel]:
        return StatusSignalLabel(ss, self.lst) if ss.signal.is_bool else AnalogSignalLabel(ss, self.lst)

    def sig_del(self, i: int):
        self.lst.takeItem(i)
