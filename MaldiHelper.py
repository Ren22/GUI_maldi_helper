import sys, os
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, \
    NavigationToolbar2QT
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import matplotlib.image as mpimg
from PIL import Image, ImageFile
from copy import deepcopy
import random
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

class NavigationToolbar(NavigationToolbar2QT):
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Subplots')]

class Window(QMainWindow):
    def __init__(self, path_inp = None, path_out = None, plot_title = None):
        super().__init__()
        self.inpFilePath = path_inp if path_inp else ''
        self.outFilePath = path_out if path_out else ''
        self.plotTitle = plot_title if plot_title else ''
        self.initUI()

    def initUI(self):
        self.setWindowTitle('AM curator')
        self.setGeometry(100, 100, 750, 750)
        # Buttons
        savef = QPushButton('Save', self)
        savef.clicked.connect(lambda: m.saveFile())

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
        vlay2.addWidget(savef, 0, QtCore.Qt.AlignRight)
        vlay2.addWidget(selectb, 0, QtCore.Qt.AlignRight)
        vlay2.addWidget(deleteb, 0, QtCore.Qt.AlignRight)
        vlay2.addWidget(revertb, 0, QtCore.Qt.AlignRight)

        m = WidgetPlot(self.inpFilePath, self.outFilePath, self.plotTitle)
        hlay.addWidget(m)
        hlay.addLayout(vlay2)
        mainMenu = self.menuBar()
        mainMenu.setNativeMenuBar(False)
        fileMenu = mainMenu.addMenu('File')
        importFile = QAction('Open', self)
        importFile.setShortcut('Ctrl+A')
        importFile.setStatusTip('Open npy array or image')
        importFile.triggered.connect(m.openFileDialog)
        fileMenu.addAction(importFile)
        saveFile = QAction('Save', self)
        saveFile.setStatusTip('Save npy array or image')
        saveFile.triggered.connect(m.saveFile)
        fileMenu.addAction(saveFile)
        saveAsFile = QAction('Save as ...', self)
        saveAsFile.setShortcut('Ctrl+S')
        saveAsFile.setStatusTip('Save npy array or image')
        saveAsFile.triggered.connect(m.saveFileDialog)
        fileMenu.addAction(saveAsFile)
        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        helpMenu = mainMenu.addMenu('Help')
        help = QAction('How to use...', self)
        help.setShortcut('Ctrl+H')
        help.triggered.connect(m.help)
        helpMenu.addAction(help)

class WidgetPlot(QWidget):
    def __init__(self, inp_file_path, out_file_path, plot_title):
        super().__init__()
        self.canvas = []
        self.setLayout(QVBoxLayout())
        self.ext = ''
        self.pltTitle = plot_title if plot_title else ''
        self.croppedImgCoords = {
            'topLeft': [],
            'topRight': [],
            'bottomLeft': [],
            'bottomRight': []
        }
        if inp_file_path:
            self.inpFilePath = inp_file_path
            self.ext = os.path.splitext(self.inpFilePath)[-1]
            self.canvasInitializer()
        else:
            self.inpFilePath = ''
        self.outFilePath = out_file_path if out_file_path else ''


    def openFileDialog(self):
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.inpFilePath, _ = QFileDialog.getOpenFileName(self, "Open File", os.path.dirname(self.inpFilePath),
                                                           "All Files (*);;Numpy files (*.npy);;"
                                                           "JPEG(*.jpeg, *.jpg);;"
                                                           "PNG(*.png);;"
                                                           "TIFF(*.tiff, *.tif)",
                                                           options=options)
            self.outFilePath = self.inpFilePath
            self.ext = os.path.splitext(self.inpFilePath)[-1]
            self.canvasInitializer()
        except Exception as e:
            print('File cannot be imported')
            print(e.message, e.args)

    def canvasInitializer(self):
        if self.ext == '.npy':
            arrX, arrY = np.load(self.inpFilePath)
            if isinstance(self.canvas, PlotCanvas):
                self.canvas.drop_n_setvals(arrX, arrY)
                self.canvas.refresh_plot(arrX, arrY)
            elif isinstance(self.canvas, PlotCanvasImg):
                self.clearWidgetLayout(self.layout())
                self.canvas = PlotCanvas(arrX, arrY, self.pltTitle)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout().addWidget(self.toolbar)
                self.layout().addWidget(self.canvas)
            elif not self.canvas:
                self.canvas = PlotCanvas(arrX, arrY, self.pltTitle)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout().addWidget(self.toolbar)
                self.layout().addWidget(self.canvas)

        elif self.ext in {'.jpg', '.jpeg', '.JPG',
                          '.png', '.PNG',
                          '.tif', '.tiff', 'TIFF'} or \
                (self.inpFilePath != '' and self.ext == ''):
            input = Image.open(self.inpFilePath)
            self.ext = input.format
            if input.mode == 'I;16B':
                img = {'src': Image.open(self.inpFilePath), 'mode': 'I;16B',
                       'croppedImgCoords': self.croppedImgCoords, 'pltTitle': self.pltTitle}
            else:
                img = {'src': Image.open(self.inpFilePath).convert('RGBA'), 'mode': 'RGBA',
                       'croppedImgCoords': self.croppedImgCoords, 'pltTitle': self.pltTitle}
            if isinstance(self.canvas, PlotCanvas):
                self.clearWidgetLayout(self.layout())
                self.canvas = PlotCanvasImg(img)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout().addWidget(self.toolbar)
                self.layout().addWidget(self.canvas)
            elif isinstance(self.canvas, PlotCanvasImg):
                self.canvas.stackImgArr = []
                self.canvas.refresh_Img_plot(img)
                self.canvas.initCropCoords(img)
            elif not self.canvas:
                self.canvas = PlotCanvasImg(img)
                self.toolbar = NavigationToolbar(self.canvas, self)
                self.layout().addWidget(self.toolbar)
                self.layout().addWidget(self.canvas)
        else:
            QMessageBox.warning(self, "Warning", "The file was not chosen or the extension is not supported!")

    def clearWidgetLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def saverContent(self, path):
        if isinstance(self.canvas, PlotCanvas):
            exp = np.array([self.canvas.currX, self.canvas.currY])
            np.save(path, exp)
        elif isinstance(self.canvas, PlotCanvasImg):
            img = self.canvas.img['src']
            if self.ext == '' or os.path.splitext(path)[-1] == '':
                img.save(path + '.{}'.format(self.ext.lower()), self.ext)
            elif self.ext == 'JPEG':
                background = Image.new('RGB', img.size, (255,255,255))
                background.paste(img, mask=img.split()[3])
                background.save(path, 'JPEG', quality=80)
            else:
                img.save(path)
            try:
                os.path.splitext("path")[0]
                with open('{}_cropCoords.npy'.format(os.path.splitext(path)[0]), 'wb') as handle:
                    np.save(handle, self.croppedImgCoords)
            except Exception as e:
                QMessageBox.critical(self, "Error", "Coordinates of the new image cannot be saved!")
                print(e.message, e.args)

    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filePath, _ = QFileDialog.getSaveFileName(self, "Save file", os.path.dirname(self.inpFilePath),
                                                  "All Files (*);;Numpy files (*.npy);;"
                                                           "JPEG(*.jpeg, *.jpg);;"
                                                           "PNG(*.png);;"
                                                           "TIFF(*.tiff, *.tif)",
                                                  options=options)
        if filePath:
            try:
                self.saverContent(filePath)
            except Exception as e:
                QMessageBox.critical(self, "Error", "File cannot be saved.")
                print('File cannot be saved!')
                print(e.message, e.args)

    def saveFile(self):
        if self.outFilePath != '':
            try:
                self.saverContent(self.outFilePath)
            except Exception as e:
                QMessageBox.critical(self, "Error", "File cannot be saved.")
                print('File cannot be saved!')
                print(e.message, e.args)
        else:
            self.saveFileDialog()

    def help(self):
        QMessageBox.information(self, "Help",
                                "An interactive program to process ablation mark regions on single cell data pipeline. \n"
                                "To import numpy array or image in different formats such as PNG, TIFF, etc. choose \n"
                                "File -> Open \n"
                                "Select the area of interest by clicking on the uploaded data in GUI (a red rectangle "
                                "will appear which you can pull and adjust its size). \n"
                                "After that you can either crop the area of interest or delete selected area.\n"
                                "The file can be then saved by:\n"
                                "Save as -> allows to specify file name and its format\n"
                                "Save -> will overwrite the existing file \n"
                                "If you have detected bugs, things just go wrong or you have other questions/suggestions,\n"
                                "please contact me :)\n"
                                "renat.nigmetzianov@embl.de ")

class PlotCanvas(FigureCanvas):
    def __init__(self, arrX, arrY, pltTitle, width=5, height=4, dpi=100):
        self.currX, self.currY = arrX, arrY
        self.stackX = []
        self.stackY = []
        self.limX = ()
        self.limY = ()
        self.set_init_coords()
        self.ind = []
        self.pltTitle = pltTitle
        self.fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(self.pltTitle)
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        FigureCanvas.__init__(self, self.fig)
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
        self.ax.set_title(self.pltTitle)
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)

    def plot(self):
        self.profScatter(self.currX, self.currY)
        self.ax.axis('equal')
        self.ax.set_xticks([])
        self.ax.set_yticks([])

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

    def selected_data_indicies(self, currX, currY, x1, y1, x2, y2):
        indX = np.intersect1d(np.where(currX >= x1)[0], np.where(currX <= x2)[0])
        for i in indX:
            if currY[i] >= y1 and currY[i] <= y2:
                self.ind.append(i)
        return self.ind

    def refresh_plot(self, x_arr, y_arr):
        self.ax.cla()
        self.profScatter(x_arr, y_arr)
        self.ax.axis('equal')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.draw()

    def refresh_plot_deletion(self, x_arr, y_arr):
        self.ax.cla()
        self.profScatter(x_arr, y_arr)
        self.ax.set_xlim(self.limX)
        self.ax.set_ylim(self.limY)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
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
                self.ind = []
            elif indexes and action == 'Delete':
                self.stackX.append(self.currX)
                self.stackY.append(self.currY)
                self.currX = np.delete(self.currX, indexes)
                self.currY = np.delete(self.currY, indexes)
                self.refresh_plot_deletion(self.currX, self.currY)
                self.set_init_coords()
                self.ind = []
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
        self.imgArr = mpimg.pil_to_array(self.img['src'])
        self.imgArr.setflags(write=True)
        self.stackImgArr = []
        self.limX = ()
        self.limY = ()
        self.fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(self.img['pltTitle'])
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        FigureCanvas.__init__(self, self.fig)
        self.set_init_coords()
        self.initCropCoords(img)
        self.plot()

    def initCropCoords(self, img):
        self.imgWidth, self.imgHeight = self.img['src'].size
        self.refImgWidth = deepcopy(self.imgWidth)
        self.refImgHeight = deepcopy(self.imgHeight)
        self.x1_ = 0
        self.y1_ = 0
        self.x2_ = self.imgWidth
        self.y2_ = 0
        self.x3_ = 0
        self.y3_ = self.imgHeight
        self.x4_ = self.imgWidth
        self.y4_ = self.imgHeight
        self.dx1, self.dx2, self.dx3, self.dx4 = [], [], [], []
        self.dy1, self.dy2, self.dy3, self.dy4 = [], [], [], []
        self.dx_dy = img['croppedImgCoords']

    def profImshow(self):
        if self.img['mode'] == 'I;16B':
            self.ax.imshow(self.imgArr, cmap='gray')
        else:
            self.ax.imshow(self.imgArr)

    def refresh_Img_plot(self, img):
        self.ax.cla()
        self.img = img
        self.imgArr = mpimg.pil_to_array(self.img['src'])
        self.imgArr.setflags(write=True)
        self.profImshow()
        self.ax.set_title(self.img['pltTitle'])
        self.ax.callbacks.connect('xlim_changed', self.on_xlims_change)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
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
        self.profImshow()

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
                self.x1_ = x1
                self.y1_ = y1
                self.dx1.append(self.x1_)
                self.dy1.append(self.y1_)
                self.x2_ = x2
                self.y2_ = y1
                self.dx2.append(self.imgWidth - self.x2_)
                self.dy2.append(self.y1_)
                self.x3_ = x1
                self.y3_ = y2
                self.dx3.append(self.x1_)
                self.dy3.append(self.imgHeight - self.y3_)
                self.x4_ = x2
                self.y4_ = y2
                self.dx4.append(self.imgWidth - self.x2_)
                self.dy4.append(self.imgHeight - self.y3_)
                self.stackImgArr.append(self.imgArr)
                self.dx_dy['topLeft'] = [sum(self.dx1), sum(self.dy1)]
                self.dx_dy['topRight'] = [self.refImgWidth - sum(self.dx2), sum(self.dy2)]
                self.dx_dy['bottomLeft'] = [sum(self.dx3), self.refImgHeight - sum(self.dy3)]
                self.dx_dy['bottomRight'] = [self.refImgWidth - sum(self.dx4), self.refImgHeight - sum(self.dy4)]
                self.img['src'] = self.img['src'].crop((x1, y1, x2, y2))
                self.imgWidth, self.imgHeight = self.img['src'].size
                self.imgArr = mpimg.pil_to_array(self.img['src'])
                self.imgArr.setflags(write=True)
                self.refresh_Img_plot(self.img)
                self.draw()
                self.set_init_coords()
            elif action == 'Delete':
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                ImgArrCopy = deepcopy(self.imgArr)
                self.stackImgArr.append(ImgArrCopy)
                self.imgArr[y1:y2, x1:x2] = 0
                self.img['src'] = Image.fromarray(self.imgArr)
                self.dx1.append(0)
                self.dx2.append(0)
                self.dx3.append(0)
                self.dx4.append(0)
                self.dy1.append(0)
                self.dy2.append(0)
                self.dy3.append(0)
                self.dy4.append(0)
                self.refresh_Img_plot(self.img)
                self.draw()
                self.set_init_coords()
        if action == 'Revert': #TODO: revert should store only changes to image array
            if self.stackImgArr:
                self.imgArr = self.stackImgArr[-1]
                self.img['src'] = Image.fromarray(self.imgArr)
                self.stackImgArr = self.stackImgArr[:-1]
                self.dx1 = self.dx1[:-1]
                self.dx2 = self.dx2[:-1]
                self.dx3 = self.dx3[:-1]
                self.dx4 = self.dx4[:-1]
                self.dy1 = self.dy1[:-1]
                self.dy2 = self.dy2[:-1]
                self.dy3 = self.dy3[:-1]
                self.dy4 = self.dy4[:-1]
                self.profImshow()
                self.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # TODO: Substitute all lines below /w argparse module
    if len(sys.argv) == 4:
        main = Window(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3:
        main = Window(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        main = Window(sys.argv[1])
    else:
        main = Window()
    main.show()
    sys.exit(app.exec_())