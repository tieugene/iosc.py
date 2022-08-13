"""Main GUI"""
# 1. std
import sys
import pathlib
# 2. 3rd
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QTabWidget
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
        encoding = None
        if path.suffix.lower() == '.cfg':
            with open(path, 'rb') as infile:
                if (enc := chardet.detect(infile.read())['encoding']) not in {'ascii', 'utf-8'}:
                    encoding = enc
        rec = Comtrade()
        if encoding:
            rec.load(str(path), encoding=encoding)
        else:
            rec.load(str(path))
        # comtrade_info(rec)
        index = self.count()
        item = ChartsWidget()
        self._chartviews.append(item)
        self.addTab(item, path.name)
        item.plot_chart(rec)
        self.setCurrentIndex(index)

    def handle_tab_close_request(self, index):
        if index >= 0 and self.count() >= 1:
            chartview = self._chartviews[index]
            self._chartviews.remove(chartview)
            self.removeTab(index)

    def close_current_tab(self):
        self.handle_tab_close_request(self.currentIndex())


class MainWindow(QMainWindow):
    tabs: ChartsTabWidget
    actOpen: QAction
    actClose: QAction
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
        self.actClose = QAction(QIcon.fromTheme("window-close"),
                                "&Close",
                                self,
                                shortcut="Ctrl+W",
                                triggered=self.file_close)
        self.actAbout = QAction(QIcon.fromTheme("help-about"),
                                "&About",
                                self,
                                statusTip="Show the application's About box",
                                triggered=self.about)

    def create_menus(self):
        menu_file = self.menuBar().addMenu("&File")
        menu_file.addAction(self.actOpen)
        menu_file.addAction(self.actClose)
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

    def file_close(self):
        if self.tabs.count() > 0:
            self.tabs.close_current_tab()
        # else:
        #    self.close()  # TODO: disable ^W

    def update_statusbar(self, s: str):
        self.statusBar().showMessage(s)
