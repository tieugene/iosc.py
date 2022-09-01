"""Widgetable table header
Powered by [internets](https://stackoverflow.com/questions/11596267/qtablewidget-personal-widget-as-header)
and [Qt blog](https://www.qt.io/blog/2012/09/28/qt-support-weekly-27-widgets-on-a-header)
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QHeaderView, QTableWidget, QWidget


class WHeaderView(QHeaderView):
    """Widgetable [table] QHeaderView
    TODO: stretch widgets
    """
    __item: dict[int, QWidget]  # TODO: replace with list

    def __init__(self, parent: QTableWidget = None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.__item = dict()
        self.sectionResized.connect(self.__slot_section_resized)
        self.sectionMoved.connect(self.__slot_section_moved)

    def __update_item(self, i: int):
        self.__item[i].setGeometry(self.sectionViewportPosition(i), 0, self.sectionSize(i) - 5, self.height())

    def __slot_section_resized(self, i: int):
        for j in range(self.visualIndex(i), self.count()):
            self.__update_item(self.logicalIndex(j))

    def __slot_section_moved(self, _: int, old_vindex: int, new_vindex: int):
        for i in range(min(old_vindex, new_vindex), self.count()):
            self.__update_item(self.logicalIndex(i))

    def showEvent(self, e: QShowEvent):
        for i in range(self.count()):
            if i not in self.__item:
                self.__item[i] = QWidget(self)
            else:
                self.__item[i].setParent(self)  # TODO: skip if already
            self.__update_item(i)
            self.__item[i].show()
        super().showEvent(e)

    def set_widget(self, i: int, w: QWidget):
        w.setParent(self)
        self.__item[i] = w

    def fix_widget_positions(self):
        """Fix widget positions after scroll"""
        for i in range(self.count()):
            self.__update_item(i)


class WHTableWidget(QTableWidget):
    """QTableWidget with Widgetable Horizontal header"""
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setHorizontalHeader(WHeaderView(Qt.Orientation.Horizontal, self))

    def scrollContentsBy(self, dx: int, dy: int):
        super().scrollContentsBy(dx, dy)
        if dx:
            self.horizontalHeader().fix_widget_positions()
