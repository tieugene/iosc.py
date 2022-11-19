"""PDF print preview."""
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrinter


class PDFOutPreviewDialog(QPrintPreviewDialog):
    """TODO:
    - Color/black (QCheckBox)
    - What to print (4 x Checkboxes)
    """
    def __init__(self, printer: QPrinter, parent='ComtradeWidget'):
        super().__init__(printer, parent)
        self.paintRequested.connect(parent.pdfout.print_)
