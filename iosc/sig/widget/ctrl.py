"""Contorl (left) side of signal bars."""
# 1. std
from typing import Union, TypeAlias
# 2. Std
from PyQt5.QtCore import QMargins, Qt, QPoint, QRect, QMimeData
from PyQt5.QtGui import QBrush, QMouseEvent, QPixmap, QFontMetrics, QPainter, QPen, QDrag
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QVBoxLayout, QMenu, QListWidget, QListWidgetItem, QFrame, \
    QGridLayout
# 3. local
import iosc.const
from iosc.sig.widget.hline import HLine


class __SignalLabel(QListWidgetItem):
    """Base signal label class."""

    ss: Union['StatusSignalSuit', 'AnalogSignalSuit']  # noqa: F821
    # signal_restyled = pyqtSignal()  # N/A

    def __init__(self, ss: Union['StatusSignalSuit', 'AnalogSignalSuit'], parent: 'BarCtrlWidget.SignalLabelList' = None):  # noqa: F821
        """Init SignalLabel object."""
        super().__init__(parent)
        self.ss = ss
        # self._set_style()
        self.slot_update_value()
        self.ss.bar.table.oscwin.signal_ptr_moved_main.connect(self.slot_update_value)

    @property
    def _value_str(self) -> str:
        return self.ss.sig2str_i(self.ss.bar.table.oscwin.main_ptr_i)

    def set_color(self):
        """Update signal label color."""
        self.setForeground(QBrush(self.ss.color))

    def slot_update_value(self):
        """Update ctrl widget value."""
        self.setText("%s\n%s" % (self.ss.sid, self._value_str))


class StatusSignalLabel(__SignalLabel):
    """B-signal label."""

    def __init__(self, ss: 'StatusSignalSuit', parent: 'BarCtrlWidget.SignalLabelList' = None):  # noqa: F821
        """Init StatusSignalLabel object."""
        super().__init__(ss, parent)


class AnalogSignalLabel(__SignalLabel):
    """A-signal label."""

    def __init__(self, ss: 'AnalogSignalSuit', parent: 'BarCtrlWidget.SignalLabelList' = None):  # noqa: F821
        """Init AnalogSignalLabel object."""
        super().__init__(ss, parent)
        self.ss.bar.table.oscwin.signal_chged_pors.connect(self.slot_update_value)
        self.ss.bar.table.oscwin.signal_chged_func.connect(self.slot_update_value)


ABSignalLabel: TypeAlias = Union[AnalogSignalLabel, StatusSignalLabel]


class BarCtrlWidget(QWidget):
    """Control (left) signal bar widget container."""

    class Anchor(QLabel):
        """Anchor widget to move bar."""

        def __init__(self, parent: 'BarCtrlWidget'):
            """Init Anchor object."""
            super().__init__(parent)
            self.setText('↕')
            self.setCursor(Qt.PointingHandCursor)

        def mousePressEvent(self, _: QMouseEvent):
            """Inherited."""
            self.__start_drag()

        def __start_drag(self):
            def _mk_icon() -> QPixmap:
                __txt = self.parent().bar.signals[0].sid
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
                bar: 'HDBar' = self.parent().bar  # noqa: F821
                return bar.table.mimeData([bar.table.item(bar.row, 0)])

            drag = QDrag(self)
            drag.setPixmap(_mk_icon())
            drag.setMimeData(_mk_mime())
            # drag.setHotSpot(event.pos())
            drag.exec_(Qt.MoveAction, Qt.MoveAction)

    class SignalLabelList(QListWidget):
        """Signal label."""

        def __init__(self, parent: 'BarCtrlWidget'):
            """Init SignalLabelList object."""
            super().__init__(parent)
            self.setDragEnabled(True)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollMode(self.ScrollPerPixel)
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.__slot_context_menu)
            self.itemClicked.connect(self.__slot_item_clicked)

        def __slot_item_clicked(self, _):
            """Deselect item on mouse up."""
            self.clearSelection()

        def __slot_context_menu(self, point: QPoint):
            self.clearSelection()
            item: ABSignalLabel = self.itemAt(point)
            if not item:
                return
            context_menu = QMenu()
            action_sig_property = context_menu.addAction(self.tr("Properties..."))
            action_sig_hide = context_menu.addAction(self.tr("Hide"))
            chosen_action = context_menu.exec_(self.mapToGlobal(point))
            if chosen_action == action_sig_property:
                item.ss.do_sig_property()
            elif chosen_action == action_sig_hide:
                item.ss.hidden = True

        @property
        def selected_row(self) -> int:
            """:return: Signal label index selected."""
            return self.selectedIndexes()[0].row()

        def startDrag(self, supported_actions: Union[Qt.DropActions, Qt.DropAction]):
            """Imherited."""
            def _mk_icon() -> QPixmap:
                __txt = self.currentItem().ss.sid
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
            self.clearSelection()

    class ZoomButtonBox(QWidget):
        """Bar Y-zoom buttons container."""

        class ZoomButton(QPushButton):
            """Bar Y-zoom button."""

            def __init__(self, txt: str, parent: 'ZoomButtonBox'):  # noqa: F821
                """Init ZoomButton object."""
                super().__init__(txt, parent)
                self.setContentsMargins(QMargins())  # not helps
                self.setFixedWidth(16)
                self.setFlat(True)
                self.setCursor(Qt.PointingHandCursor)

        __b_zoom_in: ZoomButton
        __b_zoom_0: ZoomButton
        __b_zoom_out: ZoomButton

        def __init__(self, parent: 'BarCtrlWidget'):
            """Init ZoomButtonBox object."""
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
        """Vertical line - anchor for column width changing."""

        __oscwin: 'ComtradeWidget'  # noqa: F821

        def __init__(self, oscwin: 'ComtradeWidget'):  # noqa: F821
            """Init VLine object."""
            super().__init__()
            self.__oscwin = oscwin
            self.setGeometry(QRect(0, 0, 0, 0))  # size is not the matter
            self.setFrameShape(QFrame.VLine)
            self.setCursor(Qt.SplitHCursor)
            self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        def mouseMoveEvent(self, event: QMouseEvent):
            """Inherited.

            accepted() == True, x() = Δx.
            """
            self.__oscwin.resize_col_ctrl(event.x())

    bar: 'HDBar'  # noqa: F821
    anc: Anchor
    lst: SignalLabelList
    zbx: ZoomButtonBox
    hline: HLine

    def __init__(self, bar: 'HDBar'):  # noqa: F821
        """Init BarCtrlWidget object."""
        super().__init__()  # parent will be QWidget
        self.bar = bar
        self.anc = self.Anchor(self)
        self.lst = self.SignalLabelList(self)
        self.zbx = self.ZoomButtonBox(self)
        self.hline = HLine(self)
        # layout
        layout = QGridLayout()
        layout.addWidget(self.anc, 0, 0)
        layout.addWidget(self.lst, 0, 1)
        layout.addWidget(self.zbx, 0, 2)
        layout.addWidget(self.VLine(self.bar.table.oscwin), 0, 3)
        layout.addWidget(self.hline, 1, 0, 1, -1)
        self.setLayout(layout)
        self.layout().setContentsMargins(QMargins())
        self.layout().setSpacing(0)

    def sig_add(self, ss: 'SignalSuit') -> ABSignalLabel:  # noqa: F821
        """Add signal suit."""
        return StatusSignalLabel(ss, self.lst) if ss.is_bool else AnalogSignalLabel(ss, self.lst)

    def sig_del(self, i: int):
        """Del signal suit."""
        self.lst.takeItem(i)

    def update_statusonly(self):
        """Update some things depending on if bar is status-only.

        I.e.:
        - Y-zoom buttons
        - Y-resize widget
        """
        self.zbx.setEnabled(not self.bar.is_bool())
        self.hline.setEnabled(not self.bar.is_bool())
