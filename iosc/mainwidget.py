# 2. 3rd
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget
# 3. local
import mycomtrade
from siglist_tw import SignalListView
# from draft.siglist_vbl import SignalListView


class ComtradeWidget(QWidget):
    """
    Main osc window. Includes analog and discrete panels
    """
    analog_panel: SignalListView
    discret_panel: SignalListView

    def __init__(self, rec: mycomtrade.MyComtrade, parent: QTabWidget = None):
        super(ComtradeWidget, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        # 1. analog part
        self.analog_panel = SignalListView(rec.analog, self)
        splitter.addWidget(self.analog_panel)
        # 2. digital part
        self.discret_panel = SignalListView(rec.discret, self)
        splitter.addWidget(self.discret_panel)
        # 3. lets go
        self.layout().addWidget(splitter)

    def line_up(self, dwidth: int):
        """
        Line up table colums (and rows further) according to requirements and actual geometry.
        :param dwidth: Main window widths subtraction (available - actual)
        """
        # print("Dwidth: ", dwidth)  # 320, ok
        # print("T Table: ", self.analog_panel.width())  # 940 == mw-20
        # print("T Col_0:", self.analog_panel.columnWidth(0))
        # print("D Table: ", self.discret_panel.width())
        # print("D Col_0:", self.discret_panel.columnWidth(0))
        w0 = max(self.analog_panel.columnWidth(0), self.discret_panel.columnWidth(0))
        self.analog_panel.line_up(dwidth, w0)
        self.discret_panel.line_up(dwidth, w0)
