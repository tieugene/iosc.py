# 2. 3rd
from PyQt5.QtWidgets import QWidget, QVBoxLayout
# 3. local
from iosc.sig.tools.hdbar import HDBar


class HDTable(QWidget):
    hdwin: 'HDWindow'  # functional parent

    def __init__(self, parent: 'HDWindow'):
        super().__init__(parent)
        self.hdwin = parent
        # self.setStyleSheet("border: 1px solid red")
        self.setLayout(QVBoxLayout())

    def reload_signals(self):
        self.layout().children().clear()
        if self.hdwin.ss_used:
            for ss in self.hdwin.ss_used:
                self.layout().addWidget(HDBar(ss, self))
            self.layout().addStretch(0)
