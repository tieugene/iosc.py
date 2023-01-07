"""Edit dialogs."""
# 1. std
from typing import Optional, Union
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QComboBox, QPushButton, QColorDialog, QLineEdit, \
    QInputDialog, QWidget, QDoubleSpinBox, QListWidget, QVBoxLayout, QListWidgetItem


class SignalPropertiesDialog(QDialog):
    """Base class for editing signal properties."""

    _ss: Union['StatusSignalSuit', 'AnalogSignalSuit']  # noqa: F821
    _color: QColor
    f_name: QLineEdit
    f_type: QLineEdit
    f_color: QPushButton
    button_box: QDialogButtonBox
    _layout: QFormLayout

    def __init__(self, ss: Union['StatusSignalSuit', 'AnalogSignalSuit'], parent=None):  # noqa: F821
        """Init SignalPropertiesDialog object."""
        super().__init__(parent)
        # 1. store args
        self._ss = ss
        self._color = ss.color
        # 2. set widgets
        self.f_name = QLineEdit(ss.sid, self)
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
        color = QColorDialog.getColor(self._color, self)
        if color.isValid():
            self._color = color
            self.__set_color_button()


class StatusSignalPropertiesDialog(SignalPropertiesDialog):
    """Edit B-signal properties dialog."""

    def __init__(self, ss: 'StatusSignalSuit', parent=None):  # noqa: F821
        """Init StatusSignalPropertiesDialog object."""
        super().__init__(ss, parent)
        self.f_type.setText("Status")

    def execute(self) -> bool:
        """Open dialog and return result."""
        if self.exec_():
            self._ss.color = self._color
            return True
        return False


class AnalogSignalPropertiesDialog(SignalPropertiesDialog):
    """Edit A-signal properties."""

    f_uu: QLineEdit
    f_pmult: QLineEdit
    f_smult: QLineEdit
    f_pors: QLineEdit
    f_style: QComboBox

    def __init__(self, ss: 'AnalogSignalSuit', parent=None):  # noqa: F821
        """Init AnalogSignalPropertiesDialog object."""
        super().__init__(ss, parent)
        self.f_type.setText("Analog")
        self.f_uu = QLineEdit(self._ss.signal.uu)
        self.f_uu.setReadOnly(True)
        self.f_pmult = QLineEdit(str(self._ss.signal.primary))
        self.f_pmult.setReadOnly(True)
        self.f_smult = QLineEdit(str(self._ss.signal.secondary))
        self.f_smult.setReadOnly(True)
        self.f_pors = QLineEdit(self._ss.signal.pors)
        self.f_pors.setReadOnly(True)
        self.f_style = QComboBox(self)
        self.f_style.addItems(("Solid", "Dotted", "Dash-dotted"))
        self.f_style.setCurrentIndex(self._ss.line_style)
        # add them
        self._layout.insertRow(2, "Unit", self.f_uu)
        self._layout.insertRow(3, "Primary: x", self.f_pmult)
        self._layout.insertRow(4, "Secondary: x", self.f_smult)
        self._layout.insertRow(5, "P/S", self.f_pors)
        self._layout.insertRow(7, "Line type", self.f_style)  # QInputDialog.getItem()

    def execute(self) -> bool:
        """Open doialog and return result."""
        if self.exec_():
            self._ss.line_style = self.f_style.currentIndex()
            self._ss.color = self._color
            return True
        return False


def get_new_omp_width(parent: QWidget, old_value: int) -> Optional[int]:
    """:return: New OMP ptrs distance."""
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
    """Add/Edit TmpPtr dialog."""

    f_val: QDoubleSpinBox
    f_name: QLineEdit
    button_box: QDialogButtonBox

    def __init__(self, data: tuple[float, float, float, float, str], parent=None):
        """Init TmpPtrDialog object."""
        super().__init__(parent)
        # 1. store args
        # 2. set widgets
        self.f_val = QDoubleSpinBox(self)
        self.f_val.setRange(data[1], data[2])
        self.f_val.setSingleStep(data[3])
        self.f_val.setDecimals(3)
        self.f_val.setValue(data[0])  # Note: after all
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
    """Select signal dialog."""

    f_signals: QListWidget
    button_all: QPushButton
    button_none: QPushButton
    buttons_select: QDialogButtonBox
    button_box: QDialogButtonBox

    def __init__(self, ass_list: list['AnalogSignalSuit'], ass_used: set[int] = (), parent=None):  # noqa: F821
        """Init SelectSignalsDialog object."""
        super().__init__(parent)
        self.setWindowTitle("Select signals")
        self._mk_widgets()
        self._mk_layout()
        self._mk_connections()
        self._set_data(ass_list, ass_used)
        self.button_box.setFocus()

    def _mk_widgets(self):
        self.button_all = QPushButton("Select all", self)
        self.button_none = QPushButton("Clean", self)
        self.buttons_select = QDialogButtonBox()
        self.buttons_select.addButton(self.button_all, QDialogButtonBox.AcceptRole)
        self.buttons_select.addButton(self.button_none, QDialogButtonBox.RejectRole)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.f_signals = QListWidget()
        self.f_signals.setSelectionMode(self.f_signals.MultiSelection)

    def _mk_layout(self):
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.buttons_select)
        self.layout().addWidget(self.f_signals)
        self.layout().addWidget(self.button_box)
        # layout.setVerticalSpacing(0)

    def _mk_connections(self):
        self.f_signals.itemSelectionChanged.connect(self.__slot_selection_changed)
        self.buttons_select.accepted.connect(self.__slot_select_all)
        self.buttons_select.rejected.connect(self.__slot_select_none)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _set_data(self, ass_list: list['AnalogSignalSuit'], ass_used: set[int]):  # noqa: F821
        for i, ss in enumerate(ass_list):
            item = QListWidgetItem(ss.sid, self.f_signals)
            item.setForeground(ss.color)
            item.setFlags(item.flags() & (~Qt.ItemIsUserCheckable))
            if i in ass_used:
                item.setCheckState(Qt.Checked)
                item.setSelected(True)
            else:
                item.setCheckState(Qt.Unchecked)

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

    def execute(self) -> Optional[list[int]]:
        """Open dialog and return result."""
        if self.exec_():
            retvalue = list()
            for i in range(self.f_signals.count()):
                if self.f_signals.item(i).checkState() == Qt.Checked:
                    retvalue.append(i)
            return retvalue


class MsrPtrDialog(QDialog):
    """Add/Edit MsrPtr dialog."""

    f_val: QDoubleSpinBox
    f_func: QComboBox
    button_box: QDialogButtonBox

    def __init__(self, data: tuple[float, float, float, float, int], parent=None):
        """Init MsrPtrDialog object."""
        super().__init__(parent)
        # 1. store args
        # 2. set widgets
        self.f_val = QDoubleSpinBox(self)
        self.f_val.setRange(data[1], data[2])
        self.f_val.setSingleStep(data[3])
        self.f_val.setDecimals(3)
        self.f_val.setValue(data[0])
        self.f_func = QComboBox()
        self.f_func.addItems(("As is", "Mid", "Effective", "H1", "H2", "H3", "H5"))
        self.f_func.setCurrentIndex(data[4])
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # 3. set layout
        layout = QFormLayout(self)
        layout.addRow("Value", self.f_val)
        layout.addRow("Func", self.f_func)
        layout.addRow(self.button_box)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)
        # 4. set signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # 5. go
        self.setWindowTitle("Msr ptr properties")  # FIXME: += ' M1: <sid>'


class LvlPtrDialog(QDialog):
    """Add/Edit LvlPtr dialog."""

    f_val: QDoubleSpinBox
    button_box: QDialogButtonBox

    def __init__(self, data: tuple[float, float, float], parent=None):
        """Init LvlPtrDialog object."""
        super().__init__(parent)
        # 1. store args
        # 2. set widgets
        self.f_val = QDoubleSpinBox(self)
        self.f_val.setRange(data[1], data[2])
        self.f_val.setDecimals(3)
        self.f_val.setValue(data[0])
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
        self.setWindowTitle("Lvl ptr properties")  # FIXME: += ' L1: <sid>'
