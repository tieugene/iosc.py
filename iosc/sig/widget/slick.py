"""Signal wrappers, commmon things.

TODO: move up (../
"""
# 1. std
# 2. 3rd
from PyQt5.QtCore import QMargins, Qt
from PyQt5.QtWidgets import QWidget, QScrollBar, QLabel, QHBoxLayout
from QCustomPlot_PyQt5 import QCustomPlot
# 3. local
import iosc.const


class SlickPanelPlot(QCustomPlot):
    """Parent for top/bottom bars plots."""

    def __init__(self, parent: QWidget):
        """Init OneBarPlot object."""
        super().__init__(parent)
        ar = self.axisRect(0)
        ar.setMinimumMargins(QMargins())  # the best
        ar.removeAxis(self.yAxis)
        ar.removeAxis(self.xAxis2)
        ar.removeAxis(self.yAxis2)
        self.xAxis.grid().setVisible(False)
        # self.xAxis.setTickLabels(True)  # default
        # self.xAxis.setTicks(True)  # default
        self.xAxis.setPadding(0)
        self.setFixedHeight(24)
        # self.xAxis.setRange(self.oscwin.osc.x_min, self.oscwin.osc.x_max)
        self.addLayer("tips")  # default 6 layers (from bottom (0)): background>grid>main>axes>legend>overlay

    @property
    def _oscwin(self) -> 'ComtradeWidget':  # noqa: F821
        return self.parent().parent()

    def slot_rerange(self):
        """Recalc plot x-range."""
        x_coords = self._oscwin.osc.x
        x_width = self._oscwin.osc.x_size
        self.xAxis.setRange(
            x_coords[0] + self._oscwin.xscroll_bar.norm_min * x_width,
            x_coords[0] + self._oscwin.xscroll_bar.norm_max * x_width,
        )

    def slot_rerange_force(self):
        """Recalc plot x-range and force replot it."""
        self.slot_rerange()
        self.replot()


class SlickPanelWidget(QWidget):
    """Base for top/bottom panels."""

    class RStub(QScrollBar):
        """Right stub to align against signal bars."""

        def __init__(self, parent: 'SlickPanelWidget' = None):
            """Init RStub object."""
            super().__init__(Qt.Vertical, parent)
            self.setFixedHeight(0)

    _label: QLabel
    plot: SlickPanelPlot

    def __init__(self, parent: 'ComtradeWidget'):  # noqa: F821
        """Init OneRowBar object."""
        super().__init__(parent)
        self._label = QLabel(self)

    def _post_init(self):
        # layout
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self._label)
        self.layout().addWidget(self.plot)
        self.layout().addWidget(self.RStub())
        self.layout().addWidget(self.RStub())
        # squeeze
        self.layout().setContentsMargins(QMargins())
        self.layout().setSpacing(0)
        self._label.setContentsMargins(QMargins())
        # init sizes
        self.__slot_resize_col_ctrl(self.parent().col_ctrl_width)
        self.parent().signal_resize_col_ctrl.connect(self.__slot_resize_col_ctrl)

    def __slot_resize_col_ctrl(self, x: int):
        self._label.setFixedWidth(x + iosc.const.LINE_CELL_SIZE)
