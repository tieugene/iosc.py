import cmath
import math

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

TABLE_HEAD = ("Name", "Module", "Angle", "Re", "Im")


class CVDTable(QTableWidget):
    __parent: 'CVDWindow'
    __trace_items: bool  # process item changing

    def __init__(self, parent: 'CVDWindow'):
        super().__init__(parent)
        self.__parent = parent
        self.__trace_items = False
        self.setColumnCount(len(TABLE_HEAD))
        self.horizontalHeader().setStretchLastSection(True)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalHeaderLabels(TABLE_HEAD)
        self.setSelectionMode(self.NoSelection)
        self.resizeRowsToContents()
        self.itemChanged.connect(self.__slot_item_chgd)

    def reload_signals(self):
        """Reload rows from selected signals."""
        self.__trace_items = False
        self.setRowCount(len(self.__parent.ss_used))  # all items can be None
        for r, ss in enumerate(self.__parent.ss_used):
            for c in range(self.columnCount()):
                if self.item(r, c) is None:
                    self.setItem(r, c, QTableWidgetItem())
                    if c:
                        self.item(r, c).setTextAlignment(Qt.AlignRight)
            self.item(r, 0).setCheckState(Qt.Checked)
            self.item(r, 0).setText(ss.signal.sid)
            self.item(r, 0).setForeground(ss.color)
        self.refresh_signals()
        self.resizeColumnsToContents()

    def refresh_signals(self):
        """Refresh row values by ptr"""
        self.__trace_items = False
        i = self.__parent.t_i
        for r, ss in enumerate(self.__parent.ss_used):
            v: complex = ss.hrm(1, i)
            uu = ss.signal.raw2.uu
            self.item(r, 1).setText("%.1f %s" % (abs(v), uu))
            self.item(r, 2).setText("%.1f°" % math.degrees(cmath.phase(v)))
            self.item(r, 3).setText("%.1f %s" % (v.real, uu))
            self.item(r, 4).setText("%.1f %s" % (v.imag, uu))
        self.__trace_items = True

    def __slot_item_chgd(self, item: QTableWidgetItem):
        if self.__trace_items and item.column() == 0:
            self.__parent.chart.circle.sv_show(item.row(), item.checkState() == Qt.Checked)
