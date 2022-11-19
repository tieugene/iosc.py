from PyQt5.QtGui import QPagedPaintDevice
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsView


class PrintRender(QGraphicsView):
    def __init__(self, parent='ComtradeWidget'):
        super().__init__(parent)

    def print_(self, printer: QPagedPaintDevice) -> None:
        print("Printing started...")
        # recalc/transform, split
        # self.render()
