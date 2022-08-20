# 2. 3rd
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter
# 3. local
import mycomtrade
from draft.siglist_vbl import SignalListView


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
        splitter.addWidget(self.analog_panel)
        # 2. digital part
        self.discret_panel = SignalListView(rec.discret)
        splitter.addWidget(self.discret_panel)
        # 3. lets go
        self.layout().addWidget(splitter)
