"""Circular Vector Diagram (CVD). Main window."""
# 1. std
import cmath
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QAction, QVBoxLayout, QToolBar, QSplitter, QWidget, QSizePolicy
# 3. local
from iosc.sig.tools.cvdtable import CVDTable
from iosc.sig.tools.cvdwidget import CVDiagramView
from iosc.sig.tools.ptrswitcher import PtrSwitcher
from iosc.sig.widget.sigsuit import AnalogSignalSuit
from iosc.sig.tools.cvddialog import SelectCVDSignalsDialog


class CVDWindow(QDialog):
    """Main CVD window."""

    __ptr_uid: int
    __i: int
    __ass_list: list[AnalogSignalSuit]  # just shortcut
    ss_used: list[AnalogSignalSuit]
    ss_base: AnalogSignalSuit
    toolbar: QToolBar
    chart: CVDiagramView
    table: CVDTable
    action_settings: QAction
    action_ptr: PtrSwitcher
    action_close: QAction

    def __init__(self, parent: 'ComtradeWidget'):  # noqa: F821
        """Init CVDWindow object."""
        super().__init__(parent)
        self.__ptr_uid = 0  # MainPtr
        self.__i = parent.main_ptr_i
        self.__ass_list = parent.ass_list
        self.ss_used = list()
        self.ss_base = parent.ass_list[0]
        self.__mk_widgets()
        self.__mk_layout()
        self.__mk_actions()
        self.__mk_toolbar()
        self.setWindowTitle("Vector Diagram")
        self.setWindowModality(Qt.WindowModality.NonModal)
        # self.setWindowFlag(Qt.Dialog)
        parent.signal_ptr_moved_main.connect(self.__slot_ptr_moved_main)
        parent.signal_ptr_moved_tmp.connect(self.__slot_ptr_moved_tmp)
        self.finished.connect(self.__slot_post_close)

    @property
    def t_i(self):
        """:return: Current MainPtr.i."""
        return self.__i

    def get_base_angle(self) -> float:
        """:return: Base angle (of base signal)."""
        return cmath.phase(self.ss_base.hrm(1, self.t_i))

    def __mk_widgets(self):
        self.toolbar = QToolBar(self)
        self.chart = CVDiagramView(self)
        self.table = CVDTable(self)

    def __mk_layout(self):
        """Lay out child widgets.

        They are:
        - toolbar
        - plot
        - table
        """
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        splitter.addWidget(self.chart)
        splitter.addWidget(self.table)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(splitter)

    def __mk_actions(self):
        # noinspection PyArgumentList
        self.action_settings = QAction(QIcon.fromTheme("document-properties"),
                                       "&Select signals",
                                       self,
                                       shortcut="Ctrl+S",
                                       triggered=self.__do_settings)
        # noinspection PyArgumentList
        self.action_close = QAction(QIcon.fromTheme("window-close"),
                                    "&Close",
                                    self,
                                    shortcut="Ctrl+V",
                                    triggered=self.close)
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
        ss_used_i = set([ss.i for ss in self.ss_used])  # WARN: works if ss.signal.i <=> self.__ass_list[i]
        ss_base_i = self.ss_base.i
        retvalue = SelectCVDSignalsDialog(self.__ass_list, ss_used_i, ss_base_i).execute()
        if retvalue is not None:
            self.ss_used.clear()
            self.ss_used = [self.__ass_list[i] for i in retvalue[0]]
            self.ss_base = self.__ass_list[retvalue[1]]
            self.chart.reload_signals()
            self.table.reload_signals()

    def __slot_ptr_moved(self, i: int):
        self.__i = i
        self.chart.refresh_signals()
        self.table.refresh_signals()

    def __slot_ptr_moved_main(self, i: int):
        if self.__ptr_uid == 0:
            self.__slot_ptr_moved(i)  # Plan B: get from parent

    def __slot_ptr_moved_tmp(self, uid: int, i: int):
        if self.__ptr_uid == uid:
            self.__slot_ptr_moved(i)  # Plan B: get from parent

    def slot_ptr_switch(self, uid: int):
        """Switch between pointers."""
        if uid != self.__ptr_uid:  # skip if not changed
            self.__ptr_uid = uid
            self.__slot_ptr_moved(self.parent().tmp_ptr_i[uid] if uid else self.parent().main_ptr_i)

    def __slot_post_close(self):
        self.parent().action_vector_diagram.setEnabled(True)
