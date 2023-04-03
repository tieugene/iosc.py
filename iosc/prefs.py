"""Applications settings."""
import pathlib
from typing import Dict

from PyQt5.QtCore import QRegExp, Qt, QFile
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QComboBox, QApplication, QStyleFactory, QCheckBox
# x. const
REG_EXP = QRegExp(r'.(.*)\+?Style')


class AppSettingsDialog(QDialog):
    _qss_dir: pathlib.PosixPath
    _old_style_name: str  # QCommonStyle
    _old_palette: QPalette
    _old_qss: str
    _styles: Dict[str, str]
    f_style: QComboBox
    f_palette: QCheckBox
    f_qss: QComboBox
    button_box: QDialogButtonBox
    _layout: QFormLayout

    def __init__(self, qss_dir: pathlib.PosixPath, parent=None):
        """Init AppSettingsDialog object."""
        super().__init__(parent)
        self._styles = {'---': ''}
        self._qss_dir = qss_dir
        self.__load_styles(qss_dir)
        # 1. store old
        self._old_style_name = QApplication.style().metaObject().className()
        self._old_palette: QPalette = QApplication.palette()
        if REG_EXP.exactMatch(self._old_style_name):
            self._old_style_name = REG_EXP.cap(1)
        # print(list(qss_dir.iterdir()))
        # 2. set widgets
        self.f_style = QComboBox(self)
        self.f_style.addItems(QStyleFactory.keys())
        self.f_style.setCurrentIndex(self.f_style.findText(self._old_style_name, Qt.MatchContains))
        self.f_palette = QCheckBox(self)
        self.f_qss = QComboBox(self)
        self.f_qss.addItems(self._styles.keys())
        # self.f_style.setCurrentIndex(self._ss.line_style)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        self._layout = QFormLayout(self)
        self._layout.addRow("Base style", self.f_style)
        self._layout.addRow("Default palette", self.f_palette)
        self._layout.addRow("QSS", self.f_qss)
        self._layout.addRow(self.button_box)
        self._layout.setVerticalSpacing(0)
        self.setLayout(self._layout)
        # 5. set signals
        self.f_style.activated.connect(self.__style_changed)
        self.f_palette.toggled.connect(self.__palette_changed)
        self.f_qss.activated.connect(self.__qss_changed)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 6. go
        self.setWindowTitle("Application settings")

    def __load_styles(self, qss_dir: pathlib.PosixPath):
        for f in qss_dir.iterdir():
            file = QFile(f.as_posix())
            file.open(QFile.ReadOnly)
            self._styles[f.stem] = str(file.readAll(), encoding='utf8')

    def __style_changed(self, _: int):  # idx:int 0+
        QApplication.setStyle(QStyleFactory.create(self.f_style.currentText()))
        if self.f_palette.isChecked():
            QApplication.setPalette(QApplication.style().standardPalette())

    def __palette_changed(self, v: bool):
        QApplication.setPalette(QApplication.style().standardPalette() if v else self._old_palette)

    def __qss_changed(self, v: bool):
        QApplication.instance().setStyleSheet(self._styles[self.f_qss.currentText()])

    def execute(self) -> bool:
        """Open doialog and return result."""
        if not self.exec_():
            QApplication.setStyle(self._old_style_name)
            QApplication.setPalette(self._old_palette)
            return False
        return True
