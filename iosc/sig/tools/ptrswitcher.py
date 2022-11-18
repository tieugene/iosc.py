from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QActionGroup, QToolButton, QMenu, QAction

from iosc.sig.tools.cvdobject import CVDiagramObject


class PtrSwitcher(QActionGroup):
    tb: QToolButton

    def __init__(self, parent: 'CVDiagramObject'):
        super().__init__(parent)
        self.tb = QToolButton(parent)
        self.tb.setPopupMode(QToolButton.MenuButtonPopup)
        self.tb.setMenu(QMenu())
        # Main ptr
        a0 = QAction(QIcon.fromTheme("go-jump"), "Main", parent, checkable=True)
        a0.setData(0)
        a0.setChecked(True)
        self.addAction(a0)
        self.tb.menu().addAction(a0)
        self.tb.setDefaultAction(a0)
        # tmp ptrs
        for uid in parent.parent().tmp_ptr_i.keys():
            self.__slot_add(uid)
        # connections
        self.triggered.connect(self.__slot_switch)
        parent.parent().signal_ptr_add_tmp.connect(self.__slot_add)
        parent.parent().signal_ptr_del_tmp.connect(self.__slot_del)

    def __slot_switch(self, a: QAction):
        self.tb.setDefaultAction(a)
        self.parent().slot_ptr_switch(a.data())

    def __slot_add(self, uid: int):
        a = self.addAction(QAction(f"T{uid}", self.parent(), checkable=True))
        a.setData(uid)
        self.tb.menu().addAction(a)

    def __slot_del(self, uid: int):
        reset: bool = False
        for a in self.actions():
            if a.data() == uid:
                reset = a.isChecked()
                self.removeAction(a)
        if reset:
            self.actions()[0].setChecked(True)
            self.__slot_switch(self.actions()[0])
