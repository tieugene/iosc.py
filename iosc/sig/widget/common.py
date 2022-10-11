"""Signal widgets (chart, ctrl panel).
TODO: try __slots__"""
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QScrollArea


class CleanScrollArea(QScrollArea):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
