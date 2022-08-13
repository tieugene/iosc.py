"""Main GUI"""
# 1. std
import sys
import pathlib
# 2. 3rd
from typing import Any

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QTabWidget
import chardet
# 3. local
from comtrade import Comtrade
from chart import ChartsWidget


class ChartsTabWidget(QTabWidget):
    def __init__(self, parent):
        super(ChartsTabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self._chartviews = []
        self._chartdata = []
        self.tabCloseRequested.connect(self.handle_tab_close_request)
        # tab_bar = self.tabBar()
        # tab_bar.setSelectionBehaviorOnRemove(QTabBar.SelectPreviousTab)

    def add_chart_tab(self, path: pathlib.Path):
        encoding = None
        if path.suffix.lower() == '.cfg':
            with open(path, 'rb') as infile:
                if (enc := chardet.detect(infile.read())['encoding']) not in {'ascii', 'utf-8'}:
                    encoding = enc
        index = self.count()
        rec = Comtrade()
        if encoding:
            rec.load(str(path), encoding=encoding)
        else:
            rec.load(str(path))
        self._chartdata.append(rec)
        # TODO: store file path
        item = ChartsWidget()
        self._chartviews.append(item)
        self.addTab(item, path.name)
        item.plot_chart(rec)
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
        rec: Comtrade = self._chartdata[index]
        msg = QMessageBox(QMessageBox.Icon.Information, "Comtrade file info", "Summary")
        # plan A:
        # msg.setDetailedText(rec.cfg_summary())
        # plan B
        txt = "<html><body><table><tbody>"
        txt += tr("File", rec.cfg.filepath)
        txt += tr("Station name", rec.station_name)
        txt += tr("Station id", rec.rec_dev_id)
        txt += tr("Comtrade ver.", rec.rev_year)
        txt += tr("File format", rec.ft)
        txt += tr("Analog chs.", rec.analog_count)
        txt += tr("Digital chs.", rec.status_count)
        txt += tr("Line freq, Hz", rec.frequency)
        txt += tr("Time", f"{rec.start_timestamp}&hellip;{rec.trigger_timestamp} ({rec.trigger_time}')"
                          f" with mult. {rec.cfg.timemult}")
        txt += tr("Time base", rec.time_base)
        txt += tr("Samples", rec.total_samples)
        for i in range(rec.cfg.nrates):
            rate, points = rec.cfg.sample_rates[i]
            txt += tr(f"Sample #{i+1}", f"{points} points at {rate} Hz")
        txt += "<tbody></table></body><html>"
        msg.setText(txt)
        msg.setTextFormat(Qt.RichText)
        # # /plan
        msg.exec_()


class MainWindow(QMainWindow):
    tabs: ChartsTabWidget
    actOpen: QAction
    actClose: QAction
    actInfo: QAction
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
