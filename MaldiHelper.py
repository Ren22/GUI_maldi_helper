import sys, os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import matplotlib.image as mpimg
from PIL import Image, ImageFile
from copy import deepcopy
import random
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.filePath = ''
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Ablation marks region processing')
        self.setGeometry(100, 100, 750, 750)
        # Buttons
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
        self.ext = ''

    def openFileDialog(self):
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.filePath, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                           "All Files (*);;Numpy files (*.npy);;"
                                                           "JPEG files(*.jpeg, *.jpg);;"
                                                           "PNG files(*.png)",
                                                           options=options)
            self.ext = os.path.splitext(self.filePath)[-1]
            self.canvasInitializer()
        except Exception as e:
            print('File cannot be imported')
            print(e.message, e.args)

    def canvasInitializer(self):
        if self.ext == '.npy':
            arrX, arrY = np.load(self.filePath)
            if len(arrX) >= 100000 or len(arrY) >= 100000:
                QMessageBox.about(self, "Warning", "Your input data is very big, therefore the number "
                                                   "of shown points was decreased. Your data will be still"
                                                   "consistent after you save it.")
            if isinstance(self.canvas, PlotCanvas):
                self.canvas.drop_n_setvals(arrX, arrY)
                self.canvas.refresh_plot(arrX, arrY)
            elif isinstance(self.canvas, PlotCanvasImg):
                self.clearWidgetLayout(self.layout())
                self.canvas = PlotCanvas(arrX, arrY)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout().addWidget(self.toolbar)
                self.layout().addWidget(self.canvas)
            elif not self.canvas:
                self.canvas = PlotCanvas(arrX, arrY)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout().addWidget(self.toolbar)
                self.layout().addWidget(self.canvas)

        elif self.ext == '.jpg' or \
                self.ext == '.jpeg' or \
                self.ext == '.png' or \
                self.ext == '.tif' or \
                self.ext == '.tiff' or \
                self.ext == '':
            img = Image.open(self.filePath).convert('RGBA')
            if isinstance(self.canvas, PlotCanvas):
                self.clearWidgetLayout(self.layout())
                self.canvas = PlotCanvasImg(img)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout().addWidget(self.toolbar)
                self.layout().addWidget(self.canvas)
            elif isinstance(self.canvas, PlotCanvasImg):
                self.canvas.stackImgArr = []
                self.canvas.refresh_Img_plot(img)
            elif not self.canvas:
                self.canvas = PlotCanvasImg(img)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout().addWidget(self.toolbar)
                self.layout().addWidget(self.canvas)
        else: # Check if this works!
            QMessageBox.about(self, "Error", "File extension is not supported!")

    def clearWidgetLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

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
        self.stackX = []
        self.stackY = []
        self.limX = ()
        self.limY = ()
        self.set_init_coords()
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        FigureCanvas.__init__(self, self.fig)
        # self.setParent(parent)
        self.plot()

    def on_xlims_change(self, axes):
        self.limX = axes.get_xlim()

    def on_ylims_change(self, axes):
        self.limY = axes.get_ylim()

    def drop_n_setvals(self, arrX, arrY):
        self.currX, self.currY, self.stackX, self.stackY = arrX, arrY, [], []  # curr = current

    def set_init_coords(self):
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None

    def profScatter(self, x_arr, y_arr):
        if len(x_arr) >= 100000 or len(y_arr) >= 100000:
            reducedIndexes = random.sample(range(len(x_arr)), 35000)
            self.ax.scatter(x_arr[reducedIndexes], y_arr[reducedIndexes], 5)
        else:
            self.ax.scatter(x_arr, y_arr, 5)

    def plot(self):
        self.profScatter(self.currX, self.currY)
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
                                               button=[1, 3],
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

    def refresh_plot(self, x_arr, y_arr):
        self.ax.cla()
        self.profScatter(x_arr, y_arr)
        self.ax.set_title('Loaded data')
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        self.draw()

    def refresh_plot_deletion(self, x_arr, y_arr):
        self.ax.cla()
        self.ax.set_xlim(self.limX)
        self.ax.set_ylim(self.limY)
        self.profScatter(x_arr, y_arr)
        self.ax.set_title('Loaded data')
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        self.draw()

    def on_activated(self, action, x1, y1, x2, y2):
        if x1 and y1 and x2 and y2:
            indexes = self.selected_data_indicies(self.currX, self.currY, x1, y1, x2, y2)
            if indexes and action == 'Crop':
                self.stackX.append(self.currX)
                self.stackY.append(self.currY)
                self.currX = self.currX[indexes]
                self.currY = self.currY[indexes]
                self.refresh_plot(self.currX, self.currY)
                self.set_init_coords()
            elif indexes and action == 'Delete':
                self.stackX.append(self.currX)
                self.stackY.append(self.currY)
                self.currX = np.delete(self.currX, indexes)
                self.currY = np.delete(self.currY, indexes)
                self.refresh_plot_deletion(self.currX, self.currY)
                self.set_init_coords()
        if action == 'Revert':
            if self.stackX and self.stackY:
                self.currX = self.stackX[-1]
                self.currY = self.stackY[-1]
                self.stackX = self.stackX[:-1]
                self.stackY = self.stackY[:-1]
                self.refresh_plot(self.currX, self.currY)

class PlotCanvasImg(FigureCanvas):
    def __init__(self, img, width=5, height=4, dpi=100):
        self.img = img
        self.imgArr = mpimg.pil_to_array(img)
        self.imgArr.setflags(write=True)
        self.stackImgArr = []
        self.limX = ()
        self.limY = ()
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        FigureCanvas.__init__(self, self.fig)
        self.set_init_coords()
        self.plot()

    def refresh_Img_plot(self, img):
        self.ax.cla()
        self.img = img
        self.imgArr = mpimg.pil_to_array(img)
        self.imgArr.setflags(write=True)
        self.ax.imshow(img)
        self.ax.set_title('Loaded data')
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        self.fig.canvas.draw_idle()

    def on_xlims_change(self, axes):
        self.limX = axes.get_xlim()

    def on_ylims_change(self, axes):
        self.limY = axes.get_ylim()

    def set_init_coords(self):
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None

    def plot(self):
        self.ax.imshow(self.imgArr)
        self.ax.set_title('Image processing')

        def toggle_selector(event):
            if event.key in ['Q', 'q'] and toggle_selector.RS.active:
                print(' RectangleSelector deactivated.')
                toggle_selector.RS.set_active(False)
            if event.key in ['A', 'a'] and not toggle_selector.RS.active:
                print(' RectangleSelector activated.')
                toggle_selector.RS.set_active(True)

        toggle_selector.RS = RectangleSelector(self.ax, self.rectangle_callback,
                                               drawtype='box', useblit=True,
                                               button=[1, 3],
                                               minspanx=5, minspany=5,
                                               spancoords='pixels',
                                               interactive=True)
        plt.connect('key_press_event', toggle_selector)

    def rectangle_callback(self, eclick, erelease):
        if [self.x1, self.y1, self.x2, self.y2] is not [eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata]:
            self.x1, self.y1 = eclick.xdata, eclick.ydata
            self.x2, self.y2 = erelease.xdata, erelease.ydata
            print('({:3.2f}, {:3.2f}) --> ({:3.2f}, {:3.2f})'.format(self.x1, self.y1, self.x2, self.y2))

    def on_activated(self, action, x1, y1, x2, y2):
        if x1 and y1 and x2 and y2:
            if action == 'Crop':
                self.stackImgArr.append(self.imgArr)
                self.img = self.img.crop((x1, y1, x2, y2))
                self.imgArr = mpimg.pil_to_array(self.img)
                self.imgArr.setflags(write=True)
                self.ax.cla()
                self.ax.imshow(self.imgArr)
                self.draw()
                self.set_init_coords()
            elif action == 'Delete':
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                ImgArrCopy = deepcopy(self.imgArr)
                self.stackImgArr.append(ImgArrCopy)
                self.imgArr[y1:y2, x1:x2] = 255
                self.img = Image.fromarray(self.imgArr)
                self.ax.imshow(self.imgArr)
                self.draw()
                self.set_init_coords()
        if action == 'Revert': #TODO: revert should store only changes to image array
            if self.stackImgArr:
                self.imgArr = self.stackImgArr[-1]
                self.img = Image.fromarray(self.imgArr)
                self.stackImgArr = self.stackImgArr[:-1]
                self.ax.imshow(self.imgArr)
                self.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())
