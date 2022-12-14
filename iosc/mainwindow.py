"""Main application Window."""
# 1. std
import pathlib
import sys
# 2. 3rd
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QToolBar, QWidget, QHBoxLayout, QApplication
# 3. local
from _version import __version__
from maintabber import ComtradeTabWidget, MAIN_TAB

# x. const
MAIN_MENU = True  # FIXME: False => hot keys not work
ABOUT_STR = '''Qt powered comtrade viewer/analyzer.<br/>
Version: %s<br/>
Developed for <a href="https://ntkpribor.ru/">&laquo;NTK Priborenergo&raquo;, Ltd.</a><br/>
<sub>&copy; <a href="https://www.eap.su">TI_Eugene</a></sub>'''


class MainWindow(QMainWindow):
    """Main application window."""

    tabs: ComtradeTabWidget
    act_bar: QToolBar
    act_file_open: QAction
    act_exit: QAction
    act_about: QAction

    def __init__(self, _: list):
        """Init MainWindow object."""
        super().__init__()
        self.__mk_widgets()
        self.__mk_actions()
        self.__mk_menu()
        self.__mk_layout()
        self.setWindowTitle("iOsc.py")
        # self.handle_cli()

    def __mk_widgets(self):
        """Create child widgets."""
        self.tabs = ComtradeTabWidget(self)
        self.setCentralWidget(self.tabs)
        # self.act_bar = QToolBar(self)

    def __mk_actions(self):
        """Create qctions required."""
        # noinspection PyArgumentList
        self.act_exit = QAction(QIcon.fromTheme("application-exit"),
                                "E&xit",
                                self,
                                shortcut="Ctrl+Q",
                                statusTip="Exit the application",
                                triggered=self.close)
        # noinspection PyArgumentList
        self.act_about = QAction(QIcon.fromTheme("help-about"),
                                 "&About",
                                 self,
                                 statusTip="Show the application's About box",
                                 triggered=self.__do_about)
        # noinspection PyArgumentList
        self.act_file_open = QAction(QIcon.fromTheme("document-open"),
                                     "&Open",
                                     self,
                                     shortcut="Ctrl+O",
                                     statusTip="Load comtrade file",
                                     triggered=self.__do_file_open)

    def __mk_menu(self):
        """Create main application menu."""
        self.menuBar().addMenu("&File").addActions((
            self.act_file_open,
            self.act_exit
        ))
        self.menuBar().addMenu("&Help").addAction(self.act_about)
        self.menuBar().setVisible(MAIN_MENU)
        # self.act_bar.addAction(self.actFileOpen)
        # self.act_bar.addAction(self.actAbout)
        # self.act_bar.addAction(self.actExit)
        # self.act_bar.setOrientation(Qt.Vertical)
        # self.act_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

    def __mk_layout(self):
        """Lay out child widgets."""
        main_tab = QWidget()
        main_tab.setLayout(QHBoxLayout())
        # main_tab.layout().addWidget(self.act_bar)
        main_tab.layout().addWidget(QWidget())
        if MAIN_TAB:
            self.tabs.addTab(main_tab, "File")

    def handle_cli(self):
        """Process CLI arg."""
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
    def __do_about(self):
        """Show 'About' message box."""
        # QMessageBox.about(self, "About iOsc.py", ABOUT_STR)
        dialog = QMessageBox(QMessageBox.Information, "About iOsc.py", ABOUT_STR % __version__, QMessageBox.Ok, self)
        dialog.setTextFormat(Qt.RichText)
        dialog.exec_()

    def __do_file_open(self):
        """Open comtrade file."""
        fn = QFileDialog.getOpenFileName(
            self,
            "Open data",
            "",
            "Comtrade Files (*.cfg *.cff)"
        )
        if fn[0]:
            self.tabs.add_chart_tab(pathlib.Path(fn[0]))


def main() -> int:
    """Application entry point."""
    # QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationVersion(__version__)
    mw: MainWindow = MainWindow(sys.argv)
    available_geometry = app.desktop().availableGeometry(mw)  # 0, 0, 1280, 768 (display height - taskbar)
    mw.resize(int(available_geometry.width() * 3 / 4), int(available_geometry.height() * 3 / 4))
    mw.show()
    mw.handle_cli()
    return app.exec_()
