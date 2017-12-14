import sys

from PyQt5.QtWidgets import QApplication

from .tem_circlefind import TEMCircleFind

def run():
    app = QApplication(sys.argv)
    win = TEMCircleFind()
    try:
        win.loadImage(sys.argv[1])
    except (IndexError, FileNotFoundError):
        pass
    sys.exit(app.exec_())
