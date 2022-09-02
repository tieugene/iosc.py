"""Signal properties viewer/editor
TODO: Add fields (A-ch):
- uu
- Px
- Sx
- ps
"""
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QComboBox, QPushButton, QColorDialog, QLineEdit
# 3. local
import mycomtrade


class SignalPropertiesDialog(QDialog):
    _signal: mycomtrade.Signal
    _color: QColor
    f_name: QLineEdit
    f_type: QLineEdit
    f_color: QPushButton
    button_box: QDialogButtonBox
    _layout: QFormLayout

    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super().__init__(parent)
        # 1. store args
        self._signal = signal
        self._color = QColor.fromRgb(*signal.rgb)
        # 2. set widgets
        self.f_name = QLineEdit(signal.sid, self)
        self.f_name.setReadOnly(True)
        self.f_type = QLineEdit(("Analog", "Status")[int(signal.is_bool)], self)
        self.f_type.setReadOnly(True)
        self.f_color = QPushButton(self)
        self.__set_color_button()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        self._layout = QFormLayout(self)  # FIME: not h-stretchable
        self._layout.addRow("Name", self.f_name)
        self._layout.addRow("Type", self.f_type)
        self._layout.addRow("Color", self.f_color)  # QColorDialog.getColor()
        self._layout.addRow(self.button_box)
        self._layout.setVerticalSpacing(0)
        self.setLayout(self._layout)
        # 4. set signals
        self.f_color.clicked.connect(self.__set_color)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 5. go
        self.setWindowTitle("Signal properties")

    def __set_color_button(self):
        self.f_color.setText(self._color.name(QColor.HexRgb))
        self.f_color.setStyleSheet("color : %s" % self._color.name(QColor.HexRgb))

    def __set_color(self):
        color = QColorDialog.getColor(Qt.green, self)
        if color.isValid():
            self._color = color
            self.__set_color_button()


class AnalogSignalPropertiesDialog(SignalPropertiesDialog):
    f_line: QComboBox

    def __init__(self, signal: mycomtrade.AnalogSignal, parent=None):
        super().__init__(signal, parent)
        self.f_line = QComboBox(self)
        self.f_line.addItems(("Solid", "Dotted", "Dash-dotted"))
        self.f_line.setCurrentIndex(self._signal.line_type.value)
        self._layout.insertRow(3, "Line type", self.f_line)  # QInputDialog.getItem()

    def execute(self) -> bool:
        if self.exec_():
            self._signal.line_type = mycomtrade.ELineType(self.f_line.currentIndex())
            self._signal.rgb = (self._color.red(), self._color.green(), self._color.blue())
            return True
        return False


class StatusSignalPropertiesDialog(SignalPropertiesDialog):
    def __init__(self, signal: mycomtrade.StatusSignal, parent=None):
        super().__init__(signal, parent)

    def execute(self) -> bool:
        if self.exec_():
            self._signal.rgb = (self._color.red(), self._color.green(), self._color.blue())
            return True
        return False
