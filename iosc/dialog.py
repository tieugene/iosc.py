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
    button_box: QDialogButtonBox

    def __init__(self, parent=None):
        super().__init__(parent)
        # 2. set widgets
        self.__mode = QComboBox()
        self.__mode.addItems(('S', 'R', 'S+R', 'S,R'))
        self.__side_s = QComboBox()
        self.__side_r = QComboBox()
        self.__side_sr = QComboBox()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        layout = QGridLayout(self)
        layout.addWidget(QLabel(self.tr("Mode:")), 0, 0)
        layout.addWidget(self.__mode, 0, 1)
        layout.addWidget(QLabel(self.tr("Side S:")), 1, 0)
        layout.addWidget(self.__side_s, 1, 1)
        layout.addWidget(self.__side_r, 2, 1)
        layout.addWidget(self.__side_sr, 3, 1)
        layout.addWidget(self.button_box, 4, 0)
        self.setLayout(layout)
        # 4. set signals
        self.__mode.currentIndexChanged.connect(self.__slot_mode_chgd)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 5. go
        self.setWindowTitle(self.tr("Select OMP to save"))

    def execute(self, ct_list: List[ComtradeWidget]) -> Optional[Tuple[int, int]]:
        """Open dialog and return result.
        :return: ([S-osc], [R-osc])
        :todo: who play (prepare listboxes)
        """
        self.__ct_list = ct_list
        self.__side_s.clear()
        self.__side_r.clear()
        self.__side_sr.clear()
        for ct in ct_list:
            self.__side_s.addItem(ct.osc.path.name)
            self.__side_r.addItem(ct.osc.path.name)
            self.__side_sr.addItem(ct.osc.path.name)
        # TODO: disable self.__mode indexes
        # TODO: set self.__mode index
        if self.exec_():
            return 0, 0

    def __slot_mode_chgd(self, idx: int):
        """
        - Show/hide labels and comboboxes
        - Enable/disable 'OK'
        :param idx:
        :return:
        """
        ...
