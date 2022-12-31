"""Comtrade widgets tabber."""
# 1. std
import pathlib
import struct
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QTabWidget, QMainWindow, QMessageBox
# 3. local
from core.mycomtrade import MyComtrade, SanityChkError
from sig.mainwidget import ComtradeWidget


class ComtradeTabWidget(QTabWidget):
    """Oscillogramm tabs container."""

    def __init__(self, parent: 'MainWindow'):  # noqa: F821
        """Init ComtradeTabWidget object."""
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.slot_tab_close)
        # self.tabBar().setSelectionBehaviorOnRemove(QTabBar.SelectPreviousTab)

    def add_chart_tab(self, path: pathlib.Path):
        """Add new oscillogramm tab.

        :note: If addTab() after show(), set .updatesEnabled = False B4 changes and = True after changes
         (to prevent flicker)
        """
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        self.setUpdatesEnabled(False)
        try:
            rec = MyComtrade(path)
        except struct.error as err:
            QMessageBox.critical(self, "Loading error", str(err))
        except SanityChkError as err:
            QMessageBox.critical(self, "Sanity check error", str(err))
        else:
            index = self.addTab(ComtradeWidget(rec, self), path.name)  # table width == 940 (CLI) | 100 (Open)
            self.setCurrentIndex(index)
            self.setUpdatesEnabled(True)  # table width == right
        finally:
            QGuiApplication.restoreOverrideCursor()

    def slot_tab_close(self, index):
        """Close the tab (oscillogramm)."""
        max_tabs = int(MAIN_TAB)
        if index >= max_tabs and self.count() >= (max_tabs + 1):  # main tab unclosable
            self.widget(index).close()
            self.removeTab(index)


MAIN_TAB = False  # FIXME: True => signal table too thin
