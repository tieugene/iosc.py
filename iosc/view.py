"""Main GUI"""
# 1. std
import sys
import pathlib
# 2. 3rd
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QTabWidget, QTabBar
import chardet
# 3. local
from comtrade import Comtrade
from chart import ChartsWidget


def comtrade_info(rec: Comtrade):
    # print("Trigger time = {}s".format(rec.trigger_time))
    print("Analog chs:", rec.analog_channel_ids)
    print("Status chs:", rec.status_channel_ids)
    # print("Digital chs:", rec.digital_channel_ids)  # depricated
    # print(rec.status[6])


class ChartsTabWidget(QTabWidget):
    def __init__(self, parent):
        super(ChartsTabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self._chartviews = []
        self.tabCloseRequested.connect(self.handle_tab_close_request)
        # tab_bar = self.tabBar()
        # tab_bar.setSelectionBehaviorOnRemove(QTabBar.SelectPreviousTab)

    def add_chart_tab(self, path: pathlib.Path):
        with open(path, 'rb') as infile:
            encoding = chardet.detect(infile.read())['encoding']
            print(f"Encoding: {encoding}")
        if encoding is None:
            sys.exit("Unknown encoding")
        rec = Comtrade()
        rec.load(str(path))  # encoding=encoding
        # comtrade_info(rec)
        item = ChartsWidget()
        index = self.count()
        self._chartviews.append(item)
        self.addTab(item, path.name)
        item.plot_chart(rec)
        self.setCurrentIndex(index)

    def handle_tab_close_request(self, index):
        if index >= 0 and self.count() >= 1:
            chartview = self._chartviews[index]
            self._chartviews.remove(chartview)
            self.removeTab(index)


class MainWindow(QMainWindow):
    tabs: ChartsTabWidget
    actOpen: QAction
    actExit: QAction
    actAbout: QAction

    def __init__(self):
        QMainWindow.__init__(self)
        self.create_widgets()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        self.setWindowTitle("iOsc.py")
        # actions handling

    def create_widgets(self):
        self.tabs = ChartsTabWidget(self)
        self.setCentralWidget(self.tabs)

    def create_actions(self):
        self.actExit = QAction(QIcon.fromTheme("application-exit"),
                               "E&xit",
                               self,
                               shortcut="Ctrl+Q",
                               statusTip="Exit the application",
                               triggered=self.close)
        self.actOpen = QAction(QIcon.fromTheme("document-open"),
                               "&Open",
                               self,
                               shortcut="Ctrl+O",
                               statusTip="Load comtrade file",
                               triggered=self.file_open)
        self.actAbout = QAction(QIcon.fromTheme("help-about"),
                                "&About",
                                self,
                                statusTip="Show the application's About box",
                                triggered=self.about)

    def create_menus(self):
        menu_file = self.menuBar().addMenu("&File")
        menu_file.addAction(self.actOpen)
        menu_file.addAction(self.actExit)
        menu_help = self.menuBar().addMenu("&Help")
        menu_help.addAction(self.actAbout)

    def create_toolbars(self):
        self.addToolBar("File")

    def create_statusbar(self):
        self.statusBar().showMessage("Ready")

    # actions
    def about(self):
        QMessageBox.about(self, "About iOsc.py", "PySide2 powered comtrade viewer/analyzer.")

    def file_open(self):
        fn = QFileDialog.getOpenFileName(
            self,
            "Open data",
            "",
            "Comtrade Files (*.cfg *.cff)"
        )
        if fn[0]:
            self.tabs.add_chart_tab(pathlib.Path(fn[0]))

    def update_statusbar(self, s: str):
        self.statusBar().showMessage(s)
