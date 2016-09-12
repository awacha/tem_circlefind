import os

import numpy as np
import pkg_resources
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.uic import loadUiType
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from scipy.misc import imread

TEMCircleFind_UI, baseclass = loadUiType(pkg_resources.resource_filename('tem_circlefind', "tem_circlefind.ui"))

assert baseclass is QtWidgets.QWidget


class TEMCircleFind(QtWidgets.QWidget, TEMCircleFind_UI):
    def __init__(self):
        super().__init__(parent=None, flags=QtCore.Qt.Window)
        super(TEMCircleFind_UI, self).__init__()
        self.setupUi(self)
        self.fig = Figure()
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.axes = self.fig.add_subplot(1, 1, 1)
        self.fig.tight_layout()
        self.canvas.draw()
        self.canvas.mpl_connect('button_press_event', self.canvasButtonPress)
        assert isinstance(self.figLayout, QtWidgets.QVBoxLayout)
        self.figLayout.addWidget(self.canvas, stretch=1)
        self.figLayout.addWidget(self.toolbar)
        assert isinstance(self.browseInputButton, QtWidgets.QPushButton)
        self.browseInputButton.clicked.connect(self.browseInputFile)
        assert isinstance(self.inputLineEdit, QtWidgets.QLineEdit)
        self.inputLineEdit.returnPressed.connect(self.loadImage)
        assert isinstance(self.circlediameterRadioButton, QtWidgets.QRadioButton)
        assert isinstance(self.threepointsRadioButton, QtWidgets.QRadioButton)
        assert isinstance(self.calibrationRadioButton, QtWidgets.QRadioButton)
        self.circlediameterRadioButton.toggled.connect(self.radioButtonToggled)
        self.threepointsRadioButton.toggled.connect(self.radioButtonToggled)
        self.calibrationRadioButton.toggled.connect(self.radioButtonToggled)
        assert isinstance(self.forgetPushButton, QtWidgets.QPushButton)
        self.forgetPushButton.clicked.connect(self.forgetPendingClicks)
        assert isinstance(self.clearresultsPushButton, QtWidgets.QPushButton)
        self.clearresultsPushButton.clicked.connect(self.clearResults)
        assert isinstance(self.saveresultsPushButton, QtWidgets.QPushButton)
        self.saveresultsPushButton.clicked.connect(self.saveResults)
        assert isinstance(self.clicktargetoperationBox, QtWidgets.QGroupBox)
        self.clicktargetoperationBox.toggled.connect(self.collectclicksToggled)
        self.removeselectedPushButton.clicked.connect(self.removeSelected)
        self.filename = None
        self._point_markers = []
        self._active_toolbuttons = []
        self.clicktargetoperationBox.setChecked(False)
        self.show()

    def removeSelected(self):
        assert isinstance(self.resultsTreeWidget, QtWidgets.QTreeWidget)
        model = self.resultsTreeWidget.model()
        assert isinstance(model, QtCore.QAbstractItemModel)
        lis = self.resultsTreeWidget.selectedIndexes()
        while lis:
            it = lis[0]
            assert isinstance(it, QtCore.QModelIndex)
            model.removeRow(it.row())
            lis = self.resultsTreeWidget.selectedIndexes()

    def collectclicksToggled(self, newstate: bool):
        if newstate:
            # disable zooming, etc.
            self._active_toolbuttons = [
                c for c in self.toolbar.children()
                if (
                    isinstance(c, QtWidgets.QToolButton) and
                    c.isCheckable() and c.isChecked()
                )]
            for c in self._active_toolbuttons:
                c.click()
            self.toolbar.setEnabled(False)
        else:
            for c in self._active_toolbuttons:
                c.click()
            self._active_toolbuttons = []
            self.toolbar.setEnabled(True)

    def radioButtonToggled(self, newstate: bool):
        if not newstate:
            # we are only interested in active states
            return
        self.forgetPendingClicks()

    def forgetPendingClicks(self):
        while self.clicksTreeView.topLevelItemCount():
            self.clicksTreeView.takeTopLevelItem(0)
        for pm in self._point_markers:
            pm.remove()
        self._point_markers = []
        self.canvas.draw()

    def closeEvent(self, e: QtGui.QCloseEvent):
        e.accept()
        QtCore.QCoreApplication.instance().quit()

    def loadImage(self):
        assert isinstance(self.inputLineEdit, QtWidgets.QLineEdit)
        self.filename = self.inputLineEdit.text()
        try:
            self.data = imread(self.filename, flatten=True)
            self.replotImage()
        except:
            mb = QtWidgets.QMessageBox(self)
            mb.setIcon(QtWidgets.QMessageBox.Critical)
            mb.setText('Error while loading image file.')
            mb.setWindowTitle('Error')
            mb.setWindowModality(True)
            mb.show()

    def browseInputFile(self):
        filename, filter_used = QtWidgets.QFileDialog.getOpenFileName(self, 'Open image file')
        if not filename:
            return
        else:
            self.filename = filename
        assert isinstance(self.inputLineEdit, QtWidgets.QLineEdit)
        self.inputLineEdit.setText(self.filename)
        self.loadImage()

    def replotImage(self):
        self.axes.clear()
        self.axes.imshow(self.data, cmap='gray', interpolation='nearest')
        self.canvas.draw()

    def canvasButtonPress(self, event):
        if not self.clicktargetoperationBox.isChecked():
            return
        if event.inaxes != self.axes:
            return
        if event.button != 1:
            return
        x = event.xdata * float(self.pixelsizeSpinBox.value())
        y = event.ydata * float(self.pixelsizeSpinBox.value())
        assert isinstance(self.clicksTreeView, QtWidgets.QTreeWidget)
        twi = QtWidgets.QTreeWidgetItem(self.clicksTreeView)
        twi.setText(0, str(x))
        twi.setText(1, str(y))
        self.clicksTreeView.addTopLevelItem(twi)
        self.clicksTreeView.setCurrentItem(twi)
        self._point_markers.extend(self.axes.plot(event.xdata, event.ydata, 'ro', scalex=False, scaley=False))
        self.canvas.draw()
        self.processWaitingClicks()

    def processWaitingClicks(self):
        assert isinstance(self.clicksTreeView, QtWidgets.QTreeWidget)
        points = [(float(twi.text(0)), float(twi.text(1))) for twi in
                  [self.clicksTreeView.topLevelItem(i) for i in range(self.clicksTreeView.topLevelItemCount())]]
        radius = xcen = ycen = None
        if self.calibrationRadioButton.isChecked() and (len(points) >= 2):
            pixsize = float(self.calibrationSpinBox.value()) / (
                                                                   (points[0][0] - points[1][0]) ** 2 + (
                                                                       points[0][1] - points[1][1]) ** 2) ** 0.5
            assert isinstance(self.pixelsizeSpinBox, QtWidgets.QDoubleSpinBox)
            self.pixelsizeSpinBox.setValue(pixsize)
            self.clicksTreeView.takeTopLevelItem(0)
            self.clicksTreeView.takeTopLevelItem(0)
            self._point_markers.pop(0).remove()
            self._point_markers.pop(0).remove()
            self.canvas.draw()
        elif self.circlediameterRadioButton.isChecked() and (len(points) >= 2):
            xcen = 0.5 * (points[0][0] + points[1][0])
            ycen = 0.5 * (points[0][1] + points[1][1])
            radius = 0.5 * ((points[0][0] - points[1][0]) ** 2 + (points[0][1] - points[1][1]) ** 2) ** 0.5
            self.clicksTreeView.takeTopLevelItem(0)
            self.clicksTreeView.takeTopLevelItem(0)
            self._point_markers.pop(0).remove()
            self._point_markers.pop(0).remove()
            self._point_markers = self._point_markers[2:]
            self.canvas.draw()
        elif self.threepointsRadioButton.isChecked() and (len(points) >= 3):
            # the center of the circumscribed circle.
            ax = points[0][0]
            ay = points[0][1]
            bx = points[1][0]
            by = points[1][1]
            cx = points[2][0]
            cy = points[2][1]
            d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
            xcen = ((ay ** 2 + ax ** 2) * (by - cy) + (by ** 2 + bx ** 2) * (cy - ay) + (cy ** 2 + cx ** 2) * (
                ay - by)) / d
            ycen = ((ay ** 2 + ax ** 2) * (cx - bx) + (by ** 2 + bx ** 2) * (ax - cx) + (cy ** 2 + cx ** 2) * (
                bx - ax)) / d
            a = ((by - cy) ** 2 + (bx - cx) ** 2) ** 0.5
            b = ((cy - ay) ** 2 + (cx - ax) ** 2) ** 0.5
            c = ((by - ay) ** 2 + (bx - ax) ** 2) ** 0.5
            s = (a + b + c) * 0.5
            radius = 0.25 * a * b * c / (s * (s - a) * (s - b) * (s - c)) ** 0.5
            self.clicksTreeView.takeTopLevelItem(0)
            self.clicksTreeView.takeTopLevelItem(0)
            self.clicksTreeView.takeTopLevelItem(0)
            self._point_markers.pop(0).remove()
            self._point_markers.pop(0).remove()
            self._point_markers.pop(0).remove()
            self.canvas.draw()
        else:
            # do nothing
            pass
        if radius is not None:
            assert (xcen is not None) and (ycen is not None)
            twi = QtWidgets.QTreeWidgetItem(self.resultsTreeWidget)
            twi.setText(0, str(xcen))
            twi.setText(1, str(ycen))
            twi.setText(2, str(2 * radius))
            self.resultsTreeWidget.addTopLevelItem(twi)
            self.resultsTreeWidget.setCurrentItem(twi)
            self.drawcircle(xcen, ycen, radius)

    def drawcircle(self, xcen, ycen, radius):
        x = (xcen + np.cos(np.linspace(0, 2 * np.pi, 361)) * radius) / float(self.pixelsizeSpinBox.value())
        y = (ycen + np.sin(np.linspace(0, 2 * np.pi, 361)) * radius) / float(self.pixelsizeSpinBox.value())
        self.axes.plot(x, y, 'm-', scalex=False, scaley=False)
        self.canvas.draw()

    def clearResults(self):
        while self.resultsTreeWidget.topLevelItemCount():
            self.resultsTreeWidget.takeTopLevelItem(0)

    def saveResults(self):
        if self.filename is None:
            dirname = os.path.join(os.getcwd(), 'untitled.txt')
        else:
            dirname = os.path.splitext(self.filename)[0] + '.txt'
        filename, filter = QtWidgets.QFileDialog.getSaveFileName(self, "Save results to file...", dirname)
        if not filename:
            return
        with open(filename, 'wt', encoding='utf-8') as f:
            for i in range(self.resultsTreeWidget.topLevelItemCount()):
                twi = self.resultsTreeWidget.topLevelItem(i)
                assert isinstance(twi, QtWidgets.QTreeWidgetItem)
                f.write(twi.text(0) + '\t' + twi.text(1) + '\t' + twi.text(2) + '\n')
        mb = QtWidgets.QMessageBox(self)
        mb.setIcon(QtWidgets.QMessageBox.Information)
        mb.setText('Results have been saved to {}'.format(filename))
        mb.setWindowTitle('File saved.')
        mb.setWindowModality(True)
        mb.show()
