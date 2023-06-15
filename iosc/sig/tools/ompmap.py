"""OMP map."""
# 1. std
import json
import pathlib
from typing import Union, List, Tuple, Dict
# 2. 3rd
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QComboBox, QDialogButtonBox, QFrame, QVBoxLayout, QHBoxLayout
# x. const
CORR_SIG = ('Ua', 'Ub', 'Uc', 'Ia', 'Ib', 'Ic')
OUT_NAME = ('uasc', 'ubsc', 'ucsc', 'iasc', 'ibsc', 'icsc', 'uapr', 'iapr')
OUT_NAME2 = (
    ('uassc', 'ubssc', 'ucssc', 'iassc', 'ibssc', 'icssc', 'uaspr', 'iaspr'),
    ('uarsc', 'ubrsc', 'ucrsc', 'iarsc', 'ibrsc', 'icrsc', 'uarpr', 'iarpr'),
)
HRM1_NUMBER = 3  # FIXME: hardcoded


class SignalBox(QComboBox):
    """Signal selector."""

    __side: int
    __no: int
    __parent: 'OMPMapWindow'
    signal_idx_chgd = pyqtSignal(int, int, int)

    def __init__(self, side: int, no: int, parent: 'OMPMapWindow'):
        """Init SignalBox object."""
        super().__init__(parent)
        self.__side = side
        self.__no = no
        self.__parent = parent
        self.addItem('')
        self.setItemData(0, -1)
        for i, ss in enumerate(parent.oscwin.ass_list):
            self.addItem(ss.sid)
            self.setItemData(self.count() - 1, i)
        self.currentIndexChanged.connect(self.__slot_idx_chgd)

    def __slot_idx_chgd(self, idx: int):
        self.signal_idx_chgd.emit(self.__side, self.__no, self.itemData(idx))


class OMPMapWindow(QDialog):
    """OMP map window."""

    oscwin: 'ComtradeWidget'  # noqa: F821
    __mode: QComboBox
    __side: Tuple[QFrame, QFrame]
    __button_box: QDialogButtonBox
    __map: Tuple[List[int], List[int]]  # map itself
    exec_1: bool  # Indicates 1st exec_
    ROW_HEAD: Tuple[str, ...]
    COL_LEFT: Tuple[Tuple[str, ...], Tuple[str, ...]]
    COL_RIGHT: Tuple[str, ...]

    def __init__(self, parent: 'ComtradeWidget'):  # noqa: F821
        """Init OMPMapWindow object."""
        super().__init__(parent)
        self.ROW_HEAD = (self.tr("OMP signal"), self.tr("Osc. signal"), self.tr("Value"), self.tr("Time"))
        self.COL_LEFT = (
            ('Uas', 'Ubs', 'Ucs', 'Ias', 'Ibs', 'Ics', self.tr("Uas,pr"), self.tr("Ias,pr")),
            ('Uar', 'Ubr', 'Ucr', 'Iar', 'Ibr', 'Icr', self.tr("Uar,pr"), self.tr("Iar,pr"))
        )
        self.COL_RIGHT = (self.tr("SC ptr"), self.tr("SC ptr"), self.tr("SC ptr"), self.tr("SC ptr"),
                          self.tr("SC ptr"), self.tr("SC ptr"), self.tr("PR ptr"), self.tr("PR ptr"))
        self.oscwin = parent
        self.__map = ([-1] * 6, [-1] * 6)
        self.exec_1 = True
        self.setWindowTitle(self.tr("OMP map table"))
        self.__mk_widgets()
        self.__data_autofill()
        self.__slot_mode_chgd(0)
        self.__mode.currentIndexChanged.connect(self.__slot_mode_chgd)
        self.__button_box.accepted.connect(self.accept)
        self.__button_box.rejected.connect(self.reject)
        self.finished.connect(self.__slot_post_close)

    @property
    def is_defined(self) -> bool:
        """:return: True if map fully defined."""
        idx = self.__mode.currentIndex()
        return not ((idx in {0, 2} and -1 in self.__map[0]) or (bool(idx) and -1 in self.__map[1]))

    def __mk_widgets(self):
        self.__side = (QFrame(self), QFrame(self))
        lt0 = QVBoxLayout()  # global
        # 0. Mode selector
        lt1 = QHBoxLayout()
        lt1.addWidget(QLabel(self.tr("Outlook side")))
        self.__mode = QComboBox(self)
        self.__mode.addItems(('S', 'R', 'S+R'))
        lt1.addWidget(self.__mode)
        lt1.addStretch()
        lt0.addLayout(lt1)
        # 2. Map panels
        lt2 = QHBoxLayout()
        for i in range(2):
            lt = QGridLayout()
            # 1. top head
            for c, s in enumerate(self.ROW_HEAD):
                lt.addWidget(QLabel(s), 0, c)
            # 2. body
            for r in range(6):
                lt.addWidget(QLabel(self.COL_LEFT[i][r]), r + 1, 0)
                lt.addWidget(sb := SignalBox(i, r, self), r + 1, 1)
                lt.addWidget(QLabel(), r + 1, 2)
                lt.addWidget(QLabel(self.COL_RIGHT[r]), r + 1, 3)
                sb.signal_idx_chgd.connect(self.__slot_chg_signal)
            # 3. footnote
            for r in range(6, 8):
                lt.addWidget(QLabel(self.COL_LEFT[i][r]), r + 1, 0)
                lt.addWidget(QLabel(), r + 1, 1)
                lt.addWidget(QLabel(), r + 1, 2)
                lt.addWidget(QLabel(self.COL_RIGHT[r]), r + 1, 3)
            self.__side[i].setLayout(lt)
            lt2.addWidget(self.__side[i])
        lt0.addLayout(lt2)
        # the end
        self.__button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lt0.addWidget(self.__button_box)
        self.setLayout(lt0)

    def __get_rc_widget(self, s: int, r: int, c: int) -> Union[SignalBox, QLabel]:
        """Get widget in row/col position.

        :param s: Side
        :param r: Row
        :param c: Column
        :return: Widget at position(r,c)
        """
        return self.__side[s].layout().itemAtPosition(r, c).widget()

    def __data_autofill(self):
        """Find corresponding signals."""
        for s in range(2):
            for r, lbl in enumerate(CORR_SIG):
                if (idx := self.oscwin.osc.find_signal(lbl)) is not None:
                    self.__get_rc_widget(s, r + 1, 1).setCurrentIndex(idx + 1)

    def __data_store(self):
        for s in range(2):
            for i in range(len(self.__map[s])):
                self.__map[s][i] = self.__get_rc_widget(s, i + 1, 1).currentIndex() - 1

    def __data_restore(self):
        for s in range(2):
            for i in range(len(self.__map[s])):
                self.__get_rc_widget(s, i + 1, 1).setCurrentIndex(self.__map[s][i] + 1)

    def __h1(self, __y_i: int, __i: int) -> complex:
        """Get value of __y_i-th signal in __i-th point.

        Not centered, primary.
        """
        return self.oscwin.osc.y[__y_i].value(__i, False, False, HRM1_NUMBER)

    def __slot_chg_signal(self, side: int, row: int, y_i: int):
        """Change signal values on demand.

        :param row: SignalBox row (from 0)
        :param y_i: Signal no
        """
        def __h1_str(__y_i: int, __i: int) -> str:
            """Get 1st harmonic of signal as string.

            :param __y_i: Number of signal
            :param __i: Number of X-point
            :return: String repr of 1st harmonic y_i-th signal in point Xi
            """
            if __y_i >= 0:
                return self.oscwin.osc.y[__y_i].as_str_full(self.__h1(__y_i, __i))
            else:
                return ''
        self.__get_rc_widget(side, row + 1, 2).setText(__h1_str(y_i, self.oscwin.omp_ptr.i_sc))
        if row in {0, 3}:
            dst_row = 7 if row == 0 else 8
            self.__get_rc_widget(side, dst_row, 1).setText(self.__get_rc_widget(side, row + 1, 1).currentText())
            self.__get_rc_widget(side, dst_row, 2).setText(__h1_str(y_i, self.oscwin.omp_ptr.i_pr))

    def __slot_post_close(self, result: int):
        if result:  # Ok
            self.__data_store()

    def __slot_mode_chgd(self, idx: int):
        """idx=0..2; not calling on start."""
        self.__side[0].setVisible(idx != 1)
        self.__side[1].setVisible(bool(idx))

    def exec_(self) -> int:
        """Open dialog and return result."""
        if self.exec_1:
            self.exec_1 = False
        else:
            self.__data_restore()
        return super().exec_()

    def __uim_to(self) -> Dict[str, Union[int, float]]:
        retvalue: Dict[str, Union[int, float]] = {}
        for s in range(len(self.__map)):
            if s + self.__mode.currentIndex() == 1:
                for n in OUT_NAME2[s]:
                    retvalue[n+'r'] = 0
                    retvalue[n+'i'] = 0
            else:
                data = [self.__h1(self.__map[s][i], self.oscwin.omp_ptr.i_sc) for i in range(len(self.__map[s]))]
                data.append(self.__h1(self.__map[s][0], self.oscwin.omp_ptr.i_pr))
                data.append(self.__h1(self.__map[s][3], self.oscwin.omp_ptr.i_pr))
                for i, d in enumerate(data):
                    retvalue[OUT_NAME2[s][i] + 'r'] = data[i].real
                    retvalue[OUT_NAME2[s][i] + 'i'] = data[i].imag
        return retvalue

    def __uim_from(self, data: Dict[str, Dict[str, float]]):
        ...

    def data_save(self, fn: pathlib.Path):
        """Save OMP values into *.uim file."""
        out_obj = self.__uim_to()
        with open(fn, 'wt') as fp:
            json.dump(out_obj, fp, indent=1)

    def ofd_to(self) -> Dict[str, List[int]]:
        """Convert OMP map to OFD-file compliant data ({sections: [signal numbers]})."""
        retvalue = {}
        for s, name in enumerate(('s', 'r')):
            if s + self.__mode.currentIndex() == 1:
                continue
            retvalue[name] = self.__map[s]
        return retvalue

    def ofd_from(self, data: Dict[str, List[int]]):
        """Reload OMP map from OFD-file compliant data."""
        self.__map = ([-1] * 6, [-1] * 6)
        for s, name in enumerate(('s', 'r')):
            if name not in data:
                continue
            for i, j in enumerate(data[name]):
                self.__map[s][i] = j
        # set mode selector
        if 's' in data:
            if 'r' in data:
                _mode = 2
            else:
                _mode = 0
        else:
            _mode = 1
        self.__mode.setCurrentIndex(_mode)
