# 2. 3rd
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter, QScrollArea
# 3. local
import mycomtrade
from iosc.draft.siglist_mvc import SignalListView


class SignalScrollArea(QScrollArea):
    def __init__(self, panel: QWidget, parent=None):
        super(SignalScrollArea, self).__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(panel)


class ComtradeWidget(QWidget):
    """
    Main osc window. Includes analog and discrete panels
    """
    analog_panel: SignalListView
    discret_panel: SignalListView

    def __init__(self, rec: mycomtrade.MyComtrade, parent=None):
        super(ComtradeWidget, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        # 1. analog part
        self.analog_panel = SignalListView(rec.analog)
        self.analog_scroll = SignalScrollArea(self.analog_panel)
        splitter.addWidget(self.analog_scroll)
        # 2. digital part
        self.discret_panel = SignalListView(rec.discret)
        self.discret_scroll = SignalScrollArea(self.discret_panel)
        splitter.addWidget(self.discret_scroll)
        # 3. lets go
        self.layout().addWidget(splitter)
