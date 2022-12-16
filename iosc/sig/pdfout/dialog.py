"""Main print preview dialog"""
from typing import Optional

from PyQt5.QtCore import Qt
# 2. 3rd
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QActionGroup, QToolBar, QAction, QStyle
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrintPreviewWidget
# 3. local
from .pdfprinter import PdfPrinter
from .render import PlotPrint


class PDFOutPreviewDialog(QPrintPreviewDialog):
    __parent: 'ComtradeWidget'
    __render: Optional[PlotPrint]
    __1stime: bool
    __act_opt_values: QAction
    __act_opt_ptrs: QAction
    __actions_to_print: QActionGroup

    def __init__(self, __printer: PdfPrinter, parent: 'ComtradeWidget'):
        super().__init__(__printer, parent)
        self.__parent = parent
        self.__render = None
        self.__1stime = True
        self.__mk_actions()
        root_tb: QToolBar = self.findChildren(QToolBar)[0]
        root_tb.addAction(self.__act_opt_values)
        root_tb.addAction(self.__act_opt_ptrs)
        self.finished.connect(self.clean_up)
        self.setWindowModality(Qt.WindowModality.WindowModal)

    def __mk_actions(self):
        self.__act_opt_values = QAction(
            QIcon.fromTheme(
                "list-add",
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            ),
            "Print values",
            self,
            checkable=True,
            toggled=self.__slot_option_values
        )
        self.__act_opt_ptrs = QAction(
            QIcon.fromTheme(
                "insert-link",
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon)
            ),
            "Print pointers",
            self,
            checkable=True,
            toggled=self.__slot_option_ptrs
        )

    def __repreview(self):
        """Update preview.
        :note: workaround to find built-in QPrintPreviewWidget and force it to update
        """
        if (wdg := self.findChild(QPrintPreviewWidget)) is not None:
            wdg.updatePreview()

    def __slot_option_values(self, v: bool):
        self.printer().option_values = v
        self.__repreview()

    def __slot_option_ptrs(self, v: bool):
        self.printer().option_ptrs = v
        self.__repreview()

    def open(self):
        self.__render = PlotPrint(self.__parent)
        self.paintRequested.connect(self.__render.slot_paint_request)
        super().open()
        if self.__1stime:  # dirty hack
            self.__1stime = False
        else:
            self.__repreview()

    def clean_up(self):
        self.paintRequested.disconnect(self.__render.slot_paint_request)
        self.__render.deleteLater()
        self.__render = None
