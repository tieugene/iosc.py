"""Main print preview dialog"""
from PyQt5.QtCore import Qt
# 2. 3rd
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QActionGroup, QToolButton, QToolBar, QAction, QStyle, QMenu
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrintPreviewWidget
# 3. local
from .pdfprinter import PdfPrinter
from .render import PlotPrint


class PDFOutPreviewDialog(QPrintPreviewDialog):
    __parent: 'ComtradeWidget'
    __act_opt_values: QAction
    __act_opt_ptrs: QAction
    __actions_to_print: QActionGroup
    __tb_to_print: QToolButton

    def __init__(self, __printer: PdfPrinter, parent: 'ComtradeWidget'):
        super().__init__(__printer)
        self.__parent = parent
        self.__mk_actions()
        root_tb: QToolBar = self.findChildren(QToolBar)[0]
        root_tb.addAction(self.__act_opt_values)
        root_tb.addAction(self.__act_opt_ptrs)

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

    def exec_(self):
        """Exec print dialog from Print action activated until Esc (0) or 'OK' (print) pressed."""
        rndr = PlotPrint(self.__parent)  # FIXME: += status_table
        self.paintRequested.connect(rndr.slot_paint_request)
        retvalue = super().exec_()
        # self.paintRequested.disconnect(rndr.slot_paint_request)  # not required
        # rndr.deleteLater()  # or `del rndr`; not required
        # del rndr
        return retvalue
