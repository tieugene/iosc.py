"""Main GUI"""
# 1. std
from typing import Any
import pathlib
# 2. 3rd
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QTabWidget
# 3. local
from mycomtrade import MyComtrade
from chart import ComtradeWidget


class ComtradeTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(ComtradeTabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self._chartviews = []
        self._chartdata = []
        self.tabCloseRequested.connect(self.handle_tab_close_request)
        # tab_bar = self.tabBar()
        # tab_bar.setSelectionBehaviorOnRemove(QTabBar.SelectPreviousTab)

    def add_chart_tab(self, path: pathlib.Path):
        rec = MyComtrade()
        rec.load(path)
        index = self.count()
        self._chartdata.append(rec)
        item = ComtradeWidget()
        self._chartviews.append(item)
        self.addTab(item, path.name)
        item.plot_charts(rec)
        self.setCurrentIndex(index)

    def handle_tab_close_request(self, index):
        if index >= 0 and self.count() >= 1:
            chartview = self._chartviews[index]
            self._chartviews.remove(chartview)
            chartdata = self._chartdata[index]
            self._chartdata.remove(chartdata)
            self.removeTab(index)

    def close_current_tab(self):
        self.handle_tab_close_request(self.currentIndex())

    def info_current_tab(self):
        def tr(name: str, value: Any):
            return f"<tr><th>{name}:</th><td>{value}</td></tr>"

        index = self.currentIndex()
        rec: MyComtrade = self._chartdata[index]
        msg = QMessageBox(QMessageBox.Icon.Information, "Comtrade file info", "Summary")
        # plan A:
        # msg.setDetailedText(rec.cfg_summary())
        # plan B
        txt = "<html><body><table><tbody>"
        txt += tr("File", rec.meta.filepath)
        txt += tr("Station name", rec.meta.station_name)
        txt += tr("Station id", rec.meta.rec_dev_id)
        txt += tr("Comtrade ver.", rec.meta.rev_year)
        txt += tr("File format", rec.meta.ft)
        txt += tr("AnalogSignal chs.", rec.analog.count)
        txt += tr("Digital chs.", rec.discret.count)
        txt += tr("Line freq, Hz", rec.meta.frequency)
        txt += tr("Time", f"{rec.meta.start_timestamp}&hellip;{rec.meta.trigger_timestamp}"
                          f" with &times; {rec.meta.timemult}")
        txt += tr("Time base", rec.meta.time_base)
        txt += tr("Samples", rec.meta.total_samples)
        # for i in range(rec.cfg.nrates):
        #    rate, points = rec.cfg.sample_rates[i]
        #    txt += tr(f"Sample #{i + 1}", f"{points} points at {rate} Hz")
        txt += "<tbody></table></body><html>"
        msg.setText(txt)
        msg.setTextFormat(Qt.RichText)
        # # /plan
        msg.exec_()


class MainWindow(QMainWindow):
    tabs: ComtradeTabWidget
    actOpen: QAction
    actClose: QAction
    actInfo: QAction
    actExit: QAction
    actAbout: QAction

    def __init__(self):
        super(MainWindow, self).__init__()
        self.create_widgets()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        self.setWindowTitle("iOsc.py")
        # actions handling

    def create_widgets(self):
        self.tabs = ComtradeTabWidget(self)
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
        self.actClose = QAction(QIcon.fromTheme("window-close"),  # TODO: disable if nobodu
                                "&Close",
                                self,
                                shortcut="Ctrl+W",
                                triggered=self.file_close)
        self.actInfo = QAction(QIcon.fromTheme("dialog-information"),
                               "&Info",
                               self,
                               shortcut="Ctrl+I",
                               triggered=self.file_info)
        self.actAbout = QAction(QIcon.fromTheme("help-about"),
                                "&About",
                                self,
                                statusTip="Show the application's About box",
                                triggered=self.about)

    def create_menus(self):
        menu_file = self.menuBar().addMenu("&File")
        menu_file.addAction(self.actOpen)
        menu_file.addAction(self.actClose)
        menu_file.addAction(self.actInfo)
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

    def file_info(self):
        if self.tabs.count() > 0:
            self.tabs.info_current_tab()

    def update_statusbar(self, s: str):
        self.statusBar().showMessage(s)
