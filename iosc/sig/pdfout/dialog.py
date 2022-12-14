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
    __actions_to_print: QActionGroup
    __tb_to_print: QToolButton

    def __init__(self, __printer: PdfPrinter, parent: 'ComtradeWidget'):
        super().__init__(__printer)
        self.__parent = parent
        self.__mk_actions()
        self.__mk_custom_menu()
        self.findChildren(QToolBar)[0].addWidget(self.__tb_to_print)

    def __mk_actions(self):
        self.__actions_to_print = QActionGroup(self)
        self.__actions_to_print.setExclusive(False)
        self.__actions_to_print.addAction(QAction("…values", self, checkable=True, toggled=self.__slot_option_values))
        self.__actions_to_print.addAction(QAction("…pointers", self, checkable=True, toggled=self.__slot_option_ptrs))

    def __mk_custom_menu(self):
        self.__tb_to_print = QToolButton(self)
        self.__tb_to_print.setArrowType(Qt.ArrowType.DownArrow)
        self.__tb_to_print.setText("Print…")
        self.__tb_to_print.setIcon(QIcon.fromTheme(
            "emblem-important", self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)
            ))
        self.__tb_to_print.setPopupMode(QToolButton.MenuButtonPopup)
        self.__tb_to_print.setMenu(QMenu())
        self.__tb_to_print.menu().addActions(self.__actions_to_print.actions())

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
        return super().exec_()
        # self.paintRequested.disconnect(rndr.slot_paint_request)  # not required
        # rndr.deleteLater()  # or `del rndr`; not required
