import sys
import gc

from PyQt5.QtWidgets import QApplication

from .tem_circlefind import TEMCircleFind

def run():
    app = QApplication(sys.argv)
    win = TEMCircleFind()
    try:
        win.loadImage(sys.argv[1])
    except (IndexError, FileNotFoundError):
        pass
    result = app.exec_()
    win.deleteLater()
    del win
    gc.collect()
    app.deleteLater()
    del app
    gc.collect()
    sys.exit(result)
