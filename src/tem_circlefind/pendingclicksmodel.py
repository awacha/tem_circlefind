from PyQt5 import QtCore

class PendingClicksModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data=[]


    def rowCount(self, parent: QtCore.QModelIndex = ...):
        return len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = ...):
        return 2

    def flags(self, index: QtCore.QModelIndex):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemNeverHasChildren | QtCore.Qt.ItemIsEnabled

    def parent(self, child: QtCore.QModelIndex):
        return QtCore.QModelIndex()

    def data(self, index: QtCore.QModelIndex, role: int = ...):
        if role == QtCore.Qt.DisplayRole:
            return '{:.3f}'.format(self._data[index.row()][index.column()])
        else:
            return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ['X coordinate','Y coordinate'][section]
        else:
            return None

    def index(self, row: int, column: int, parent: QtCore.QModelIndex = ...):
        return self.createIndex(row, column, None)

    def append(self, x:float, y:float):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._data), len(self._data))
        self._data.append((x,y))
        self.endInsertRows()

    def removeRow(self, row: int, parent: QtCore.QModelIndex = ...):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._data[row]
        self.endRemoveRows()

    def clear(self):
        self.beginResetModel()
        self._data=[]
        self.endResetModel()

    def getData(self):
        return self._data[:]

    def pop(self, number=1):
        if len(self._data) <number:
            raise ValueError('Not enough clicks waiting')
        res = self._data[:number]
        self.beginRemoveRows(QtCore.QModelIndex(), 0, 0+number-1)
        self._data = self._data[number:]
        self.endRemoveRows()
        return res