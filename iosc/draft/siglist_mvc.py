"""Signal list view.
MVC version
:todo: try QAbstractTableModelItem
:todo: try wrap QVariant/QObject/QSomething(signal)
"""
# 2. 3rd
from PySide2.QtCore import Qt, QModelIndex, QAbstractTableModel
from PySide2.QtWidgets import QStyledItemDelegate, QTableView
# 3. local
import mycomtrade
from sigwidget import SignalCtrlView, SignalChartView


class SignalListModel(QAbstractTableModel):  # FIXME: QAbstractTableModel (examples/widgets/itemviews/addressbook/)
    slist: mycomtrade.SignalList

    def __init__(self, slist: mycomtrade.SignalList, parent=None):
        super().__init__(parent)
        self.slist = slist

    def rowCount(self, index=QModelIndex()) -> int:
        """ Returns the number of rows the model holds. """
        return self.slist.count

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return 2

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section == 0:
                return "Ctrl"
            elif section == 1:
                return "Chart"
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if not 0 <= index.row() < self.slist.count:
            return None
        if role == Qt.DisplayRole and index.column() in {0, 1}:
            return self.slist[index.row()]
        return None


class SignalDelegate(QStyledItemDelegate):  # FIXME: class
    def __init__(self, parent=None):
        super().__init__(parent)

    def setEditorData(self, editor: SignalCtrlView, index: QModelIndex):
        value = index.model().data(index, Qt.DisplayRole)
        editor.set_data(value)

    def setModelData(self, editor, model, index):
        pass


class SignalCtrlDelegate(SignalDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        return SignalCtrlView(parent)


class SignalChartDelegate(SignalDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        return SignalChartView(parent)


class SignalListView(QTableView):
    model: SignalListModel

    def __init__(self, slist: mycomtrade.SignalList, parent=None):
        super().__init__(parent)
        self.model = SignalListModel(slist)
        self.setModel(self.model)
        self.setItemDelegateForColumn(0, SignalCtrlDelegate(self))
        self.setItemDelegateForColumn(1, SignalChartDelegate(self))
        for i in range(slist.count):
            self.openPersistentEditor(self.model.index(i, 0))
            self.openPersistentEditor(self.model.index(i, 1))
