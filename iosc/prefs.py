"""Applications settings.
Location:
- Linux: ~/.config/TI_Eugene/iOsc.conf
"""
import pathlib
from typing import Dict, List

from PyQt5.QtCore import QRegExp, Qt, QSettings
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QComboBox, QApplication, QStyleFactory, QCheckBox

import iosc.const


def load_style(settings: QSettings, shares_dir: pathlib.PosixPath):
    """Setup style with settings."""
    if style_name := settings.value('style'):
        style = QStyleFactory.create(style_name)
    else:
        style = ''
    QApplication.setStyle(style)
    if settings.value('palette'):
        palette = QApplication.style().standardPalette()
    else:
        palette = QPalette()
    QApplication.setPalette(palette)
    if qss_name := settings.value(iosc.const.QSS_DIR):
        qss_file = shares_dir.joinpath(iosc.const.QSS_DIR, qss_name).with_suffix('.qss')
        with open(qss_file.as_posix(), 'rt') as file:
            qss = file.read()
    else:
        qss = ''
    QApplication.instance().setStyleSheet(qss)


def _load_qss(shares_dir: pathlib.PosixPath) -> Dict[str, str]:
    """Load styles from data folder"""
    retvalue = {'---': ''}
    for f in shares_dir.joinpath(iosc.const.QSS_DIR).iterdir():
        with open(f.as_posix(), 'rt') as file:
            retvalue[f.stem] = file.read()
    return retvalue


class AppSettingsDialog(QDialog):
    _settings: QSettings
    _shares_dir: pathlib.PosixPath
    _style: List[str]
    _qss: Dict[str, str]
    f_style: QComboBox
    f_palette: QCheckBox
    f_qss: QComboBox
    button_box: QDialogButtonBox
    _layout: QFormLayout

    def __init__(self, settings: QSettings, shares_dir: pathlib.PosixPath, parent=None):
        """Init AppSettingsDialog object."""
        super().__init__(parent)
        self._settings = settings
        self._shares_dir = shares_dir
        self._style = ['---']
        self._style.extend(QStyleFactory.keys())
        self._qss = _load_qss(shares_dir)
        # 2. set widgets
        self.f_style = QComboBox(self)
        self.f_style.addItems(self._style)
        self.f_palette = QCheckBox(self)
        self.f_qss = QComboBox(self)
        self.f_qss.addItems(self._qss.keys())
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        self._layout = QFormLayout(self)
        self._layout.addRow("Base style", self.f_style)
        self._layout.addRow("Default palette", self.f_palette)
        self._layout.addRow("QSS", self.f_qss)
        self._layout.addRow(self.button_box)
        self._layout.setVerticalSpacing(0)
        self.setLayout(self._layout)
        # 4. set initial
        if style := settings.value('style'):
            idx = self.f_style.findText(style)
        else:
            idx = 0
        self.f_style.setCurrentIndex(idx)
        if settings.value('palette'):
            self.f_palette.setChecked(True)
        if qss := settings.value('qss'):
            idx = self.f_qss.findText(qss)
        else:
            idx = 0
        self.f_qss.setCurrentIndex(idx)
        # 5. set signals
        self.f_style.activated.connect(self.__on_chg_style)
        self.f_palette.toggled.connect(self.__on_chg_palette)
        self.f_qss.activated.connect(self.__on_chg_qss)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 6. go
        self.setWindowTitle("Application settings")

    def __on_chg_style(self, idx: int):  # idx:int 0+
        QApplication.setStyle(QStyleFactory.create(self.f_style.currentText()) if idx else '')
        QApplication.setPalette(QApplication.style().standardPalette() if self.f_palette.isChecked() else QPalette())

    def __on_chg_palette(self, v: bool):
        QApplication.setPalette(QApplication.style().standardPalette() if v else QPalette())

    def __on_chg_qss(self, v: bool):
        QApplication.instance().setStyleSheet(self._qss[self.f_qss.currentText()])

    def execute(self) -> bool:
        """Open dialog and return result."""
        if self.exec_():  # True: save settings
            if self.f_style.currentIndex() > 0:
                self._settings.setValue('style', self.f_style.currentText())
            else:
                self._settings.remove('style')
            if self.f_palette.isChecked():
                self._settings.setValue('palette', True)
            else:
                self._settings.remove('palette')
            if self.f_qss.currentIndex() > 0:
                self._settings.setValue('qss', self.f_qss.currentText())
            else:
                self._settings.remove('qss')
            return True
        load_style(self._settings, self._shares_dir)  # False: restore style
        return False
