"""QDialog successors"""
# 1. std
from typing import List
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPushButton, QColorDialog, QComboBox
# 3. local
from iosc.sig.widget.sigsuit import AnalogSignalSuit


class LineStyleSelector(QComboBox):
    """Line style selector"""

    def __init__(self, parent: QDialog = None):
        """Init LineStyleSelector object."""
        super().__init__(parent)
        self.addItems(("Solid", "Dotted", "Dash-dotted"))
        self.setCurrentIndex(0)


class SignalSelector(QComboBox):
    """Signal selector."""

    def __init__(self, ass_list: List[AnalogSignalSuit], parent: QDialog = None):
        """Init SignalSelector object."""
        super().__init__(parent)
        for i, ss in enumerate(ass_list):
            self.addItem(ss.sid)
            self.setItemData(self.count() - 1, i)  # FIXME: ss itself


class MathModuleDialog(QDialog):
    """Dialog to add/edit Maths/Conversion/Module signal"""
    _color: QColor
    f_name: QLineEdit
    f_color: QPushButton
    f_style: LineStyleSelector
    f_signal: SignalSelector
    button_box: QDialogButtonBox

    def __init__(self, ass_list: List[AnalogSignalSuit], parent=None):
        """Init MathModuleDialog object."""
        super().__init__(parent)
        self._color = QColor(Qt.GlobalColor.black)
        self.setWindowTitle("Signal module")
        self._mk_widgets(ass_list)
        self._mk_layout()
        self._mk_connections()
        self.button_box.setFocus()

    def _mk_widgets(self, ass_list: List[AnalogSignalSuit]):
        self.f_name = QLineEdit()
        self.f_style = LineStyleSelector()
        self.f_color = QPushButton()
        self.__set_color_button()
        self.f_signal = SignalSelector(ass_list)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

    def _mk_layout(self):
        lt = QFormLayout()
        lt.addRow("Name", self.f_name)
        lt.addRow("Color", self.f_color)
        lt.addRow("Style", self.f_style)
        lt.addRow("Signal", self.f_signal)
        lt.addRow(self.button_box)
        lt.setVerticalSpacing(0)
        self.setLayout(lt)

    def _mk_connections(self):
        self.f_color.clicked.connect(self.__set_color)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def __set_color_button(self):
        self.f_color.setText(self._color.name(QColor.HexRgb))
        self.f_color.setStyleSheet("color : %s" % self._color.name(QColor.HexRgb))

    def __set_color(self):
        color = QColorDialog.getColor(self._color, self)
        if color.isValid():
            self._color = color
            self.__set_color_button()
