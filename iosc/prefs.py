"""Applications settings."""
from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QComboBox, QApplication, QStyleFactory, \
    QCommonStyle, QCheckBox

# x. const
REG_EXP = QRegExp(r'.(.*)\+?Style')


class AppSettingsDialog(QDialog):
    f_style: QComboBox
    f_palette: QCheckBox
    f_qss: QComboBox
    button_box: QDialogButtonBox
    _layout: QFormLayout
    _old_style: QCommonStyle
    _old_palette: QPalette
    _old_qss: str

    def __init__(self, parent=None):
        """Init AppSettingsDialog object."""
        super().__init__(parent)
        # 1. store old
        self._old_style = QApplication.style()
        _old_style_name = self._old_style.metaObject().className()
        self._old_palette: QPalette = QApplication.palette()
        if REG_EXP.exactMatch(_old_style_name):
            _old_style_name = REG_EXP.cap(1)
        # 2. set widgets
        self.f_style = QComboBox(self)
        self.f_style.addItems(QStyleFactory.keys())
        self.f_style.setCurrentIndex(self.f_style.findText(_old_style_name, Qt.MatchContains))
        self.f_palette = QCheckBox(self)
        self.f_qss = QComboBox(self)
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
        # 4. set signals
        # self.f_color.clicked.connect(self.__set_color)
        self.f_style.activated.connect(self.__style_changed)
        self.f_palette.toggled.connect(self.__palette_changed)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 5. go
        self.setWindowTitle("Application settings")

    def __style_changed(self, idx: int):
        # print(idx, type(idx), self.f_style.currentText())
        QApplication.setStyle(QStyleFactory.create(self.f_style.currentText()))
        if self.f_palette.isChecked():
            QApplication.setPalette(QApplication.style().standardPalette())
        # QApplication.setStyle(QStyleFactory.create(styleName))

    def __palette_changed(self, v: bool):
        QApplication.setPalette(QApplication.style().standardPalette() if v else self._old_palette)
