from typing import List

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QComboBox, QDialogButtonBox

from iosc.sig.widget.common import AnalogSignalSuit

ROW_HEAD = ("OMP signal", "Osc. signal", "Value", "Time")
COL_LEFT = ("Ua", "Ub", "Uc", "Ia", "Ib", "Ic", "Ua,pr", "Ia,pr")
COL_RIGHT = ("SC ptr", "SC ptr", "SC ptr", "SC ptr", "SC ptr", "SC ptr", "PR ptr", "PR ptr")
CORR_SIG = ('Ua', 'Ub', 'Uc', 'Ia', 'Ib', 'Ic', 'Ua', 'Ia')


class SignalBox(QComboBox):
    ss:
    def __init__(self, ass_list: List[AnalogSignalSuit], v: str):
        super().__init__()
        for ss in ass_list:
            self.addItem(ss.signal.sid)
            if v in ss.signal.sid:
                self.setCurrentIndex(self.count() - 1)
            # TODO: add data (signal no, signal itself)


class OMPMapWindow(QDialog):
    button_box: QDialogButtonBox

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.setWindowTitle("OMP Map")
        self.__mk_widgets(parent.ass_list)
        self.__load_data()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def __mk_widgets(self, ass_list: List[AnalogSignalSuit]):
        lt = QGridLayout()
        # 1. top head
        for c, s in enumerate(ROW_HEAD):
            lt.addWidget(QLabel(s), 0, c)
        # the end
        for r in range(8):
            lt.addWidget(QLabel(COL_LEFT[r]), r + 1, 0)
            lt.addWidget(SignalBox(ass_list, CORR_SIG[r]), r + 1, 1)
            lt.addWidget(QLabel(), r + 1, 2)
            lt.addWidget(QLabel(COL_RIGHT[r]), r + 1, 3)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.setLayout(lt)

    def __load_data(self):
        """Find correspondent signals"""
        for r, lbl in enumerate(CORR_SIG):
            ...
            # find
            # set combobox index
