"""Harminic Diagram (HD).
Main window."""
from typing import Optional

# 1. std
# 2. 3rd
from PyQt5.QtCore import Qt, QMargins, pyqtSignal
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

        def set_color(self, color: QColor):
            self.setStyleSheet("background-color: %s" % color2style(color))

    class _Space(QFrame):
        def __init__(self, parent: 'SignalHarmBar'):
            super().__init__(parent)

        def set_color(self, color: QColor):
            self.setStyleSheet("background-color: %s" % color2style(color))

    h_no: int
    title: _Text
    indic: _Space
    legend: _Text
    pad: _Space
    """One harmonic row"""
    def __init__(self, h_no: int, parent: 'SignalBar'):
        """
        :param h_no: Harmonic number
        :param parent: Subj
        """
        super().__init__(parent)
        self.h_no = h_no
        # self.setStyleSheet("border: 1px dotted black")
        self.setLayout(QHBoxLayout())
        # 1. mk widgets
        # - title
        self.title = self._Text(self)
        self.title.setFixedWidth(WIDTH_HRM_TITLE)
        self.title.set_text(f"{h_no}: {h_no * 50} Гц")  # FIXME: use ss.signal.frequency
        self.layout().addWidget(self.title)
        self.layout().setStretchFactor(self.title, 0)
        # - indicator
        self.indic = self._Space(self)
        self.layout().addWidget(self.indic)
        # - percentage
        self.legend = self._Text(self)
        self.layout().addWidget(self.legend)
        self.title.setFixedWidth(WIDTH_HRM_LEGEND)
        self.layout().setStretchFactor(self.legend, 0)
        # - pad
        self.pad = self._Space(self)
        self.layout().addWidget(self.pad)

    def set_value(self, v: int):
        self.legend.set_text(f"{v}%")
        self.layout().setStretchFactor(self.indic, v)
        self.layout().setStretchFactor(self.pad, 100 - v)

    def set_color(self, color: QColor):
        self.title.set_color(color)
        self.indic.set_color(color)


class SignalTitleBar(QWidget):
    def __init__(self, text: str, color: QColor, parent: 'SignalBar'):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(QLabel(text, self))
        self.layout().addStretch(0)
        self.set_color(color)

    def set_color(self, color: QColor):
        self.setStyleSheet("background-color: %s" % color2style(color))


class SignalBar(QWidget):
    """One signal's row."""
    __ss: AnalogSignalSuit
    title: SignalTitleBar
    harm: list[SignalHarmBar]

    def __init__(self, ss: AnalogSignalSuit, parent: 'HDTable'):
        super().__init__(parent)
        self.__ss = ss
        self.title = SignalTitleBar(ss.signal.sid, ss.color, self)
        self.harm = list()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.title)
        for i in (1, 2, 3, 5):
            hrm = SignalHarmBar(i, self)
            self.harm.append(hrm)
            self.layout().addWidget(hrm)
        parent.hdwin.signal_ptr_moved.connect(self.__slot_ptr_moved)
        ss.signal_chg_color.connect(self.__slot_set_color)

    def __slot_ptr_moved(self, i: int):
        # FIXME: chk h1 = 0
        i = self.parent().hdwin.t_i
        h1 = abs(self.__ss.hrm(1, i))
        self.harm[0].set_value(100)
        self.harm[1].set_value(round(abs(self.__ss.hrm(2, i))/h1 * 100))
        self.harm[2].set_value(round(abs(self.__ss.hrm(3, i))/h1 * 100))
        self.harm[3].set_value(round(abs(self.__ss.hrm(5, i))/h1 * 100))

    def __slot_set_color(self):
        for w in self.layout().children():
            w.set_color(self.__ss.color)


class HDTable(QWidget):
    hdwin: 'HDWindow'  # functional parent

    def __init__(self, parent: 'HDWindow'):
        super().__init__(parent)
        self.hdwin = parent
        self.setStyleSheet("border: 1px solid red")
        self.setLayout(QVBoxLayout())
        # self.layout().addStretch(0)

    def reload_signals(self):
        self.layout().children().clear()
        if self.hdwin.ss_used:
            for ss in self.hdwin.ss_used:
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
    signal_ptr_moved = pyqtSignal(int)

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
        parent.signal_ptr_moved_main.connect(self.__slot_ptr_moved_main)
        parent.signal_ptr_moved_tmp.connect(self.__slot_ptr_moved_tmp)

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
        self.signal_ptr_moved.emit(i)

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
