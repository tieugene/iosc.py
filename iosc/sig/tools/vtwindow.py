"""Value table."""
# 2. 3rd
from PyQt5.QtWidgets import QTableWidget, QDialog, QVBoxLayout, QTableWidgetItem, QAbstractItemView
# 3. local
from iosc.core.sigfunc import func_list
# x. const
TYPE_NAME = ("As is", "Mid", "Eff", "H1", "H2", "H3", "H5")
CENTERED = False  # use not centered values


class ValueTable(QTableWidget):
    """Value table widget.

    Columns:
    - sid
    - type
    - Min
    - Max
    - MainPtr value (of Type)
    - TmpPtr[]
    """

    def __init__(self, oscwin: 'ComtradeWidget', parent: 'VTWindow'):  # noqa: F821
        """Init ValueTable object."""
        super().__init__(parent)
        self.setWordWrap(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setColumnCount(5 + len(oscwin.tmp_ptr_i))
        self.setRowCount(len(oscwin.osc.y))
        # 1. header
        h = ["Signal", "Type", "Min", "Max", "Main pointer"]
        for uid, r in oscwin.tmp_ptr_i.items():
            h.append("T%d (%.3f ms)" % (uid, oscwin.osc.x[r]))
        self.setHorizontalHeaderLabels(h)
        # 1.5.
        type_name = TYPE_NAME[oscwin.viewas]
        func = func_list[oscwin.viewas]
        spp = oscwin.osc.spp
        pors = oscwin.show_sec
        # 2. body
        for r, s in enumerate(oscwin.osc.y):
            self.setItem(r, 0, QTableWidgetItem(s.sid))  # 0. sig name
            if not s.is_bool:  # 1. type
                self.setItem(r, 1, QTableWidgetItem(type_name))
            self.setItem(r, 2, QTableWidgetItem(str(0 if s.is_bool else s.v_min(CENTERED))))  # 2. Min
            self.setItem(r, 3, QTableWidgetItem(str(1 if s.is_bool else s.v_max(CENTERED))))  # 3. Max
            if s.is_bool:  # 4. MainPtr
                v = str(s.value(oscwin.main_ptr_i))
            else:
                # v = s.as_str_full(func(s.value, oscwin.main_ptr_i, spp), pors)
                v = s.as_str_full(s.value(oscwin.main_ptr_i, CENTERED, pors, oscwin.viewas))
            self.setItem(r, 4, QTableWidgetItem(v))
            for c, tmp_i in enumerate(oscwin.tmp_ptr_i.values()):  # 5. TmpPtr[]
                if s.is_bool:
                    v = str(s.value(tmp_i))
                else:
                    # v = s.as_str_full(func(s.value, tmp_i, spp), pors)
                    v = s.as_str_full(s.value(tmp_i, CENTERED, pors, oscwin.viewas))
                self.setItem(r, c + 5, QTableWidgetItem(v))
        # 3. the end
        self.resizeRowsToContents()
        self.resizeColumnsToContents()


class VTWindow(QDialog):
    """Value table window."""

    def __init__(self, parent: 'ComtradeWidget'):  # noqa: F821
        """Init VTWindow object."""
        super().__init__(parent)
        self.setWindowTitle("Value table")
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(ValueTable(parent, self))
