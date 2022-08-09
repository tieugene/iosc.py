"""Main GUI"""
# 2. 3rd
from PySide2 import QtWidgets, QtGui
# 3. local
from comtrade import Comtrade


class MainWindow(QtWidgets.QMainWindow):
    # misc
    tabs: QtWidgets.QTabWidget
    # actions
    actOpen: QtWidgets.QAction
    actExit: QtWidgets.QAction
    actAbout: QtWidgets.QAction

    def __init__(self):
        super().__init__()
        self.create_widgets()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        self.setWindowTitle("iOsc.py")
        # actions handling

    def create_widgets(self):
        # order
        self.tabs = QtWidgets.QTabWidget()
        # that's all
        self.setCentralWidget(self.tabs)
        # attributes

    def create_actions(self):
        # noinspection PyArgumentList
        self.actExit = QtWidgets.QAction(QtGui.QIcon(':/icons/power-standby.svg'),
                                         "E&xit", self,
                                         shortcut="Ctrl+Q",
                                         statusTip="Exit the application",
                                         triggered=self.close)
        self.actOpen = QtWidgets.QAction(QtGui.QIcon(':/icons/cloud-download.svg'),
                                         "&Open", self,
                                         shortcut="Ctrl+O",
                                         statusTip="Load comtrade file",
                                         triggered=self.file_open)
        # noinspection PyArgumentList
        self.actAbout = QtWidgets.QAction(QtGui.QIcon(':/icons/question-mark.svg'),
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
        QtWidgets.QMessageBox.about(self, "About iOsc.py", "PySide2 powered comtrade viewer/analyzer.")

    def file_open(self):
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open data",
            "",
            "Comtrade Files (*.cfg *.cff)"
        )
        if fn[0]:
            rec = Comtrade()
            rec.load(fn[0])
            print("Trigger time = {}s".format(rec.trigger_time))
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(rec.time, rec.analog[0])
            plt.plot(rec.time, rec.analog[1])
            plt.legend([rec.analog_channel_ids[0], rec.analog_channel_ids[1]])
            plt.show()

    def update_statusbar(self, s: str):
        self.statusBar().showMessage(s)
