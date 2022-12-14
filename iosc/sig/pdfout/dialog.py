"""Main print preview dialog"""
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
        self.__actions_to_print.addAction(QAction(
            "Print values",
            self,
            checkable=True,
            toggled=self.__slot_set_2lines
        ))

    def __mk_custom_menu(self):
        self.__tb_to_print = QToolButton(self)
        self.__tb_to_print.setIcon(QIcon.fromTheme(
            "emblem-important",
            self.style().standardIcon(QStyle.StandardPixmap.SP_ToolBarVerticalExtensionButton)
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

    def __slot_set_2lines(self, v: bool):
        self.printer().option_2lines = v
        self.__repreview()

    def exec_(self):
        """Exec print dialog from Print action activated until Esc (0) or 'OK' (print) pressed."""
        rndr = PlotPrint(self.__parent.analog_table.bars)  # FIXME: += status_table
        self.paintRequested.connect(rndr.slot_paint_request)
        return super().exec_()
        # self.paintRequested.disconnect(rndr.slot_paint_request)  # not required
        # rndr.deleteLater()  # or `del rndr`; not required
