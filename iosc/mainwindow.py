"""Main GUI"""
# 1. std
import struct
from typing import Any
import pathlib
# 2. 3rd
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon, QGuiApplication
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QTabWidget
# 3. local
from mycomtrade import MyComtrade
from mainwidget import ComtradeWidget
from convtrade import convert, ConvertError


class ComtradeTabWidget(QTabWidget):
    _chartview: list[ComtradeWidget]
    _chartdata: list[MyComtrade]

    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self._chartviews = []
        self._chartdata = []
        self.tabCloseRequested.connect(self.handle_tab_close_request)
        # tab_bar = self.tabBar()
        # tab_bar.setSelectionBehaviorOnRemove(QTabBar.SelectPreviousTab)

    def __misc(self):
        scr0 = QGuiApplication.screens()[0]
        # print("Screen:", QApplication.desktop().screenGeometry())  # depricated
        print("Screen:", scr0.geometry())  # 1280x800
        # print("Avail:", QApplication.desktop().availableGeometry())  # depricated
        print("Avail:", scr0.availableGeometry())  # 1280x768
        print("MainWin:", self.parent().width())  # 960 (== avail-320

    def add_chart_tab(self, path: pathlib.Path):
        """
        :note: If addTab() after show(), set .updatesEnabled = False B4 changes and = True after changes
         (to prevent flicker)
        """
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        self.setUpdatesEnabled(False)
        try:
            rec = MyComtrade(path)
        except struct.error as e:
            QMessageBox.critical(self, "Loading error", str(e))
        else:
            index = self.count()
            self._chartdata.append(rec)
            item = ComtradeWidget(rec, self)  # table width == 100
            self._chartviews.append(item)
            self.addTab(item, path.name)  # table width == 940 (CLI) | 100 (Open)
            self.setCurrentIndex(index)
            self.setUpdatesEnabled(True)  # table width == right
            # self.__misc()
            item.line_up(QGuiApplication.screens()[0].availableGeometry().width() - self.parent().width())
        finally:
            QGuiApplication.restoreOverrideCursor()

    def handle_tab_close_request(self, index):
        if index >= 0 and self.count() >= 1:
            chartview = self._chartviews[index]
            self._chartviews.remove(chartview)
            chartdata = self._chartdata[index]
            self._chartdata.remove(chartdata)
            self.removeTab(index)

    def current_tab_close(self):
        self.handle_tab_close_request(self.currentIndex())

    def current_tab_info(self):
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
        txt += tr("Digital chs.", rec.status.count)
        txt += tr("Line freq, Hz", rec.meta.frequency)
        txt += tr("Time", f"{rec.meta.start_timestamp}&hellip;{rec.meta.trigger_timestamp}"
                          f" with &times; {rec.meta.timemult}")
        txt += tr("Time base", rec.meta.time_base)
        txt += tr("Samples", rec.meta.total_samples)
        for i in range(rec.rate.count):
            rate, points = rec.rate[i]
            txt += tr(f"Sample #{i + 1}", f"{points} points at {rate} Hz")
        txt += "<tbody></table></body><html>"
        msg.setText(txt)
        msg.setTextFormat(Qt.RichText)
        # # /plan
        msg.exec_()

    def current_tab_convert(self):
        index = self.currentIndex()
        rec = self._chartdata[index]
        fn = QFileDialog.getSaveFileName(self, "Save file as %s" % {'ASCII': 'BINARY', 'BINARY': 'ASCII'}[rec.meta.ft])
        if fn[0]:
            try:
                convert(pathlib.Path(rec.meta.filepath), pathlib.Path(fn[0]))
            except ConvertError as e:
                QMessageBox.critical(self, "Converting error", str(e))

    def current_tab_unhide_all(self):
        index = self.currentIndex()
        self._chartviews[index].sig_unhide()


class MainWindow(QMainWindow):
    tabs: ComtradeTabWidget
    actFileOpen: QAction
    actFileClose: QAction
    actFileInfo: QAction
    actFileConvert: QAction
    actExit: QAction
    actAbout: QAction
    actSigUnhideAll: QAction

    def __init__(self, _: list, parent=None):
        super().__init__(parent)
        self.create_widgets()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        self.setWindowTitle("iOsc.py")
        # self.handle_cli()

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
        self.actAbout = QAction(QIcon.fromTheme("help-do_about"),
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
        self.actFileClose = QAction(QIcon.fromTheme("window-close"),  # TODO: disable if nobodu
                                    "&Close",
                                    self,
                                    shortcut="Ctrl+W",
                                    triggered=self.do_file_close)
        self.actFileInfo = QAction(QIcon.fromTheme("dialog-information"),
                                   "&Info",
                                   self,
                                   shortcut="Ctrl+I",
                                   triggered=self.do_file_info)
        self.actFileConvert = QAction(QIcon.fromTheme("document-save-as"),
                                      "&Save as...",
                                      self,
                                      shortcut="Ctrl+S",
                                      triggered=self.do_file_convert)
        self.actSigUnhideAll = QAction(QIcon.fromTheme("edit-undo"),
                                       "&Unhide all",
                                       self,
                                       statusTip="Show hidden channels",
                                       triggered=self.do_sig_unhide_all)

    def create_menus(self):
        menu_file = self.menuBar().addMenu("&File")
        menu_file.addAction(self.actFileOpen)
        menu_file.addAction(self.actFileClose)
        menu_file.addAction(self.actFileInfo)
        menu_file.addAction(self.actFileConvert)
        menu_file.addAction(self.actExit)
        menu_channel = self.menuBar().addMenu("&Channel")
        menu_channel.addAction(self.actSigUnhideAll)
        menu_help = self.menuBar().addMenu("&Help")
        menu_help.addAction(self.actAbout)

    def create_toolbars(self):
        self.addToolBar("File")

    def create_statusbar(self):
        self.statusBar().showMessage("Ready")

    def update_statusbar(self, s: str):
        self.statusBar().showMessage(s)

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

    def do_file_close(self):
        if self.tabs.count() > 0:
            self.tabs.current_tab_close()
        # else:
        #    self.close()  # TODO: disable ^W

    def do_file_info(self):
        if self.tabs.count() > 0:
            self.tabs.current_tab_info()

    def do_file_convert(self):
        if self.tabs.count() > 0:
            self.tabs.current_tab_convert()

    def do_sig_unhide_all(self):
        if self.tabs.count() > 0:
            self.tabs.current_tab_unhide_all()
