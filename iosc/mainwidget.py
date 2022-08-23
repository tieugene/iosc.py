# 2. 3rd
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget
# 3. local
import mycomtrade
from siglist_tw import SignalListView
# from draft.siglist_vbl import SignalListView
# x. const
TICK_RANGE = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000)
TICS_PER_CHART = 20


def find_std_ti(ti: int):
    for i in TICK_RANGE:
        if i >= ti:
            return i
    return TICK_RANGE[-1]


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
        # 0. calc tick interval
        ti_wanted = int(rec.meta.total_samples * (1000/rec.rate[0][0]) / TICS_PER_CHART)  # ms
        ti = find_std_ti(ti_wanted)
        # print(f"{ti_wanted} => {ti}")
        # 1. analog part
        self.analog_panel = SignalListView(rec.analog, ti, self)
        splitter.addWidget(self.analog_panel)
        # 2. digital part
        self.discret_panel = SignalListView(rec.discret, ti, self)
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
