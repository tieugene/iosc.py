# 1. std
import json
import pathlib
from typing import Union, List, Optional
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
OUT_NAME = ('uasc', 'ubsc', 'ucsc', 'iasc', 'ibsc', 'icsc', 'uapr', 'iapr')


class SignalBox(QComboBox):
    __no: int
    __parent: 'OMPMapWindow'
    signal_idx_chgd = pyqtSignal(int, int)

    def __init__(self, no: int, parent: 'OMPMapWindow'):
        super().__init__(parent)
        self.__no = no
        self.__parent = parent
        self.addItem('')
        self.setItemData(0, -1)
        for i, ss in enumerate(parent.oscwin.ass_list):
            self.addItem(ss.signal.sid)
            self.setItemData(self.count() - 1, i)
        self.currentIndexChanged.connect(self.__slot_idx_chgd)

    def __slot_idx_chgd(self, idx: int):
        self.signal_idx_chgd.emit(self.__no, self.itemData(idx))


class OMPMapWindow(QDialog):
    oscwin: 'ComtradeWidget'
    __button_box: QDialogButtonBox
    __map: List[int]  # map itself
    __exec_1: bool  # Indicates 1st exec_

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.oscwin = parent
        self.__map = [-1] * 6
        self.__exec_1 = True
        self.setWindowTitle("OMP Map")
        self.__mk_widgets()
        self.__data_autofill()
        self.__button_box.accepted.connect(self.accept)
        self.__button_box.rejected.connect(self.reject)
        self.finished.connect(self.__slot_post_close)

    @property
    def map(self) -> List[int]:
        return self.__map

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
        self.__button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lt.addWidget(self.__button_box, 9, 0, 4, 1)
        self.setLayout(lt)

    def __get_rc_widget(self, r: int, c: int) -> Union[SignalBox, QLabel]:
        """
        :param r: Row
        :param c: Column
        :return: Widget at position(r,c)
        """
        return self.layout().itemAtPosition(r, c).widget()

    def __data_autofill(self):
        """Find correspondent signals"""
        for r, lbl in enumerate(CORR_SIG):
            if (idx := self.oscwin.osc.find_signal(lbl)) is not None:
                self.__get_rc_widget(r + 1, 1).setCurrentIndex(idx + 1)

    def __data_store(self):
        for i in range(len(self.__map)):
            self.__map[i] = self.__get_rc_widget(i + 1, 1).currentIndex() - 1

    def __data_restore(self):
        for i in range(len(self.__map)):
            self.__get_rc_widget(i + 1, 1).setCurrentIndex(self.__map[i] + 1)

    def __h1(self, __y_i: int, __i: int) -> complex:
        return hrm1(self.oscwin.osc.y[__y_i].value, __i, self.oscwin.osc.spp)

    def __slot_chg_signal(self, row: int, y_i: int):
        """
        :param row: SignalBox row (from 0)
        :param y_i: Signal no
        :return:
        """
        def __h1_str(__y_i: int, __i: int) -> str:
            """
            :param __y_i: Number of signal
            :param __i: Number of X-point
            :return: String repr of 1st harmonic y_i-th signal in point Xi
            """
            if __y_i >= 0:
                return self.oscwin.osc.y[__y_i].as_str_full(self.__h1(__y_i, __i), self.oscwin.show_sec)
            else:
                return ''
        self.__get_rc_widget(row + 1, 2).setText(__h1_str(y_i, self.oscwin.sc_ptr_i))
        if row in {0, 3}:
            dst_row = 7 if row == 0 else 8
            self.__get_rc_widget(dst_row, 1).setText(self.__get_rc_widget(row + 1, 1).currentText())
            self.__get_rc_widget(dst_row, 2).setText(__h1_str(y_i, self.oscwin.pr_ptr_i))

    def __slot_post_close(self, result: int):
        if result:  # Ok
            self.__data_store()

    def exec_(self) -> int:
        if self.__exec_1:
            self.__exec_1 = False
        else:
            self.__data_restore()
        return super().exec_()

    def data_save(self, fn: pathlib.Path):
        data = [self.__h1(self.__map[i], self.oscwin.sc_ptr_i) for i in range(len(self.__map))]
        data.append(self.__h1(self.__map[0], self.oscwin.pr_ptr_i))
        data.append(self.__h1(self.__map[3], self.oscwin.pr_ptr_i))
        out_obj = {}
        for i, d in enumerate(data):
            out_obj[OUT_NAME[i]+'r'] = data[i].real
            out_obj[OUT_NAME[i]+'i'] = data[i].imag
        with open(fn, 'wt') as fp:
            json.dump(out_obj, fp, indent=1)
