# 1. std
from typing import List, Union
# 2. 3rd
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QComboBox, QDialogButtonBox
# 3. local
from iosc.core.sigfunc import hrm1
# x. const
ROW_HEAD = ("OMP signal", "Osc. signal", "Value", "Time")
COL_LEFT = ("Ua", "Ub", "Uc", "Ia", "Ib", "Ic", "Ua,pr", "Ia,pr")
COL_RIGHT = ("SC ptr", "SC ptr", "SC ptr", "SC ptr", "SC ptr", "SC ptr", "PR ptr", "PR ptr")
CORR_SIG = ('Ua', 'Ub', 'Uc', 'Ia', 'Ib', 'Ic')


class SignalBox(QComboBox):
    __no: int
    __parent: 'OMPMapWindow'
    signal_idx_chgd = pyqtSignal(int, int)

    def __init__(self, no: int, parent: 'OMPMapWindow'):
        super().__init__(parent)
        self.__no = no
        self.__parent = parent
        # TODO: add empty
        for i, ss in enumerate(parent.oscwin.ass_list):
            self.addItem(ss.signal.sid)
            self.setItemData(self.count() - 1, i)
        self.currentIndexChanged.connect(self.__slot_idx_chgd)

    def __slot_idx_chgd(self, idx: int):
        self.signal_idx_chgd.emit(self.__no, self.itemData(idx))


class OMPMapWindow(QDialog):
    oscwin: 'ComtradeWidget'
    button_box: QDialogButtonBox

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.oscwin = parent
        self.setWindowTitle("OMP Map")
        self.__mk_widgets()
        self.__set_data()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def __mk_widgets(self):
        lt = QGridLayout()
        # 1. top head
        for c, s in enumerate(ROW_HEAD):
            lt.addWidget(QLabel(s), 0, c)
        # 2. body
        for r in range(6):
            lt.addWidget(QLabel(COL_LEFT[r]), r + 1, 0)
            lt.addWidget(sb := SignalBox(r, self), r + 1, 1)
            lt.addWidget(QLabel(), r + 1, 2)
            lt.addWidget(QLabel(COL_RIGHT[r]), r + 1, 3)
            sb.signal_idx_chgd.connect(self.__slot_chg_signal)
        # 3. footnote
        for r in range(6, 8):
            lt.addWidget(QLabel(COL_LEFT[r]), r + 1, 0)
            lt.addWidget(QLabel(), r + 1, 1)
            lt.addWidget(QLabel(), r + 1, 2)
            lt.addWidget(QLabel(COL_RIGHT[r]), r + 1, 3)
        # the end
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.setLayout(lt)

    def __get_rc_widget(self, r: int, c: int) -> Union[SignalBox, QLabel]:
        """
        :param r: Row
        :param c: Column
        :return: Widget at position(r,c)
        """
        return self.layout().itemAtPosition(r, c).widget()

    def __set_data(self):
        """Find correspondent signals"""
        for r, lbl in enumerate(CORR_SIG):
            if (idx := self.oscwin.osc.find_signal(lbl)) is not None:
                self.__get_rc_widget(r + 1, 1).setCurrentIndex(idx)  # TODO: add empty

    def __slot_chg_signal(self, row: int, y_i: int):
        """
        :param row: SignalBox row (from 0)
        :param y_i: Signal no
        :return:
        """
        def __h1(__i: int):
            v = hrm1(self.oscwin.osc.y[y_i].value, __i, self.oscwin.osc.spp)
            return self.oscwin.osc.y[y_i].as_str_full(v, self.oscwin.show_sec)
        self.__get_rc_widget(row + 1, 2).setText(__h1(self.oscwin.sc_ptr_i))
        if row in {0, 3}:
            dst_row = 7 if row == 0 else 8
            self.__get_rc_widget(dst_row, 1).setText(self.oscwin.osc.y[y_i].sid)
            i = self.oscwin.sc_ptr_i + self.oscwin.osc.spp * self.oscwin.omp_width  # x_i of PR ptr
            self.__get_rc_widget(dst_row, 2).setText(__h1(i))
