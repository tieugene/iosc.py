"""Main GUI"""
# 1. std
import pathlib
import sys

# 2. 3rd
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QToolBar, QWidget, QHBoxLayout, QApplication
# 3. local
from maintabber import ComtradeTabWidget, MAIN_TAB

# x. const
MAIN_MENU = True  # FIXME: False => hot keys not work


class MainWindow(QMainWindow):
    tabs: ComtradeTabWidget
    act_bar: QToolBar
    actFileOpen: QAction
    actExit: QAction
    actAbout: QAction

    def __init__(self, _: list):
        super().__init__()
        self.create_widgets()
        self.create_actions()
        self.create_menus()
        self.__mk_layout()
        self.setWindowTitle("iOsc.py")
        # self.handle_cli()

    def create_widgets(self):
        self.tabs = ComtradeTabWidget(self)
        self.setCentralWidget(self.tabs)
        self.act_bar = QToolBar(self)

    def create_actions(self):
        self.actExit = QAction(QIcon.fromTheme("application-exit"),
                               "E&xit",
                               self,
                               shortcut="Ctrl+Q",
                               statusTip="Exit the application",
                               triggered=self.close)
        self.actAbout = QAction(QIcon.fromTheme("help-about"),
                                "&About",
                                self,
                                statusTip="Show the application's About box",
                                triggered=self.do_about)
        self.actFileOpen = QAction(QIcon.fromTheme("document-open"),
                                   "&Open",
                                   self,
                                   shortcut="Ctrl+O",
                                   statusTip="Load comtrade file",
                                   triggered=self.do_file_open)

    def create_menus(self):
        menu_file = self.menuBar().addMenu("&File")
        menu_file.addAction(self.actFileOpen)
        menu_file.addAction(self.actExit)
        self.menuBar().setVisible(MAIN_MENU)
        self.act_bar.addAction(self.actFileOpen)
        self.act_bar.addAction(self.actAbout)
        self.act_bar.addAction(self.actExit)
        self.act_bar.setOrientation(Qt.Vertical)
        self.act_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

    def __mk_layout(self):
        main_tab = QWidget()
        main_tab.setLayout(QHBoxLayout())
        main_tab.layout().addWidget(self.act_bar)
        main_tab.layout().addWidget(QWidget())
        if MAIN_TAB:
            self.tabs.addTab(main_tab, "File")

    def handle_cli(self):
        """Process CLI arg.
        :this can be slot
        """
        argv = QCoreApplication.arguments()
        if len(argv) > 2:
            QMessageBox.warning(self, "CLI error", "One file only")
        elif len(argv) == 2:
            file = pathlib.Path(argv[1])
            if not file.is_file():
                QMessageBox.warning(self, "CLI error", f"'{file}' not exists or is not file")
            else:
                self.tabs.add_chart_tab(file)

    # actions
    def do_about(self):
        QMessageBox.about(self, "About iOsc.py", "Qt powered comtrade viewer/analyzer.")

    def do_file_open(self):
        fn = QFileDialog.getOpenFileName(
            self,
            "Open data",
            "",
            "Comtrade Files (*.cfg *.cff)"
        )
        if fn[0]:
            self.tabs.add_chart_tab(pathlib.Path(fn[0]))


def main() -> int:
    # QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    mw: QMainWindow = MainWindow(sys.argv)
    available_geometry = app.desktop().availableGeometry(mw)  # 0, 0, 1280, 768 (display height - taskbar)
    mw.resize(int(available_geometry.width() * 3 / 4), int(available_geometry.height() * 3 / 4))
    mw.show()
    mw.handle_cli()
    return app.exec_()
