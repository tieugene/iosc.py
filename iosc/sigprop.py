# 2. 3rd
from PySide2.QtCore import Qt
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QComboBox, QPushButton, QColorDialog, QLineEdit
# 3. local
import mycomtrade


class SigPropertiesDialog(QDialog):
    """:todo: move to sigwidget.py"""
    f_name: QLineEdit
    f_type: QLineEdit
    f_color: QPushButton
    f_line: QComboBox
    button_box: QDialogButtonBox
    __color: QColor
    __signal: mycomtrade.Signal

    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super().__init__(parent)
        # 1. store args
        self.__signal = signal
        self.__color = QColor.fromRgb(*signal.rgb)
        # 2. set widgets
        self.f_name = QLineEdit(signal.sid, self)
        self.f_name.setReadOnly(True)
        self.f_type = QLineEdit(("Analog", "Status")[int(signal.is_bool)], self)
        self.f_type.setReadOnly(True)
        self.f_color = QPushButton(self)
        self.__set_color_button()
        self.f_line = QComboBox(self)
        self.f_line.addItems(("Solid", "Dotted", "Dash-dotted"))
        self.f_line.setCurrentIndex(signal.line_type.value)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        layout = QFormLayout(self)  # FIME: not h-stretchable
        layout.addRow("Name", self.f_name)
        layout.addRow("Type", self.f_type)
        layout.addRow("Color", self.f_color)  # QColorDialog.getColor()
        layout.addRow("Line type", self.f_line)  # QInputDialog.getItem()
        # the end
        layout.addRow(self.button_box)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)
        # 4. set signals
        self.f_color.clicked.connect(self.set_color)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 5. go
        self.setWindowTitle("Signal properties")

    def __set_color_button(self):
        self.f_color.setText(self.__color.name(QColor.HexRgb))
        self.f_color.setStyleSheet("color : %s" % self.__color.name(QColor.HexRgb))

    def set_color(self):
        color = QColorDialog.getColor(Qt.green, self)
        if color.isValid():
            self.__color = color
            self.__set_color_button()

    def execute(self) -> bool:
        if self.exec_():
            self.__signal.line_type = mycomtrade.ELineType(self.f_line.currentIndex())
            self.__signal.rgb = (self.__color.red(), self.__color.green(), self.__color.blue())
            return True
        return False
