"""PDF print preview."""
from PyQt5.QtPrintSupport import QPrintPreviewDialog


class PDFOutPreviewDialog(QPrintPreviewDialog):
    """TODO:
    - Color/black (QCheckBox)
    - What to print (4 x Checkboxes)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
