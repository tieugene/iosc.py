from typing import List

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QComboBox, QDialogButtonBox

from iosc.sig.widget.common import AnalogSignalSuit

ROW_HEAD = ("OMP signal", "Osc. signal", "Value", "Time")
COL_LEFT = ("Ua", "Ub", "Uc", "Ia", "Ib", "Ic", "Ua,pr", "Ia,pr")
COL_RIGHT = ("SC ptr", "SC ptr", "SC ptr", "SC ptr", "SC ptr", "SC ptr", "PR ptr", "PR ptr")
CORR_SIG = ('Ua', 'Ub', 'Uc', 'Ia', 'Ib', 'Ic', 'Ua', 'Ia')


class SignalBox(QComboBox):
    __buddy: QLabel
    __parent: 'OMPMapWindow'

    def __init__(self, buddy: QLabel, v: str, parent: 'OMPMapWindow'):
        super().__init__(parent)
        self.__buddy = buddy
        self.__parent = parent
        idx = None
        for ss in parent.oscwin.ass_list:
            self.addItem(ss.signal.sid)
            if v in ss.signal.sid:
                idx = self.count() - 1
                self.setCurrentIndex(idx)
            # TODO: add data (signal no, signal itself)
        if idx is not None:
            self.__slot_update_buddy(idx)
        self.currentIndexChanged.connect(self.__slot_update_buddy)

    def __slot_update_buddy(self, idx: int):
        self.__buddy.setText(self.itemText(idx))


class OMPMapWindow(QDialog):
    oscwin: 'ComtradeWidget'
    button_box: QDialogButtonBox

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.oscwin = parent
        self.setWindowTitle("OMP Map")
        self.__mk_widgets()
        self.__load_data()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def __mk_widgets(self):
        lt = QGridLayout()
        # 1. top head
        for c, s in enumerate(ROW_HEAD):
            lt.addWidget(QLabel(s), 0, c)
        # the end
        for r in range(8):
            lt.addWidget(QLabel(COL_LEFT[r]), r + 1, 0)
            lt.addWidget(buddy := QLabel(), r + 1, 2)
            lt.addWidget(SignalBox(buddy, CORR_SIG[r], self), r + 1, 1)
            lt.addWidget(QLabel(COL_RIGHT[r]), r + 1, 3)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.setLayout(lt)

    def __load_data(self):
        """Find correspondent signals"""
        for r, lbl in enumerate(CORR_SIG):
            ...
            # find
            # set combobox index
