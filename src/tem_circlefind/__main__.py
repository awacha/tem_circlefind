import sys

from qtpy.QtWidgets import QApplication

from .tem_circlefind import TEMCircleFind

def run():
    app = QApplication(sys.argv)
    win = TEMCircleFind()
    sys.exit(app.exec_())
