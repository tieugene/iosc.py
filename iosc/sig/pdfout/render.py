from PyQt5.QtGui import QPagedPaintDevice
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QAction


class PrintRender(QGraphicsView):
    __to_print: list[bool]

    def __init__(self, parent='ComtradeWidget'):
        super().__init__(parent)
        self.__to_print = [False] * 5
        self.setScene(QGraphicsScene())

    def set_to_print(self, a: QAction):
        i = a.data()
        v = a.isChecked()
        # print("Set #", i, "=>", v)
        self.__to_print[i] = v

    def print_(self, printer: QPrinter) -> None:
        ...
        # print("Printing started to", printer.pageRect(QPrinter.Millimeter), "mm, ", printer.pageRect(QPrinter.DevicePixel))
        # print(printer.pageRect(QPrinter.Millimeter))
        # recalc/transform, split by pages
        # use self.render()
