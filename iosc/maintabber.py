"""Comtrade widgets tabber"""
import pathlib
import struct

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QTabWidget, QMainWindow, QMessageBox

from core.mycomtrade import MyComtrade
from sig.mainwidget import ComtradeWidget


class ComtradeTabWidget(QTabWidget):
    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.__slot_tab_close)
        # self.tabBar().setSelectionBehaviorOnRemove(QTabBar.SelectPreviousTab)

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
            index = self.addTab(ComtradeWidget(rec, self), path.name)  # table width == 940 (CLI) | 100 (Open)
            self.setCurrentIndex(index)
            self.setUpdatesEnabled(True)  # table width == right
        finally:
            QGuiApplication.restoreOverrideCursor()

    def __slot_tab_close(self, index):
        max_tabs = int(MAIN_TAB)
        if index >= max_tabs and self.count() >= (max_tabs + 1):  # main tab unclosable
            self.removeTab(index)


MAIN_TAB = False  # FIXME: True => signal table too thin
