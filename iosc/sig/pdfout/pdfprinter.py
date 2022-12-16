from PyQt5.QtPrintSupport import QPrinter

from .const import PORTRAIT


class PdfPrinter(QPrinter):
    option_values: bool
    option_ptrs: bool

    def __init__(self):
        super().__init__(QPrinter.PrinterMode.HighResolution)
        self.option_values = False
        self.option_ptrs = False
        self.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        self.setResolution(100)
        self.setPageMargins(10, 10, 10, 10, QPrinter.Unit.Millimeter)
        self.setOrientation(QPrinter.Orientation.Portrait if PORTRAIT else QPrinter.Orientation.Landscape)
