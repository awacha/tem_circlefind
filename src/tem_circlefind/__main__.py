import sys

from PyQt5 import QtWidgets

from .tem_circlefind import TEMCircleFind


def run():
    app = QtWidgets.QApplication(sys.argv)
    win = TEMCircleFind()
    sys.exit(app.exec_())
