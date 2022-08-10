"""Main GUI"""
# 1. std
import sys
# 2. 3rd
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QWidget, QVBoxLayout, QSizePolicy, \
    QSplitter
import chardet
# 3. local
from comtrade import Comtrade


class MainWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        splitter = QSplitter(self)
        self.panel_top = QWidget(splitter)
        self.panel_bottom = QWidget(splitter)
        splitter.addWidget(self.panel_top)
        splitter.addWidget(self.panel_bottom)
        splitter.setOrientation(Qt.Horizontal)
        # splitter.setStretchFactor(0, 0)
        # splitter.setStretchFactor(1, 0)
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    # misc
    central_wodget: MainWidget
    # actions
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
        # order
        self.central_wodget = MainWidget()
        # that's all
        self.setCentralWidget(self.central_wodget)
        # attributes

    def create_actions(self):
        # noinspection PyArgumentList
        self.actExit = QAction(QIcon(':/icons/power-standby.svg'),
                               "E&xit", self,
                               shortcut="Ctrl+Q",
                               statusTip="Exit the application",
                               triggered=self.close)
        self.actOpen = QAction(QIcon(':/icons/cloud-download.svg'),
                               "&Open", self,
                               shortcut="Ctrl+O",
                               statusTip="Load comtrade file",
                               triggered=self.file_open)
        # noinspection PyArgumentList
        self.actAbout = QAction(QIcon(':/icons/question-mark.svg'),
                                "&About", self,
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
            with open(fn[0], 'rb') as infile:
                encoding = chardet.detect(infile.read())['encoding']
            if encoding is None:
                sys.exit("Unknown encoding")
            rec = Comtrade()
            rec.load(fn[0], encoding=encoding)
            # print("Trigger time = {}s".format(rec.trigger_time))
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(rec.time, rec.analog[0])
            plt.plot(rec.time, rec.analog[1])
            plt.legend([rec.analog_channel_ids[0], rec.analog_channel_ids[1]])
            plt.show()

    def update_statusbar(self, s: str):
        self.statusBar().showMessage(s)
