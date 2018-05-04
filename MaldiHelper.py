import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
from matplotlib.patches import Rectangle
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.filePath = ''
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Ablation marks region processing')
        self.setGeometry(10, 10, 750, 750)

        #Buttons
        selectb = QPushButton('Crop', self)
        selectb.setShortcut('C')
        selectb.clicked.connect(lambda: m.canvas.on_activated('Crop', m.canvas.x1, m.canvas.y1,
                                                              m.canvas.x2, m.canvas.y2))

        deleteb = QPushButton('Delete', self)
        deleteb.setShortcut('D')
        deleteb.clicked.connect(lambda: m.canvas.on_activated('Delete', m.canvas.x1, m.canvas.y1,
                                                              m.canvas.x2, m.canvas.y2))

        revertb = QPushButton('Revert', self)
        revertb.setShortcut('R')
        revertb.clicked.connect(lambda: m.canvas.on_activated('Revert', m.canvas.x1, m.canvas.y1,
                                                              m.canvas.x2, m.canvas.y2))

        widget = QWidget(self)
        self.setCentralWidget(widget)
        vlay = QVBoxLayout()
        hlay = QHBoxLayout(widget)
        hlay.addLayout(vlay)

        # Nested layout
        vlay2 = QVBoxLayout()
        vlay2.addStretch()
        vlay2.addWidget(selectb, 0, QtCore.Qt.AlignRight)
        vlay2.addWidget(deleteb, 0, QtCore.Qt.AlignRight)
        vlay2.addWidget(revertb, 0, QtCore.Qt.AlignRight)
        m = WidgetPlot()
        hlay.addWidget(m)
        hlay.addLayout(vlay2)

        mainMenu = self.menuBar()
        mainMenu.setNativeMenuBar(False)
        fileMenu = mainMenu.addMenu('File')
        helpMenu = mainMenu.addMenu('Help')

        importFile = QAction('Import', self)
        importFile.setShortcut('Ctrl+A')
        importFile.setStatusTip('Import npy array or image')
        importFile.triggered.connect(m.openFileDialog)
        fileMenu.addAction(importFile)

        importFile = QAction('Export', self)
        importFile.setShortcut('Ctrl+S')
        importFile.setStatusTip('Export npy array or image')
        importFile.triggered.connect(m.saveFileDialog)
        fileMenu.addAction(importFile)

        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

class WidgetPlot(QWidget):
    def __init__(self):
        super().__init__()
        self.canvas = []
        self.setLayout(QVBoxLayout())

    def openFileDialog(self):
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.filePath, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                           "All Files (*);;Numpy files (*.npy);;JPEG files(*.jpeg, *.jpg)",
                                                           options=options)

            self.arrX, self.arrY = np.load(self.filePath)
        except:
            print('File cannot be imported')
        if not self.canvas:
            self.canvas = PlotCanvas(self.arrX, self.arrY)
            self.toolbar = NavigationToolbar(self.canvas, self)
            self.layout().addWidget(self.toolbar)
            self.layout().addWidget(self.canvas)

        else:
            PlotCanvas.drop_vals(self.canvas, self.arrX, self.arrY)
            PlotCanvas.refresh_n_plot(self.canvas, self.arrX, self.arrY)

    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filePath, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "All Files (*);;Numpy files (*.npy);;JPEG files(*.jpeg, *.jpg)",
                                                  options=options)
        if filePath:
            try:
                exp = np.array([self.canvas.currX, self.canvas.currY])
                np.save('{:s}'.format(filePath), exp)
            except:
                print('Values were not exported!')

class PlotCanvas(FigureCanvas):
    def __init__(self, arrX, arrY, width=5, height=4, dpi=100):
        self.currX, self.currY = arrX, arrY  # curr = current
        self.stackX = []; self.stackY = []
        self.set_init_coords()
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        # self.setParent(parent)
        self.plot()

    def drop_vals(self, arrX, arrY):
        self.currX, self.currY, self.stackX, self.stackY = arrX, arrY, [], []  # curr = current

    def set_init_coords(self):
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None

    def plot(self):
        self.ax.scatter(self.currX, self.currY, 5)
        self.ax.axis('equal')
        self.ax.set_title('Loaded data')

        def toggle_selector(event):
            if event.key in ['Q', 'q'] and toggle_selector.RS.active:
                print(' RectangleSelector deactivated.')
                toggle_selector.RS.set_active(False)
            if event.key in ['A', 'a'] and not toggle_selector.RS.active:
                print(' RectangleSelector activated.')
                toggle_selector.RS.set_active(True)

        toggle_selector.RS = RectangleSelector(self.ax, self.rectangle_callback,
                                               drawtype='box', useblit=True,
                                               button=[1, 3],  # don't use middle button
                                               minspanx=5, minspany=5,
                                               spancoords='pixels',
                                               interactive=True)

        plt.connect('key_press_event', toggle_selector)

    def rectangle_callback(self, eclick, erelease):
        self.x1, self.y1 = eclick.xdata, eclick.ydata
        self.x2, self.y2 = erelease.xdata, erelease.ydata
        print('({:3.2f}, {:3.2f}) --> ({:3.2f}, {:3.2f})'.format(self.x1, self.y1, self.x2, self.y2))
        print('The button you used were: {:d} {:d}'.format(eclick.button, erelease.button))

    @staticmethod
    def selected_data_indicies(currX, currY, x1, y1, x2, y2):
        indX = np.intersect1d(np.where(currX >= x1)[0], np.where(currX <= x2)[0])
        ind = []
        for i in indX:
            if currY[i] >= y1 and currY[i] <= y2:
                ind.append(i)

        return ind

    def refresh_n_plot(self, x_arr, y_arr):
        self.ax.cla()
        self.ax.scatter(x_arr, y_arr, 5)
        self.ax.axis('equal')
        self.ax.set_title('Loaded data')
        self.draw()

    def on_activated(self, action, x1, y1, x2, y2):
        if x1 and y1 and x2 and y2:
            indexes = self.selected_data_indicies(self.currX, self.currY, x1, y1, x2, y2)
            if indexes and action == 'Crop':
                self.stackX.append(self.currX)
                self.stackY.append(self.currY)
                self.currX = self.currX[indexes]
                self.currY = self.currY[indexes]
                self.refresh_n_plot(self.currX, self.currY)
                self.set_init_coords()
            elif indexes and action == 'Delete':
                self.stackX.append(self.currX)
                self.stackY.append(self.currY)
                self.currX = np.delete(self.currX, indexes)
                self.currY = np.delete(self.currY, indexes)
                self.refresh_n_plot(self.currX, self.currY)
                self.set_init_coords()
        if action == 'Revert':
            if self.stackX and self.stackY:
                self.currX = self.stackX[-1]
                self.currY = self.stackY[-1]
                self.stackX = self.stackX[:-1]
                self.stackY = self.stackY[:-1]
                self.refresh_n_plot(self.currX, self.currY)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())