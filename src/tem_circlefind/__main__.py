import sys

from PyQt4 import QtGui

QtWidgets = QtGui

from .tem_circlefind import TEMCircleFind


def run():
    app = QtWidgets.QApplication(sys.argv)
    win = TEMCircleFind()
    sys.exit(app.exec_())
