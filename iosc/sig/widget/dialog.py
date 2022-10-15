"""Edit dialogs"""
from typing import Optional

# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QDoubleValidator, QBrush
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QComboBox, QPushButton, QColorDialog, QLineEdit, \
    QInputDialog, QWidget, QDoubleSpinBox, QListWidget, QVBoxLayout, QListWidgetItem
# 3. local
from iosc.core import mycomtrade
from iosc.core.mycomtrade import AnalogSignalList, StatusSignalList


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
        self.f_type = QLineEdit()
        self.f_type.setReadOnly(True)
        self.f_color = QPushButton(self)
        self.__set_color_button()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        self._layout = QFormLayout(self)  # FIXME: not h-stretchable
        self._layout.addRow("Name", self.f_name)
        self._layout.addRow("Type", self.f_type)
        self._layout.addRow("Color", self.f_color)
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
    f_uu: QLineEdit
    f_pmult: QLineEdit
    f_smult: QLineEdit
    f_pors: QLineEdit
    f_style: QComboBox

    def __init__(self, signal: mycomtrade.AnalogSignal, parent=None):
        super().__init__(signal, parent)
        self.f_type.setText("Analog")
        self.f_uu = QLineEdit(self._signal.raw2.uu)
        self.f_uu.setReadOnly(True)
        self.f_pmult = QLineEdit(str(self._signal.raw2.primary))
        self.f_pmult.setReadOnly(True)
        self.f_smult = QLineEdit(str(self._signal.raw2.secondary))
        self.f_smult.setReadOnly(True)
        self.f_pors = QLineEdit(self._signal.raw2.pors)
        self.f_pors.setReadOnly(True)
        self.f_style = QComboBox(self)
        self.f_style.addItems(("Solid", "Dotted", "Dash-dotted"))
        self.f_style.setCurrentIndex(self._signal.line_type.value)
        # add them
        self._layout.insertRow(2, "Unit", self.f_uu)
        self._layout.insertRow(3, "Primary: x", self.f_pmult)
        self._layout.insertRow(4, "Secondary: x", self.f_smult)
        self._layout.insertRow(5, "P/S", self.f_pors)
        self._layout.insertRow(7, "Line type", self.f_style)  # QInputDialog.getItem()

    def execute(self) -> bool:
        if self.exec_():
            self._signal.line_type = mycomtrade.ELineType(self.f_style.currentIndex())
            self._signal.rgb = (self._color.red(), self._color.green(), self._color.blue())
            return True
        return False


class StatusSignalPropertiesDialog(SignalPropertiesDialog):
    def __init__(self, signal: mycomtrade.StatusSignal, parent=None):
        super().__init__(signal, parent)
        self.f_type.setText("Status")

    def execute(self) -> bool:
        if self.exec_():
            self._signal.rgb = (self._color.red(), self._color.green(), self._color.blue())
            return True
        return False


def get_new_omp_width(parent: QWidget, old_value: int) -> Optional[int]:
    new_value, ok = QInputDialog.getInt(
            parent,
            "Distance between PR and SC",
            "Main frequency periods number",
            old_value,
            1,
            10
        )
    if ok and new_value != old_value:
        return new_value


class TmpPtrDialog(QDialog):
    f_val: QDoubleSpinBox
    f_name: QLineEdit
    button_box: QDialogButtonBox

    def __init__(self, data: tuple[float, float, float, float, str], parent=None):
        super().__init__(parent)
        # 1. store args
        # 2. set widgets
        self.f_val = QDoubleSpinBox(self)
        self.f_val.setRange(data[1], data[2])
        self.f_val.setSingleStep(data[3])
        self.f_val.setDecimals(3)
        self.f_val.setValue(data[0])
        self.f_name = QLineEdit(data[4], self)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        layout = QFormLayout(self)
        layout.addRow("Value", self.f_val)
        layout.addRow("Name", self.f_name)
        layout.addRow(self.button_box)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)
        # 4. set signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 5. go
        self.setWindowTitle("Tmp ptr properties")


class SelectSignalsDialog(QDialog):
    f_signals: QListWidget
    button_all: QPushButton
    button_none: QPushButton
    buttons_select: QDialogButtonBox
    button_box: QDialogButtonBox

    def __init__(self, a_list: AnalogSignalList, s_list: StatusSignalList, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select signals")
        # 1. set widgets
        self.button_all = QPushButton("Select all", self)
        self.button_none = QPushButton("Clean", self)
        self.buttons_select = QDialogButtonBox()
        self.buttons_select.addButton(self.button_all, QDialogButtonBox.AcceptRole)
        self.buttons_select.addButton(self.button_none, QDialogButtonBox.RejectRole)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.f_signals = QListWidget()
        self.f_signals.setSelectionMode(self.f_signals.MultiSelection)
        for _list in (a_list, s_list):
            for sig in _list:
                item = QListWidgetItem(sig.sid)
                item.setFlags(item.flags() & (~Qt.ItemIsUserCheckable))
                item.setCheckState(Qt.Unchecked)
                item.setForeground(QColor(*sig.rgb))
                self.f_signals.addItem(item)
        # 3. set layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.buttons_select)
        self.layout().addWidget(self.f_signals)
        self.layout().addWidget(self.button_box)
        # layout.setVerticalSpacing(0)
        # 4. set signals
        self.f_signals.itemSelectionChanged.connect(self.__slot_selection_changed)
        self.buttons_select.accepted.connect(self.__slot_select_all)
        self.buttons_select.rejected.connect(self.__slot_select_none)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def __slot_selection_changed(self):
        for i in range(self.f_signals.count()):
            item = self.f_signals.item(i)
            if item.isSelected():
                if item.checkState() != Qt.Checked:
                    item.setCheckState(Qt.Checked)
            else:
                if item.checkState() != Qt.Unchecked:
                    item.setCheckState(Qt.Unchecked)

    def __select(self, state: bool):
        for i in range(self.f_signals.count()):
            self.f_signals.item(i).setSelected(state)

    def __slot_select_all(self):
        self.__select(True)

    def __slot_select_none(self):
        self.__select(False)

    def execute(self) -> list[int]:
        retvalue = list()
        if self.exec_():
            for i in range(self.f_signals.count()):
                if self.f_signals.item(i).isSelected():
                    retvalue.append(i)
        return retvalue


class MsrPtrDialog(QDialog):
    f_val: QDoubleSpinBox
    button_box: QDialogButtonBox

    def __init__(self, data: tuple[float, float, float, float], parent=None):
        super().__init__(parent)
        # 1. store args
        # 2. set widgets
        self.f_val = QDoubleSpinBox(self)
        self.f_val.setValue(data[0])
        self.f_val.setRange(data[1], data[2])
        self.f_val.setSingleStep(data[3])
        self.f_val.setDecimals(3)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        layout = QFormLayout(self)
        layout.addRow("Value", self.f_val)
        layout.addRow(self.button_box)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)
        # 4. set signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 5. go
        self.setWindowTitle("Msr ptr properties")


class AnalogMsrPtrDialog(MsrPtrDialog):
    f_func: QComboBox

    def __init__(self, data: tuple[float, float, float, float, str], parent=None):
        super().__init__(data, parent)
        self.f_func = QComboBox()
        self.layout().insertRow(1, "Func", self.f_func)
