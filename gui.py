#!/usr/bin/env python

import sys
import numpy as np
import matplotlib
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from window import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):
    matplotlib.use('tkagg')
    data = ""

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.openButton.clicked.connect(self.load_file)
        self.ui.saveButton.clicked.connect(self.save_file)
        self.ui.do_some.clicked.connect(self.do)

        self.ui.figure = Figure(figsize=(5, 4), dpi=100)
        self.ui.canvas = FigureCanvas(self.ui.figure)
        self.ui.verticalLayout.addWidget(self.ui.canvas)

        self.ax = self.ui.figure.add_subplot(projection='3d')

    def load_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Вибрати файл", "", "Текстові файли (*.gcode);;Усі файли (*)", options=options)
        if file_name:
            self.data = self.load_data_from_file(file_name)
            self.plot_data(self.data)

    def save_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Зберегти файл", "", "Текстові файли (*.gcode);;Усі файли (*)", options=options)
        if file_name:
            with open('{}.gcode'.format(file_name.replace('.gcode', '')), 'w') as file:
                file.write(self.data)

    def do(self):
        self.data = self.move_xy(self.data, self.ui.move_x.value(), self.ui.move_y.value())
        self.data = self.rotate_data(self.data)
        self.data = self.mirror_xy(self.data)
        self.data = self.scale_code(self.data)
        self.data = self.combine_gcode(self.data)
        self.plot_data(self.data)

    def sizes(self, data):
        max_x = max_y = min_x = min_y = 0

        for row in data.split('\n'):
            for b in row.split():
                if b.find('X') != -1:
                    x = float(b.replace('X', ''))
                    if x > max_x:
                        max_x = x
                    if x < min_x:
                        min_x = x
                if b.find('Y') != -1:
                    y = float(b.replace('Y', ''))
                    if y > max_y:
                        max_y = y
                    if y < min_y:
                        min_y = y
            size_x = max_x - min_x
            size_y = max_y - min_y
        return [max_x, max_y, min_x, min_y, size_x, size_y]

    def move_xy(self, data, x, y):
        n_data = ''
        for row in data.split('\n'):
            n_row = []
            for b in row.split():
                if b.find('X') != -1:
                    n_b = 'X{}'.format((float(b.replace('X', '')) + x))
                elif b.find('Y') != -1:
                    n_b = 'Y{}'.format((float(b.replace('Y', '')) + y))
                else:
                    n_b = b
                n_row.append(n_b)
            n_data = "{}{}\n".format(n_data, ' '.join(n_row))
        return n_data

    def rotate_data(self, data):
        rotate = int(self.ui.rotate.value())
        if rotate != 0:
            if rotate == -90:
                rotate = 270
            for i in range(int(rotate / 90)):
                g_size = self.sizes(data)
                n_data = ''
                for row in data.split('\n'):
                    n_row = []
                    for b in row.split():
                        if b.find('X') != -1:
                            n_val = -float(b.replace('X', '')) + g_size[4]
                            n_b = 'Y{}'.format(n_val)
                        elif b.find('Y') != -1:
                            val = b.replace('Y', '')
                            n_b = 'X{}'.format(float(val))
                        else:
                            n_b = b
                        n_row.append(n_b)
                    n_data = "{}{}\n".format(n_data, ' '.join(n_row))
                data = n_data
        return data

    def mirror_xy(self, data):
        n_data = ''
        x=self.ui.mirror_x.isChecked()
        y=self.ui.mirror_y.isChecked()

        if x or y:
            g_size = self.sizes(data)
            for row in data.split('\n'):
                n_row = []
                for b in row.split():
                    if b.find('X') != -1 and x:
                        n_val = -float(b.replace('X', '')) + g_size[4]
                        n_b = 'X{}'.format(n_val)
                    elif b.find('Y') != -1 and y:
                        n_val = -float(b.replace('Y', '')) + g_size[5]
                        n_b = 'Y{}'.format(n_val)
                    else:
                        n_b = b
                    n_row.append(n_b)
                n_data = "{}{}\n".format(n_data, ' '.join(n_row))
        else:
            n_data = data

        return n_data

    def scale_code(self, data):
        n_data = ''
        if self.ui.scale.value() > 0:
            rate = float(int(self.ui.scale.value()) / 100)
            for row in data.split('\n'):
                n_row = []
                for b in row.split():
                    if b.find('X') != -1:
                        x = float(b.replace('X', ''))
                        n_b = 'X{}'.format(float(x * rate))
                    elif b.find('Y') != -1:
                        y = float(b.replace('Y', ''))
                        n_b = 'Y{}'.format(float(y * rate))
                    else:
                        n_b = b
                    n_row.append(n_b)
                n_data = "{}{}\n".format(n_data, ' '.join(n_row))
        else:
            n_data = data

        return n_data

    def combine_gcode(self, data):
        out_data = ""

        x = int(self.ui.combine_x.value())
        y = int(self.ui.combine_y.value())

        if x > 1 or y > 1:
            offset = int(self.ui.combine_margin.value())
            move_x = int(self.ui.move_x.value())
            move_y = int(self.ui.move_y.value())

            g_size = self.sizes(data)
            for i in range(x):
                for j in range(y):
                    m_x = int((g_size[4] + int(offset)) * i)
                    m_y = int((g_size[5] + int(offset)) * j)
                    out_data = '{}{}'.format(out_data, self.move_xy(data, m_x, m_y))
            if move_x > 0 or move_y > 0:
                out_data = self.move_xy(data, move_x, move_y)
        else:
            out_data = data

        return out_data

    def plot_data(self, data):
        self.ax.clear()
        xs = 0
        ys = 0
        zs = 0

        x_points = []
        y_points = []
        z_points = []

        for row in data.split('\n'):
            for b in row.split():
                if b.find('X') != -1:
                    xs = float(b.replace('X', ''))
                if b.find('Y') != -1:
                    ys = float(b.replace('Y', ''))
                if b.find('Z') != -1:
                    zs = float(b.replace('Z', ''))
            if row.find('X') != -1 or row.find('Y') != -1 or row.find('Z') != -1:
                x_points.append(xs)
                y_points.append(ys)
                z_points.append(zs)

        self.ax.set_box_aspect((np.ptp(x_points), np.ptp(y_points), np.ptp(z_points) * 5))
        self.ax.plot(x_points, y_points, z_points)

        self.ui.canvas.draw()

    def load_data_from_file(self, file_name):
        with open(file_name) as file:
            data = file.read()
        return data


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    main_window = MainWindow()
    main_window.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print('Закриття вікна')

