"""Signal list view
QTableWidget version
:todo: try QTableWidgetItem
"""
# 2. 3rd
from PySide2.QtCore import Qt, QPoint
from PySide2.QtGui import QPalette, QColor
from PySide2.QtWidgets import QTableWidget, QAbstractItemView, QMenu, QDialog, QFormLayout, QDialogButtonBox, \
    QComboBox, QPushButton, QColorDialog, QLineEdit
# 3. local
import mycomtrade
from sigwidget import SignalCtrlView, SignalChartView
# x. const
ANALOG_ROW_HEIGHT = 64


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
        super(SigPropertiesDialog, self).__init__(parent)
        # 1. store args
        self.__signal = signal
        self.__color = QColor.fromRgb(*signal.rgb)
        # 2. set widgets
        self.f_name = QLineEdit(signal.sid, self)
        self.f_name.setReadOnly(True)
        self.f_type = QLineEdit(("Analog", "Discrete")[int(signal.is_bool)], self)
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


class SignalListView(QTableWidget):
    slist: mycomtrade.SignalList

    def __init__(self, slist: mycomtrade.SignalList, ti: int, parent=None):
        super(SignalListView, self).__init__(parent)
        self.slist = slist
        self.setColumnCount(2)
        self.setRowCount(slist.count)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.setShowGrid(True)  # default
        # self.setContentsMargins(0, 0, 0, 0)  # not works
        # self.setFrameStyle(QFrame.NoFrame)  # remove table outer frame lines
        # self.verticalHeader().setVisible(False)
        # self.horizontalHeader().setVisible(False)
        # self.setSelectionBehavior(QAbstractItemView.NoSelection)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        # self.setStyleSheet("QTableWidget::item { padding: 0; margin: 0; }")  # not works
        for row in range(slist.count):
            ctrl = SignalCtrlView(self)
            ctrl.set_data(slist[row])
            self.setCellWidget(row, 0, ctrl)  # or .setItem(row, col, QTableWidgetItem())
            chart = SignalChartView(ti, self)
            chart.set_data(slist[row])
            self.setCellWidget(row, 1, chart)
            self.setRowHeight(row, ANALOG_ROW_HEIGHT)
            # self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # too high
        # self.resizeRowsToContents()
        # <dbg>
        # print("Table:", self.width())  # 100 always
        # print("Col0 #0", self.columnWidth(0))  # 100 always
        self.resizeColumnToContents(0)
        # print("Col0 #1", self.columnWidth(0))  # right
        # </dbf>
        # self.horizontalHeader().setStretchLastSection(True)  # FIXME: calc; default = 100
        # conext menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._handle_context_menu)

    def line_up(self, dwidth: int, w0: int):
        """Resize columns according to requirements.
        :param dwidth: Main window widths subtraction (available - actual)
        :param w0: Width of 0th column
        :fixme: subtract something (vheader width?)
        """
        self.setColumnWidth(0, w0)
        self.setColumnWidth(1, self.width() + dwidth - w0 - 48)  # FIXME: magic number

    def _handle_context_menu(self, point: QPoint):
        index: int = self.rowAt(point.y())
        if index < 0:
            return
        context_menu = QMenu()
        sig_property = context_menu.addAction("Signal property")
        chosen_action = context_menu.exec_(self.mapToGlobal(point))
        if chosen_action == sig_property:
            self.__set_sig_property(index)

    def __set_sig_property(self, index: int):
        """Show/set signal properties:
        - Name:str (r/o)
        - Type:enum[analog/discrete] (r/o)
        - Color:color (r/w)
        - Linetype:enum[solid/dot/dashdot
        """
        signal = self.slist[index]
        if SigPropertiesDialog(signal).execute():
            # repaint 2xWidgets
            print("Color: ", signal.rgb)
            print("Line: ", signal.line_type.value)
