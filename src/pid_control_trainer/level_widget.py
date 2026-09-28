# -*- coding: utf-8 -*-
"""
Created on Sun Sep 30 22:19:34 2018

@author: nazri
"""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QColor, QPen

# from PySide2.QtCore import Qt, QRectF
# from PySide2.QtWidgets import QWidget
# from PySide2.QtGui import QPainter, QFont, QColor, QPen

class LevelWidget(QWidget):
    def __init__(self, color, max_cap = 100):      
        super().__init__()
        self.initUI()
        self.MAX_CAPACITY = max_cap
        self.color = color

    def initUI(self):
        self.setMinimumSize(10, 1)
        self.value = 0

    def setValue(self, value):
        self.value = value

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):
        size = self.size()
        w = size.width()
        h = size.height()
        till = ((h / self.MAX_CAPACITY) * self.value)
        rectangle = QRectF(0, 0, w, till)
        rectangle.moveBottom(h)
        qp.setPen(self.color)
        qp.setBrush(self.color)
        qp.drawRect(rectangle)
        pen = QPen(QColor(20, 20, 20), 1, Qt.SolidLine)
        qp.setPen(pen)
        qp.setBrush(Qt.NoBrush)
        qp.drawRect(0, 0, w-1, h-1)

        
class LevelBarWidget(LevelWidget):
    def __init__(self, color, max_cap=1, interval=0.1, fontsize=7.5, minval=0.0, maxval=1.0):      
        super().__init__(color, max_cap)
        self.initUI()
        self.interval = interval
        self.fontsize = fontsize
        self.minval = minval
        self.maxval = maxval

    def drawWidget(self, qp):
        font = QFont('Serif', -1, QFont.Light)
        font.setPointSizeF(self.fontsize)
        qp.setFont(font)
        size = self.size()
        w = size.width()
        h = size.height()
        npoints = int(self.MAX_CAPACITY/self.interval)
        step = int(round(h / npoints))
        till = ((h / self.MAX_CAPACITY) * self.value)
        rectangle = QRectF(0, 0, w, till)
        rectangle.moveBottom(h)
        qp.setPen(self.color) # QColor(0, 0, 255)
        qp.setBrush(self.color)
        qp.drawRect(rectangle)
        pen = QPen(QColor(20, 20, 20), 1, Qt.SolidLine)
        qp.setPen(pen)
        qp.setBrush(Qt.NoBrush)
        qp.drawRect(0, 0, w-1, h-1)
        initpoint = self.interval
        for i in range(step, npoints*step, step):
            qp.drawLine(0, h-i, 5, h-i)
            metrics = qp.fontMetrics()
            fh = metrics.height()
            qp.drawText(int(w/4), int(h-i+fh/2.5), str(round(initpoint*(self.maxval-self.minval)+self.minval, 2)))
            initpoint += self.interval  