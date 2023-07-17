from typing import List, Optional, Tuple

from PyQt5.QtWidgets import QDialog, QComboBox, QDialogButtonBox, QGridLayout, QLabel

from iosc.sig.mainwidget import ComtradeWidget


class OMPSaveDialog(QDialog):
    """
    - Collect lefts, rights, boths
    - Prepare x4 listboxes
    - call select s/r dialog
    - call QFileDialog
    - do it
    :return: ([S-osc], [R-osc])
    :todo: move up
    """
    __ct_list: List = []
    __mode: QComboBox
    __side_s: QComboBox
    __side_r: QComboBox
    __side_sr: QComboBox
    __side_r_x: QComboBox
    __label_s: QLabel
    __label_r: QLabel
    button_box: QDialogButtonBox

    def __init__(self, parent=None):
        super().__init__(parent)
        # 2. set widgets
        self.__mode = QComboBox()
        self.__mode.addItems(('S', 'R', 'S+R', 'S,R'))
        self.__side_s = QComboBox()
        self.__side_r = QComboBox()
        self.__side_sr = QComboBox()
        self.__side_r_x = QComboBox()
        self.__label_s = QLabel(self.tr("Oscillogramm:"))
        self.__label_r_x = QLabel(self.tr("R:"))
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        layout = QGridLayout(self)
        layout.addWidget(QLabel(self.tr("Mode:")), 0, 0)
        layout.addWidget(self.__mode, 0, 1)
        layout.addWidget(self.__label_s, 1, 0)
        layout.addWidget(self.__side_s, 1, 1)
        layout.addWidget(self.__side_r, 1, 1)
        layout.addWidget(self.__side_sr, 1, 1)
        layout.addWidget(self.__label_r_x, 1, 2)
        layout.addWidget(self.__side_r_x, 1, 3)
        layout.addWidget(self.button_box, 2, 0, 1, 4)
        self.setLayout(layout)
        # 4. set signals
        self.__mode.currentIndexChanged.connect(self.__slot_mode_chgd)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 5. go
        self.setWindowTitle(self.tr("Select OMP to save"))

    def execute(self, ct_list: List[ComtradeWidget]) -> Optional[Tuple[Optional[int], Optional[int]]]:
        """Open dialog and return result.
        :return: ([S-osc], [R-osc])
        """
        self.__ct_list = ct_list
        self.__side_s.clear()
        self.__side_r.clear()
        self.__side_sr.clear()
        for i, ct in enumerate(ct_list):
            defined = ct.ompmapwin.is_defined  # 0..3
            if defined & 1:
                self.__side_s.addItem(ct.osc.path.name, i)
            if defined & 2:
                self.__side_r.addItem(ct.osc.path.name, i)
                self.__side_r_x.addItem(ct.osc.path.name, i)
            if defined == 3:
                self.__side_sr.addItem(ct.osc.path.name, i)
        self.__slot_mode_chgd(self.__mode.currentIndex())
        if self.exec_():
            return 0, 0

    def __slot_mode_chgd(self, idx: int):
        """
        - Show/hide labels and comboboxes
        - Enable/disable 'OK'
        :param idx:
        :return:
        """
        self.__side_s.setVisible(idx in (0, 3))
        self.__side_r.setVisible(idx == 1)
        self.__side_sr.setVisible(idx == 2)
        self.__side_r_x.setVisible(idx == 3)
        self.__label_r_x.setVisible(idx == 3)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(
            (idx == 0 and self.__side_s.currentIndex() > -1) or
            (idx == 1 and self.__side_r.currentIndex() > -1) or
            (idx == 2 and self.__side_sr.currentIndex() > -1) or
            (idx == 3 and self.__side_s.currentIndex() > -1 and self.__side_r_x.currentIndex() > -1)
        )
