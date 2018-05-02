import sys
from PyQt5.QtWidgets import *
from matplotlib.patches import Rectangle
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
# from matplotlib.widgets import LassoSelector

MF = 'test/FT1/'
MFA = MF + 'Analysis/'
Path = MFA + 'gridFit/ablation_marks_XYOLD'
oldX, oldY = np.load(Path + '.npy')

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Ablation marks region processing')
        self.setGeometry(10, 10, 750, 750)

        mainMenu = self.menuBar()
        mainMenu.setNativeMenuBar(False)
        fileMenu = mainMenu.addMenu('File')
        helpMenu = mainMenu.addMenu('Help')

        widget = QWidget(self)
        self.setCentralWidget(widget)
        vlay = QVBoxLayout()
        hlay = QHBoxLayout(widget)
        hlay.addLayout(vlay)

        #Buttons
        selectb = QPushButton('Crop', self)
        selectb.clicked.connect(lambda: m.canvas.on_activated('Crop', m.canvas.x1, m.canvas.y1,
                                                              m.canvas.x2, m.canvas.y2))
        deleteb = QPushButton('Delete', self)
        deleteb.clicked.connect(lambda: m.canvas.on_activated('Delete', m.canvas.x1, m.canvas.y1,
                                                              m.canvas.x2, m.canvas.y2))
        revertb = QPushButton('Revert', self)

        # Nested layout
        vlay2 = QVBoxLayout()
        vlay2.addWidget(selectb)
        vlay2.addWidget(deleteb)
        vlay2.addWidget(revertb)

        m = WidgetPlot(self)

        hlay.addWidget(m)
        hlay.addLayout(vlay2)

        # #TODO: Add lasso to the tools list
        #
        # self.comboBox = QComboBox(self)
        # self.comboBox.move(620, 180)
        # self.comboBox.setObjectName(("comboBox"))
        # self.comboBox.addItem("Rectqngular")
        # self.comboBox.addItem("Lasso")

        # menubar = self.menuBar()
        # fileMenu = menubar.addMenu('Import')
        # fileMenu.addAction(QAction('Data', self))
        # self.show()

class WidgetPlot(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.canvas = PlotCanvas(self, width=6, height=5)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.plot()

    def plot(self):
        self.ax.scatter(oldX, oldY, 5)
        self.ax.axis('equal')
        self.ax.set_title('Loaded data')

        def toggle_selector(event):
            if event.key in ['Q', 'q'] and toggle_selector.RS.active:
                print(' RectangleSelector deactivated.')
                toggle_selector.RS.set_active(False)
            if event.key in ['A', 'a'] and not toggle_selector.RS.active:
                print(' RectangleSelector activated.')
                toggle_selector.RS.set_active(True)

        toggle_selector.RS = RectangleSelector(self.ax, self.select_rectangle_callback,
                                               drawtype='box', useblit=True,
                                               button=[1, 3],  # don't use middle button
                                               minspanx=5, minspany=5,
                                               spancoords='pixels',
                                               interactive=True,
                                               state_modifier_keys={'square': 'shift'})

        # self.pts = self.ax.scatter(oldX, oldY, 5)
        # selector = SelectFromCollection(self.ax, self.pts)
        plt.connect('key_press_event', toggle_selector)

    def select_rectangle_callback(self, eclick, erelease):
        self.x1, self.y1 = eclick.xdata, eclick.ydata
        self.x2, self.y2 = erelease.xdata, erelease.ydata
        print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (self.x1, self.y1, self.x2, self.y2))
        print(" The button you used were: %s %s" % (eclick.button, erelease.button))

    def on_activated(self, action, x1, y1, x2, y2):
        if action == 'Crop':
            x_range = np.intersect1d(np.where(oldX >= x1)[0], np.where(oldX <= x2)[0])
            selectedX = np.take(oldX, x_range)
            selectedY = np.take(oldY, x_range)
            y_range = np.intersect1d(np.where(selectedY >= y1)[0], np.where(selectedY <= y2)[0])
            newX = np.take(selectedX, y_range)
            newY = np.take(selectedY, y_range)
            self.ax.cla()
            self.ax.scatter(newX, newY)
            print('Import')
            self.ax.axis('equal')
            self.ax.set_title('Cropped data')
            self.draw()
        if action == 'Delete':
            print('Delete')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())


# class SelectFromCollection(object):
#
#     def __init__(self, ax, collection, alpha_other=0.3):
#         self.canvas = ax.figure.canvas
#         self.collection = collection
#         self.alpha_other = alpha_other
#
#         self.xys = collection.get_offsets()
#         self.Npts = len(self.xys)
#
#         # Ensure that we have separate colors for each object
#         self.fc = collection.get_facecolors()
#         if len(self.fc) == 0:
#             raise ValueError('Collection must have a facecolor')
#         elif len(self.fc) == 1:
#             self.fc = np.tile(self.fc, (self.Npts, 1))
#
#         self.lasso = LassoSelector(ax, onselect=self.onselect)
#         self.ind = []
#
#     def onselect(self, verts):
#         path = Path(verts)
#         self.ind = np.nonzero(path.contains_points(self.xys))[0]
#         self.fc[:, -1] = self.alpha_other
#         self.fc[self.ind, -1] = 1
#         self.collection.set_facecolors(self.fc)
#         self.canvas.draw_idle()
#
#     def disconnect(self):
#         self.lasso.disconnect_events()
#         self.fc[:, -1] = 1
#         self.collection.set_facecolors(self.fc)
#         self.canvas.draw_idle()
