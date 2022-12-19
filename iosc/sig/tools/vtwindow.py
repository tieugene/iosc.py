"""Value table"""
# 2. 3rd
from PyQt5.QtWidgets import QTableWidget, QDialog, QVBoxLayout, QTableWidgetItem, QAbstractItemView

from iosc.core.sigfunc import func_list

# x. const
TYPE_NAME = ("As is", "Mid", "Eff", "H1", "H2", "H3", "H5")


class ValueTable(QTableWidget):
    """Columns:
    - sid
    - type
    - Min
    - Max
    - MainPtr value (of Type)
    - TmpPtr[]
    """
    def __init__(self, oscwin: 'ComtradeWidget', parent: 'VTWindow'):
        super().__init__(parent)
        self.setWordWrap(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setColumnCount(5 + len(oscwin.tmp_ptr_i))
        self.setRowCount(len(oscwin.osc.y))
        # 1. header
        h = ["Signal", "Type", "Min", "Max", "Main pointer"]
        for k, v in oscwin.tmp_ptr_i.items():
            h.append("Name, time")
        self.setHorizontalHeaderLabels(h)
        # 1.5.
        type_name = TYPE_NAME[oscwin.viewas]
        func = func_list[oscwin.viewas]
        spp = oscwin.osc.spp
        pors = oscwin.show_sec
        # 2. body
        for i, s in enumerate(oscwin.osc.y):
            self.setItem(i, 0, QTableWidgetItem(s.sid))  # 0. sig name
            if not s.is_bool:  # 1. type
                self.setItem(i, 1, QTableWidgetItem(type_name))
            self.setItem(i, 2, QTableWidgetItem(str(0 if s.is_bool else s.v_min)))  # 2. Min
            self.setItem(i, 3, QTableWidgetItem(str(1 if s.is_bool else s.v_max)))  # 3. Max
            if s.is_bool:  # 4. MainPtr
                v = str(s.value[oscwin.main_ptr_i])
            else:
                v = s.as_str_full(func(s.value, oscwin.main_ptr_i, spp), pors)
            self.setItem(i, 4, QTableWidgetItem(v))
            # 6. TmpPtr[]
        # 3. the end
        self.resizeRowsToContents()
        self.resizeColumnsToContents()


class VTWindow(QDialog):
    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.setWindowTitle("Value table")
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(ValueTable(parent, self))
