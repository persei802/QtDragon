#!/usr/bin/env python
import sys
import os
import math
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QPoint, QLine, QRect, QFile, Qt, QEvent
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor

class Preview(QtWidgets.QWidget):
    def __init__(self):
        super(Preview, self).__init__()
        self.num_holes = 0
        self.first_angle = 0.0

    def paintEvent(self, event):
        painter = QPainter(self)
#        painter.begin(self)
        painter.setBrush(QColor(200, 200, 200, 255))
        painter.drawRect(event.rect())
        self.draw_main_circle(event, painter)
        self.draw_crosshair(event, painter)
        self.draw_holes(event, painter)
        painter.end()        

    def draw_main_circle(self, event, qp):
        size = self.size()
        w = size.width()
        h = size.height()
        center = QPoint(w/2, h/2)
        diameter = min(w, h) -20
        qp.setPen(QPen(Qt.black, 1))
        qp.drawEllipse(center, diameter/2, diameter/2)

    def draw_crosshair(self, event, qp):
        size = self.size()
        w = size.width()
        h = size.height()
        qp.setPen(QPen(Qt.black, 1))
        p1 = QPoint(int(w/2), 0)
        p2 = QPoint(int(w/2), h)
        p3 = QPoint(0, int(h/2))
        p4 = QPoint(w, int(h/2))
        qp.drawLine(p1, p2)
        qp.drawLine(p3, p4)

    def draw_holes(self, event, qp):
        size = self.size()
        w = size.width()
        h = size.height()
        center = QPoint(w/2, h/2)
        diameter = min(w, h) -20
        qp.setPen(QPen(Qt.black, 2))
        for i in range(self.num_holes):
            r = diameter/2
            theta = ((360.0/self.num_holes) * i) + self.first_angle
            x = r * math.cos(math.radians(theta))
            y = r * math.sin(math.radians(theta))
            x = round(x, 3)
            y = -round(y, 3) # need this to make it go CCW
            p = QPoint(x, y) + center
            qp.drawEllipse(p, 8, 8)

    def set_num_holes(self, num):
        self.num_holes = num

    def set_first_angle(self, angle):
        self.first_angle = angle

class Hole_Circle(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Hole_Circle, self).__init__(parent)
        # Load the widgets UI file:
        self.filename = os.path.join(os.getcwd(), 'hole_circle.ui')
        try:
            self.instance = uic.loadUi(self.filename, self)
        except AttributeError as e:
            print("Error: ", e)
        self.preview = Preview()
        self.layout_preview.insertWidget(0, self.preview)

        # set up Help messagebox
        help_file = open("hole_circle_help.txt", "r")
        help_text = help_file.read()
        self.mb = QMessageBox()
        self.mb.setIcon(QMessageBox.Information)
        self.mb.setWindowTitle("Hole Circle Help")
        self.mb.setText(help_text)
        self.mb.setStandardButtons(QMessageBox.Ok)

        # set valid input formats for lineEdits
        self.lineEdit_spindle.setValidator(QtGui.QDoubleValidator(0, 99999, 0))
        self.lineEdit_num_holes.setValidator(QtGui.QDoubleValidator(0, 99, 0))
        self.lineEdit_radius.setValidator(QtGui.QDoubleValidator(0, 999, 2))
        self.lineEdit_first.setValidator(QtGui.QDoubleValidator(-999, 999, 2))
        self.lineEdit_safe_z.setValidator(QtGui.QDoubleValidator(0, 99, 2))
        self.lineEdit_start_height.setValidator(QtGui.QDoubleValidator(0, 99, 2))
        self.lineEdit_depth.setValidator(QtGui.QDoubleValidator(0, 99, 2))
        self.lineEdit_drill_feed.setValidator(QtGui.QDoubleValidator(0, 999, 2))
        self.checked = QtGui.QPixmap('images/checked.png')
        self.unchecked = QtGui.QPixmap('images/unchecked.png')
        self.unit_code = "G21"
        self.rpm = 0
        self.num_holes = 0
        self.radius = 0.0
        self.first = 0.0
        self.safe_z = 0.0
        self.start = 0.0
        self.depth = 0.0
        self.drill_feed = 0.0
        self.valid = True
        self.units_changed()

        # signal connections
        self.btn_validate.clicked.connect(self.validate)
        self.btn_create.clicked.connect(self.create_program)
        self.btn_mm.clicked.connect(self.units_changed)
        self.btn_inch.clicked.connect(self.units_changed)
        self.btn_help.clicked.connect(lambda obj: self.mb.show())

    def units_changed(self):
        if self.btn_inch.isChecked():
            unit = "IMPERIAL"
        else:
            unit = "METRIC"
        self.lbl_units_info.setText("**NOTE - All units are in {}".format(unit))

    def clear_all(self):
        self.lbl_spindle_ok.setPixmap(self.unchecked)
        self.lbl_num_holes_ok.setPixmap(self.unchecked)
        self.lbl_radius_ok.setPixmap(self.unchecked)
        self.lbl_first_ok.setPixmap(self.unchecked)
        self.lbl_safe_z_ok.setPixmap(self.unchecked)
        self.lbl_start_height_ok.setPixmap(self.unchecked)
        self.lbl_depth_ok.setPixmap(self.unchecked)
        self.lbl_drill_feed_ok.setPixmap(self.unchecked)
        
    def validate(self):
        self.valid = True
        self.clear_all()
        try:
            self.rpm = int(self.lineEdit_spindle.text())
            self.num_holes = int(self.lineEdit_num_holes.text())
            self.radius = float(self.lineEdit_radius.text())
            self.first = float(self.lineEdit_first.text())
            self.safe_z = float(self.lineEdit_safe_z.text())
            self.start = float(self.lineEdit_start_height.text())
            self.depth = float(self.lineEdit_depth.text())
            self.drill_feed = float(self.lineEdit_drill_feed.text())
        except:
            print("Entries cannot be blank")
            return
        if self.rpm > 0:
            self.lbl_spindle_ok.setPixmap(self.checked)
        else:
            self.valid = False

        if self.num_holes > 0:
            self.lbl_num_holes_ok.setPixmap(self.checked)
        else:
            self.valid = False

        if self.radius > 0.0:
            self.lbl_radius_ok.setPixmap(self.checked)
        else:
            self.valid = False

        if self.first < 360.0:
            self.lbl_first_ok.setPixmap(self.checked)
        else:
            self.valid = False

        if self.safe_z > 0.0:
            self.lbl_safe_z_ok.setPixmap(self.checked)
        else:
            self.valid = False

        if self.start > 0.0:
            self.lbl_start_height_ok.setPixmap(self.checked)
        else:
            self.valid = False

        if self.depth > 0.0:
            self.lbl_depth_ok.setPixmap(self.checked)
        else:
            self.valid = False

        if self.drill_feed > 0.0:
            self.lbl_drill_feed_ok.setPixmap(self.checked)
        else:
            self.valid = False
        
        if self.valid is True:
            self.preview.set_num_holes(self.num_holes)
            self.preview.set_first_angle(self.first)
            self.update()

    def create_program(self):
        self.validate()
        if self.valid is False:
            print("There are errors in input fields")
            return
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save to file","","All Files (*);;ngc Files (*.ngc)", options=options)
        if fileName:
            self.calculate_toolpath(fileName)
        else:
            print("Program creation aborted")

    def calculate_toolpath(self, fname):
        comment = self.lineEdit_comment.text()
        self.line_num = 5
        self.file = open(fname, 'w')
        # opening preamble
        self.file.write("%\n")
        self.file.write("({})\n".format(comment))
        self.next_line("{} G40 G49 G64 P0.03".format(self.unit_code))
        self.next_line("G17")
        self.next_line("G0 Z{}".format(self.safe_z))
        self.next_line("G0 X0.0 Y0.0")
        self.next_line("S{} M3".format(self.rpm))
        # main section
        for i in range(self.num_holes):
            next_angle = ((360.0/self.num_holes) * i) + self.first
            next_angle = round(next_angle, 3)
            self.next_line("G0 @{} ^{}".format(self.radius, next_angle))
            self.next_line("Z{}".format(self.start))
            self.next_line("G1 Z-{} F{}".format(self.depth, self.drill_feed))
            self.next_line("G0 Z{}".format(self.safe_z))
        # closing section
        self.next_line("G0 x0.0 Y0.0")
        self.next_line("M2")
        self.file.write("%\n")
        self.file.close()

    def btn_help_clicked(self, state):
        self.mb.show()

    def next_line(self, text):
        self.file.write("N{} ".format(self.line_num) + text + "\n")
        self.line_num += 5

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = Hole_Circle()
    w.show()
    sys.exit( app.exec_() )

