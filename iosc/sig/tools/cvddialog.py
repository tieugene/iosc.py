"""CVD dialog."""
# 1. std
from typing import Optional
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QComboBox, QLabel
# 3. local
from iosc.sig.widget.dialog import SelectSignalsDialog


class SelectCVDSignalsDialog(SelectSignalsDialog):
    """Select signals to show and base signal."""

    f_base_signal: QComboBox

    def __init__(
            self,
            ass_list: list['AnalogSignalSuit'],  # noqa: F821
            ass_used: set[int],
            ass_base: int = 0,
            parent=None
    ):
        """Init SelectCVDSignalsDialog object."""
        super().__init__(ass_list, ass_used, parent)
        self.f_base_signal = QComboBox(self)
        for i, ss in enumerate(ass_list):
            pixmap = QPixmap(16, 16)
            pixmap.fill(ss.color)
            self.f_base_signal.addItem(QIcon(pixmap), ss.signal.sid)
        if ass_base is not None:
            self.f_base_signal.setCurrentIndex(ass_base)
        self.layout().insertWidget(2, QLabel("Base:", self))
        self.layout().insertWidget(3, self.f_base_signal)

    def execute(self) -> Optional[tuple[list[int], int]]:
        """Open dialog and return result.

        :return: None if Cancel, list of selected items if ok
        """
        if self.exec_():
            retlist = list()
            for i in range(self.f_signals.count()):
                if self.f_signals.item(i).checkState() == Qt.Checked:
                    retlist.append(i)
            retval = self.f_base_signal.currentIndex()
            return retlist, retval
