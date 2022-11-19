"""PDF print preview."""
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrinter
from PyQt5.QtWidgets import QToolBar, QToolButton, QMenu, QAction, QActionGroup
# 3. local
from iosc.sig.pdfout.render import PrintRender
# x. const
TO_PRINT = (
    "Print b/w",
    "Print signal names",
    "Print scale coefficient",
    "Print pointers",
    "Print signal values at main pointer"
)


class PDFOutPreviewDialog(QPrintPreviewDialog):
    __render: PrintRender
    __actions_to_print: QActionGroup
    __tb_to_print: QToolButton

    def __init__(self, printer: QPrinter, render: PrintRender, parent='ComtradeWidget'):
        super().__init__(printer, parent)
        self.__render = render
        self.__mk_actions()
        self.__mk_custom_menu()
        self.findChildren(QToolBar)[0].addWidget(self.__tb_to_print)
        # connections
        self.__actions_to_print.triggered.connect(self.__render.set_to_print)
        self.paintRequested.connect(self.__render.print_)

    def __mk_actions(self):
        self.__actions_to_print = QActionGroup(self)
        self.__actions_to_print.setExclusive(False)
        for i, s in enumerate(TO_PRINT):
            self.__actions_to_print.addAction(QAction(s, self, checkable=True, )).setData(i)

    def __mk_custom_menu(self):
        # FIXME: add icon or text
        self.__tb_to_print = QToolButton(self)
        self.__tb_to_print.setPopupMode(QToolButton.MenuButtonPopup)
        self.__tb_to_print.setMenu(QMenu())
        self.__tb_to_print.menu().addActions(self.__actions_to_print.actions())
