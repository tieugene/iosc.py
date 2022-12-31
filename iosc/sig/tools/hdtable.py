"""Harmonic diagram table."""
# 2. 3rd
from PyQt5.QtWidgets import QWidget, QVBoxLayout
# 3. local
from iosc.sig.tools.hdbar import HDBar


class HDTable(QWidget):
    """Harmonic diagram table."""

    hdwin: 'HDWindow'  # noqa: F821; functional parent

    def __init__(self, parent: 'HDWindow'):  # noqa: F821
        """Init HDTable object."""
        super().__init__(parent)
        self.hdwin = parent
        # self.setStyleSheet("border: 1px solid red")
        self.setLayout(QVBoxLayout())

    def __clear(self):
        """Remove all bars.

        (like a hack)
        """
        while item := self.layout().takeAt(0):
            if v := item.widget():
                v.deleteLater()
            del item  # mostly QWidgetItem
        # self.layout().children().clear()

    def reload_signals(self):
        """Reload all signals on demand."""
        self.__clear()
        if self.hdwin.ss_used:
            for ss in self.hdwin.ss_used:
                self.layout().addWidget(HDBar(ss, self))
            self.layout().addStretch(0)
