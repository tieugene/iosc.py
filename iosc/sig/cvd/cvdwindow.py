"""Circular Vector Diagram"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
# 2. 3rd
from PyQt5.QtWidgets import QDialog, QTableWidget, QWidget, QAction, QVBoxLayout, QToolBar, QSplitter, QGraphicsView


class CVDiagram(QGraphicsView):
    def __init__(self, parent: 'CVDWindow'):
        super().__init__(parent)


class CVTable(QTableWidget):
    def __init__(self, parent: 'CVDWindow'):
        super().__init__(parent)
        self.setColumnCount(6)
        self.horizontalHeader().setStretchLastSection(True)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalHeaderLabels(("№", "Name", "Module", "Angle", "Re", "Im"))
        self.resizeRowsToContents()


class CVDWindow(QDialog):
    """Main CVD window.
    Buttons (custom toolbar):
    - Window: close, expand/restore, menu
    - menu:
      + Settings
      + Time:
        * MainPtr
        * Tx[]
    """
    toobar: QToolBar
    diagram: CVDiagram
    table: CVTable
    action_settings: QAction
    action_select_ptr: QAction
    action_close: QAction

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.__mk_widgets()
        self.__mk_layout()
        self.__mk_actions()
        self.__mk_toolbar()
        self.setWindowTitle("Vector Diagram")

    def __mk_widgets(self):
        self.toolbar = QToolBar(self)
        self.diagram = CVDiagram(self)
        self.table = CVTable(self)

    def __mk_layout(self):
        """Layout:
        - toolbar
        - plot
        - table
        """
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        splitter.addWidget(self.diagram)
        splitter.addWidget(self.table)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(splitter)

    def __mk_actions(self):
        self.action_settings = QAction(QIcon.fromTheme("document-properties"),
                                       "&Settings",
                                       self,
                                       triggered=self.__do_settings)
        self.action_select_ptr = QAction(QIcon.fromTheme("go-jump"),
                                         "&Pointer",
                                         self,
                                         triggered=self.__do_select_ptr)
        self.action_close = QAction(QIcon.fromTheme("window-close"),
                                    "&Close",
                                    self,
                                    triggered=self.close)

    def __mk_toolbar(self):
        self.toolbar.addAction(self.action_settings)
        self.toolbar.addAction(self.action_select_ptr)
        self.toolbar.addAction(self.action_close)

    def __do_settings(self):
        ...

    def __do_select_ptr(self):
        ...
