import os

import numpy as np
from matplotlib.figure import Figure
from matplotlib.widgets import MultiCursor
from pkg_resources import get_distribution, resource_filename
from scipy.misc import imread

from PyQt5.uic import loadUiType
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.gridspec import GridSpec
from PyQt5 import QtGui, QtCore, QtWidgets

from .resultsmodel import ResultsModel
from .pendingclicksmodel import PendingClicksModel

# try to load the pre-compiled UI
try:
    from .tem_circlefind_ui import Ui_TEMCircleFind

    raise ImportError
except ImportError:
    Ui_TEMCircleFind, baseclass = loadUiType(resource_filename('tem_circlefind', 'tem_circlefind.ui'))
    assert baseclass == QtWidgets.QWidget

class TEMCircleFind(QtWidgets.QWidget, Ui_TEMCircleFind):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.fig = Figure()
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
#        GX=1
#        GY=1
#        gs=GridSpec(GY,GX)
        self.axes = self.fig.add_subplot(1,1,1)
        self.axes.set_frame_on(False)
        self.axes.xaxis.set_visible(False)
        self.axes.yaxis.set_visible(False)
#        self.xsliceaxes = self.fig.add_subplot(gs[GY-1,1:], sharex=self.axes)
#        self.xsliceaxes.yaxis.set_visible(False)
#        self.ysliceaxes = self.fig.add_subplot(gs[:GY-1,0], sharey=self.axes)
#        self.ysliceaxes.xaxis.set_visible(False)
#        self.axes_horizsection = self.fig.add_subplot()
        self.fig.tight_layout()
        self.canvas.draw()
        self.canvas.mpl_connect('button_press_event', self.canvasButtonPress)
        assert isinstance(self.figLayout, QtWidgets.QVBoxLayout)
        self.figLayout.addWidget(self.canvas, stretch=1)
        self.figLayout.addWidget(self.toolbar)
        self.fighistogram = Figure()
        self.canvashistogram = FigureCanvasQTAgg(self.fighistogram)
        self.toolbarhistogram = NavigationToolbar2QT(self.canvashistogram, self)
        self.axeshistogram = self.fighistogram.add_subplot(1,1,1)
        self.axeshistogram.set_xlabel('Diameter (nm)')
        self.fighistogram.tight_layout()
        self.histogramVerticalLayout.addWidget(self.canvashistogram)
        self.histogramVerticalLayout.addWidget(self.toolbarhistogram)
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
        self.replotPushButton.clicked.connect(self.replotImage)
        self.loadResultsPushButton.clicked.connect(self.loadResults)
        self.filename = None
        self._point_markers = []
        self._active_toolbuttons = []
        self.resultsModel = ResultsModel()
        self.resultsTreeView.setModel(self.resultsModel)
        self.pendingClicksModel = PendingClicksModel()
        self.clicksTreeView.setModel(self.pendingClicksModel)
        self.clicktargetoperationBox.setChecked(False)
        self.nHistogramBinsSpinBox.valueChanged.connect(self.drawHistogram)
        self.setWindowTitle('TEM Circle Finder v{}'.format(get_distribution('tem_circlefind').version))
        self.show()

    def drawHistogram(self):
        self.axeshistogram.clear()
        self.axeshistogram.hist([d[2] for d in self.resultsModel.getData()], self.nHistogramBinsSpinBox.value())
        self.canvashistogram.draw()


    def removeSelected(self):
        lis = self.resultsTreeView.selectedIndexes()
        while lis:
            it = lis[0]
            self.resultsModel.removeRow(it.row())
            lis = self.resultsTreeView.selectedIndexes()

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
            try:
                self.mpl_cursor.clear(None)
                self.mpl_cursor.visible=False
                self.mpl_cursor.set_active(False)
                del self.mpl_cursor
            except AttributeError:
                pass
            self.mpl_cursor = MultiCursor(self.canvas, axes=[self.axes], horizOn=True, vertOn=True, useblit=True, color='r')
            self.mpl_cursor.clear(None)
        else:
            for c in self._active_toolbuttons:
                c.click()
            self._active_toolbuttons = []
            self.toolbar.setEnabled(True)
            try:
                self.mpl_cursor.visible=False
                self.mpl_cursor.clear(None)
                self.mpl_cursor.set_active(True)
                del self.mpl_cursor
                self.canvas.draw()
            except AttributeError:
                pass

    def radioButtonToggled(self, newstate: bool):
        if not newstate:
            # we are only interested in active states
            return
        self.forgetPendingClicks()

    def forgetPendingClicks(self):
        self.pendingClicksModel.clear()
        for pm in self._point_markers:
            try:
                pm.remove()
            except ValueError:
                continue
        self._point_markers = []
        self.canvas.draw()

    def closeEvent(self, e: QtGui.QCloseEvent):
        e.accept()
        QtCore.QCoreApplication.instance().quit()

    def loadImage(self, filename=None):
        assert isinstance(self.inputLineEdit, QtWidgets.QLineEdit)
        if filename is not None:
            self.inputLineEdit.setText(filename)
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
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open image file')[0]
        if not filename:
            return
        else:
            self.filename = filename
        assert isinstance(self.inputLineEdit, QtWidgets.QLineEdit)
        self.inputLineEdit.setText(self.filename)
        self.loadImage()

    def loadResults(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Load previously saved circle data')[0]
        if not filename:
            return
        else:
            try:
                data = np.loadtxt(filename)
            except:
                QtWidgets.QMessageBox.critical(self, 'Error loading file', 'Malformed file: {}'.format(filename))
                return
        if data.shape[1] !=3:
            QtWidgets.QMessageBox.critical(self, 'Error loading file', 'File {} does not have three columns.'.format(filename))
            return
        for i in range(data.shape[0]):
            self.resultsModel.append(data[i,0], data[i, 1], data[i,2])
        self.replotImage()
        self.drawHistogram()
        self.updateStatistics()

    def replotImage(self):
        self.axes.clear()
        self.axes.imshow(self.data, cmap='gray', interpolation='nearest')
        for x, y, diameter in self.resultsModel.getData():
            self.drawcircle(x, y, diameter*0.5, silent=True)
        self.canvas.draw()

    def canvasButtonPress(self, event):
        if not self.clicktargetoperationBox.isChecked():
            print('Not collecting this click')
            return
        if event.inaxes != self.axes:
            print('Not in this axes')
            return
        if event.button != 1:
            print('Not left button')
            return
        x = event.xdata
        y = event.ydata
        self.pendingClicksModel.append(x,y)
        self._point_markers.extend(self.axes.plot(event.xdata, event.ydata, 'ro', scalex=False, scaley=False))
        self.canvas.draw()
        self.processWaitingClicks()

    def processWaitingClicks(self):
        radius = xcen = ycen = None
        if self.calibrationRadioButton.isChecked():
            try:
                points = self.pendingClicksModel.pop(2)
            except ValueError:
                return
            pixsize = float(self.calibrationSpinBox.value()) / (
                                                                   (points[0][0] - points[1][0]) ** 2 + (
                                                                       points[0][1] - points[1][1]) ** 2) ** 0.5
            assert isinstance(self.pixelsizeSpinBox, QtWidgets.QDoubleSpinBox)
            self.pixelsizeSpinBox.setValue(pixsize)
            for i in range(2):
                try:
                    self._point_markers.pop(0).remove()
                except ValueError:
                    pass
            self._point_markers = self._point_markers[2:]
            self.canvas.draw()
        elif self.circlediameterRadioButton.isChecked():
            try:
                points = self.pendingClicksModel.pop(2)
            except ValueError:
                return
            xcen = 0.5 * (points[0][0] + points[1][0])*self.pixelsizeSpinBox.value()
            ycen = 0.5 * (points[0][1] + points[1][1])*self.pixelsizeSpinBox.value()
            radius = self.pixelsizeSpinBox.value()*0.5 * ((points[0][0] - points[1][0]) ** 2 + (points[0][1] - points[1][1]) ** 2) ** 0.5
            for i in range(2):
                try:
                    self._point_markers.pop(0).remove()
                except ValueError:
                    pass
            self._point_markers = self._point_markers[2:]
            self.canvas.draw()
        elif self.threepointsRadioButton.isChecked():
            # the center of the circumscribed circle.
            try:
                points = self.pendingClicksModel.pop(3)
            except ValueError:
                return
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
            xcen *= self.pixelsizeSpinBox.value()
            ycen *= self.pixelsizeSpinBox.value()
            radius *= self.pixelsizeSpinBox.value()
            for i in range(3):
                try:
                    self._point_markers.pop(0).remove()
                except ValueError:
                    continue
            self._point_markers=self._point_markers[3:]
            self.canvas.draw()
        else:
            # do nothing
            pass
        if radius is not None:
            assert (xcen is not None) and (ycen is not None)
            self.resultsModel.append(xcen, ycen, 2*radius)
            self.drawcircle(xcen, ycen, radius)
            self.drawHistogram()
            self.updateStatistics()

    def updateStatistics(self):
        self.meanDiameterLabel.setText('{:.3f}'.format(self.resultsModel.getMeanDiameter()))
        self.stdDiameterLabel.setText('{:.3f}'.format(self.resultsModel.getStdDiameter()))
        self.minDiameterLabel.setText('{:.3f}'.format(self.resultsModel.getMinDiameter()))
        self.maxDiameterLabel.setText('{:.3f}'.format(self.resultsModel.getMaxDiameter()))
        self.ptpDiameterLabel.setText('{:.3f}'.format(self.resultsModel.getPtPDiameter()))

    def drawcircle(self, xcen, ycen, radius, silent=False):
        x = (xcen + np.cos(np.linspace(0, 2 * np.pi, 361)) * radius) / float(self.pixelsizeSpinBox.value())
        y = (ycen + np.sin(np.linspace(0, 2 * np.pi, 361)) * radius) / float(self.pixelsizeSpinBox.value())
        self.axes.plot(x, y, 'm-', scalex=False, scaley=False)
        if not silent:
            self.canvas.draw()

    def clearResults(self):
        self.resultsModel.clear()

    def saveResults(self):
        if self.filename is None:
            dirname = os.path.join(os.getcwd(), 'untitled.txt')
        else:
            dirname = os.path.splitext(self.filename)[0] + '.txt'
        filename, filter = QtWidgets.QFileDialog.getSaveFileName(self, "Save results to file...", dirname)
        if not filename:
            return
        with open(filename, 'wt', encoding='utf-8') as f:
            f.write('# Mean diameter: {:.3f}\n# STD diameter: {:.3f}\n# Min diameter: {:.3f}\n# Max diameter: {:.3f}\n# P-P diameter: {:.3f}\n'.format(
                self.resultsModel.getMeanDiameter(),
                self.resultsModel.getStdDiameter(),
                self.resultsModel.getMinDiameter(),
                self.resultsModel.getMaxDiameter(),
                self.resultsModel.getPtPDiameter()
            ))
            f.write('# Pixel size: {:.5f}\n'.format(self.pixelsizeSpinBox.value()))
            data = self.resultsModel.getData()
            for x,y,diameter in data:
                f.write('{:12.6f}\t{:12.6f}\t{:12.6f}\n'.format(x,y,diameter))
        QtWidgets.QMessageBox.information(self, 'File saved.', 'Results have been saved to {}'.format(filename))

