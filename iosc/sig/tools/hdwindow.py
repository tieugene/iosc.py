"""Harminic Diagram (HD).
Main window."""
from typing import Optional

# 1. std
# 2. 3rd
from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtGui import QIcon, QColor, QFont
from PyQt5.QtWidgets import QDialog, QToolBar, QAction, QScrollArea, QVBoxLayout, QWidget, QSizePolicy, QLabel, \
    QHBoxLayout, QFrame
# 3. local
from iosc.sig.tools.ptrswitcher import PtrSwitcher
from iosc.sig.widget.common import AnalogSignalSuit
from iosc.sig.widget.dialog import SelectSignalsDialog
# x. const
FONT_STD = QFont('mono', 8)
WIDTH_HRM_TITLE = 75
WIDTH_HRM_LEGEND = 35
HRM_VAL = (100, 50, 25, 12, 6, 3, 1, 0)


def color2style(c: QColor) -> str:
    """Convert QColor into stylesheet-compatible string"""
    return "rgb(%d, %d, %d)" % (c.red(), c.green(), c.blue())


class SignalHarmBar(QWidget):
    class _Text(QWidget):
        subj: QLabel

        def __init__(self, parent: 'SignalHarmBar'):
            super().__init__(parent)
            self.subj = QLabel(self)
            self.subj.setFont(FONT_STD)
            self.setLayout(QHBoxLayout())
            self.layout().setContentsMargins(QMargins())
            self.layout().setSpacing(0)
            self.layout().addWidget(self.subj)

        def set_text(self, text: str):
            self.subj.setText(text)

    class _Space(QFrame):
        def __init__(self, parent: 'SignalHarmBar', color: Optional[QColor] = None):
            super().__init__(parent)
            if color:
                self.set_color(color)

        def set_color(self, color: QColor):
            self.setStyleSheet("background-color: %s" % color2style(color))

    title: _Text
    indic: _Space
    legend: _Text
    pad: _Space
    """One harmonic row"""
    def __init__(self, ss: AnalogSignalSuit, hrm_no: int, parent: 'SignalBar'):
        """
        :param ss: Signal about
        :param hrm_no: Harmonic order number (1..5)
        :param parent: Subj
        """
        super().__init__(parent)
        # self.setStyleSheet("border: 1px dotted black")
        self.setLayout(QHBoxLayout())
        # 1. mk widgets
        # - title
        self.title = self._Text(self)
        self.title.setFixedWidth(WIDTH_HRM_TITLE)
        self.title.set_text(f"{hrm_no}: {hrm_no * 50} Гц")
        self.layout().addWidget(self.title)
        self.layout().setStretchFactor(self.title, 0)
        # - indicator
        self.indic = self._Space(self, ss.color)
        self.layout().addWidget(self.indic)
        # self.layout().setStretchFactor(self.indic, val)  # TODO:
        # - percentage
        self.legend = self._Text(self)
        self.layout().addWidget(self.legend)
        self.title.setFixedWidth(WIDTH_HRM_LEGEND)
        # set value
        # self.layout().setStretchFactor(self.legend, 0)
        # - pad
        self.indic = self._Space(self)
        self.layout().addWidget(self.indic)
        # self.layout().setStretchFactor(self.indic, 100 - val)


class SignalTitleBar(QWidget):
    def __init__(self, text: str, color: QColor, parent: 'SignalBar'):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(QLabel(text, self))
        self.layout().addStretch(0)
        self.setStyleSheet("background-color: %s" % color2style(color))

    def set_color(self, color: QColor):
        ...


class SignalBar(QWidget):
    """One signal's row."""
    title: SignalTitleBar
    harm: list[SignalHarmBar]

    def __init__(self, ss: AnalogSignalSuit, parent: 'HDTable'):
        super().__init__(parent)
        self.title = SignalTitleBar(ss.signal.sid, ss.color, self)
        self.harm = list()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.title)
        for i in (1, 2, 3, 5):
            hrm = SignalHarmBar(ss, i, self)
            self.harm.append(hrm)
            self.layout().addWidget(hrm)


class HDTable(QWidget):
    __parent: 'HDWindow'  # functional parent

    def __init__(self, parent: 'HDWindow'):
        super().__init__(parent)
        self.__parent = parent
        self.setStyleSheet("border: 1px solid red")
        self.setLayout(QVBoxLayout())
        self.layout().addStretch(0)

    def reload_signals(self):
        self.layout().children().clear()
        if self.__parent.ss_used:
            for ss in self.__parent.ss_used:
                self.layout().addWidget(SignalBar(ss, self))
            self.layout().addStretch(0)


class HDWindow(QDialog):
    """Main HD window."""
    __ptr_uid: int
    __i: int
    __ass_list: list[AnalogSignalSuit]  # just shortcut
    ss_used: list[AnalogSignalSuit]
    toolbar: QToolBar
    sa: QScrollArea
    table: HDTable
    action_settings: QAction
    action_ptr: PtrSwitcher
    action_close: QAction

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.__ptr_uid = 0  # MainPtr
        self.__i = parent.main_ptr_i
        self.__ass_list = parent.ass_list
        self.ss_used = list()
        self.__mk_widgets()
        self.__mk_layout()
        self.__mk_actions()
        self.__mk_toolbar()
        self.setWindowTitle("Harmonic Diagram")
        # self.setWindowFlag(Qt.Dialog)

    @property
    def t_i(self):
        """Current MainPtr.i"""
        return self.__i

    def __mk_widgets(self):
        self.toolbar = QToolBar(self)
        self.sa = QScrollArea(self)
        self.table = HDTable(self)

    def __mk_layout(self):
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.sa)
        self.sa.setWidget(self.table)
        self.sa.setWidgetResizable(True)

    def __mk_actions(self):
        self.action_settings = QAction(QIcon.fromTheme("document-properties"),
                                       "&Select signals",
                                       self,
                                       shortcut="Ctrl+S",
                                       triggered=self.__do_settings)
        self.action_close = QAction(QIcon.fromTheme("window-close"),
                                    "&Close",
                                    self,
                                    shortcut="Ctrl+H",
                                    triggered=self.parent().action_harmonic_diagram.trigger)
        self.action_ptr = PtrSwitcher(self)

    def __mk_toolbar(self):
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setVisible(True)
        self.toolbar.addAction(self.action_settings)
        self.toolbar.addWidget(self.action_ptr.tb)
        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(self.action_close)

    def __do_settings(self):
        ss_used_i = set([ss.signal.i for ss in self.ss_used])  # WARN: works if ss.signal.i <=> self.__ass_list[i]
        retvalue = SelectSignalsDialog(self.__ass_list, ss_used_i).execute()
        if retvalue is not None:
            self.ss_used.clear()
            self.ss_used = [self.__ass_list[i] for i in retvalue]
            self.table.reload_signals()

    def __slot_ptr_moved(self, i: int):
        self.__i = i
        self.table.refresh_signals()

    def __slot_ptr_moved_main(self, i: int):
        if self.__ptr_uid == 0:
            self.__slot_ptr_moved(i)  # Plan B: get from parent

    def __slot_ptr_moved_tmp(self, uid: int, i: int):
        if self.__ptr_uid == uid:
            self.__slot_ptr_moved(i)  # Plan B: get from parent

    def slot_ptr_switch(self, uid: int):
        if uid != self.__ptr_uid:  # skip if not changed
            self.__ptr_uid = uid
            self.__slot_ptr_moved(self.parent().tmp_ptr_i[uid] if uid else self.parent().main_ptr_i)
