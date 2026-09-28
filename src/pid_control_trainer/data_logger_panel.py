from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

import pyqtgraph as pg
from pyqtgraph import mkPen

import numpy as np

from pathlib import Path

pen_color_list = ['b', 'g', 'y', 'c', 'm']

UI_PATH = Path(__file__).parent / 'data_logger_panel.ui'
Ui_Window, QtBaseClass = uic.loadUiType(str(UI_PATH))
class DataLogger(QWidget):
    def __init__(self, title_str, PVmin, PVmax, PVunit, data_size, Ts=1.0, time_horizon=5, dec_place=2):
        super(DataLogger, self).__init__()
        
        self.ui = Ui_Window()
        self.ui.setupUi(self)

        self.setWindowTitle(title_str)

        self.plot_area_PV = pg.PlotWidget()
        self.ui.verticalLayout_4.addWidget(self.plot_area_PV)

        self.plot_area_PV.setRange(xRange=(0, 1), update=True)
        self.plot_area_PV.setRange(yRange=(PVmin, PVmax), update=True)  
        self.plot_area_PV.showGrid(True, True)
        self.plot_area_PV.setLabel(axis='left', text=PVunit)
        self.plot_area_PV.setLabel(axis='bottom', text='time (s)')
        self.plot_area_PV.enableAutoRange(enable=True, y=True)
        PV_viewbox = self.plot_area_PV.getViewBox()
        PV_viewbox.setMouseMode(3)
        #self.plot_area_PV.sigXRangeChanged.connect(self.update_OP_plot_Xrange)
        self.plot_area_PV.hideButtons()
        self.PVplot = self.plot_area_PV.plot()
        gpen = mkPen('b', width=2)
        self.PVplot.setPen(gpen)
        
        self.plot_area_OP = pg.PlotWidget()
        self.ui.verticalLayout_6.addWidget(self.plot_area_OP)

        self.plot_area_OP.setRange(xRange=(0, 1), update=True)
        self.plot_area_OP.setRange(yRange=(0.0, 100.0), update=True)  
        self.plot_area_OP.showGrid(True, True)
        self.plot_area_OP.setLabel(axis='left', text="%")
        self.plot_area_OP.setLabel(axis='bottom', text='time (s)')
        self.plot_area_OP.enableAutoRange(enable=True, y=True)
        OP_viewbox = self.plot_area_OP.getViewBox()
        OP_viewbox.setMouseMode(3)
        #self.plot_area_OP.sigXRangeChanged.connect(self.update_PV_plot_Xrange)
        self.plot_area_OP.hideButtons()
        self.OPplot = self.plot_area_OP.plot()
        gpen = mkPen('g', width=2)
        self.OPplot.setPen(gpen)
        
        self.ui.comboBox.addItems(["5", "10", "15", "30", "60"])
        self.ui.comboBox.setCurrentIndex(0)
        self.timerange = 5*60  
        self.delt = Ts
        
        self.nsize = data_size
        self.timerecord = np.zeros(int(self.nsize), dtype=float)
        self.SPrecord = np.zeros(int(self.nsize), dtype=float)
        self.PVrecord = np.zeros(int(self.nsize), dtype=float)
        self.OPrecord = np.zeros(int(self.nsize), dtype=float)
        self.dataindex = 0

        self.dec_place = dec_place
        
        self.ui.pushButton_addHorizonLine.clicked.connect(self.add_horizonline_PV)
        self.ui.pushButton_addVertLine.clicked.connect(self.add_vertline_PV)
        self.ui.pushButton_addSlantedLine.clicked.connect(self.add_slantedline_PV)
        self.ui.pushButton_RemoveLines.clicked.connect(self.remove_all_lines)
        self.ui.pushButton_RemoveLastLine.clicked.connect(self.remove_last_line_PV)
        
        self.PV_horizon_line_list = []
        self.PV_horizon_textitem_list = []
        self.PV_vert_line_list = []
        self.PV_vert_text_list = []
        self.PV_lineseg_list = []
        
        self.PV_all_lines_list = []
        
        self.ui.pushButton_addHorizonLineOP.clicked.connect(self.add_horizonline_OP)
        self.ui.pushButton_addVertLineOP.clicked.connect(self.add_vertline_OP)
        self.ui.pushButton_addSlantedLineOP.clicked.connect(self.add_slantedline_OP)
        self.ui.pushButton_RemoveLinesOP.clicked.connect(self.remove_all_lines_OP)
        self.ui.pushButton_RemoveLastLineOP.clicked.connect(self.remove_last_line_OP)
        
        self.OP_horizon_line_list = []
        self.OP_horizon_textitem_list = []
        self.OP_vert_line_list = []
        self.OP_vert_text_list = []
        self.OP_lineseg_list = []
        
        self.OP_all_lines_list = []
        
        self.ui.radioButton_mousePan.toggled.connect(self.change_mouseMode_PVplot)
        self.ui.radioButton_mousePanOP.toggled.connect(self.change_mouseMode_OPplot)
        self.ui.checkBox_showSP.toggled.connect(self.show_SP_trend)
        
        self.ui.checkBox_Pause.clicked[bool].connect(self.activate_line_buttons)
        
    def show_SP_trend(self, checked=False):
        if checked:
            self.plot_area_PV.addItem(self.SPplot)
        else:
            self.plot_area_PV.removeItem(self.SPplot)
        
    def change_mouseMode_PVplot(self, checked=False):
        PV_viewbox = self.plot_area_PV.getViewBox()
        if checked:
            PV_viewbox.setMouseMode(3)
        else:
            PV_viewbox.setMouseMode(1)
            
    def change_mouseMode_OPplot(self, checked=False):
        OP_viewbox = self.plot_area_OP.getViewBox()
        if checked:
            OP_viewbox.setMouseMode(3)
        else:
            OP_viewbox.setMouseMode(1)
        
    def update_OP_plot_Xrange(self):
        #self.display_vertical_values_OP()
        self.display_horizontal_values()
        self.display_vertical_values()
        
        range_bound = self.plot_area_PV.getViewBox().viewRange()[0]
        
        self.plot_area_OP.sigXRangeChanged.disconnect()
        self.plot_area_OP.setXRange(range_bound[0], range_bound[1], padding=0)
        self.display_horizontal_values_OP()
        self.plot_area_OP.sigXRangeChanged.connect(self.update_PV_plot_Xrange)
        
    def update_PV_plot_Xrange(self):
        #self.display_vertical_values()
        self.display_horizontal_values_OP()
        self.display_vertical_values_OP()
        
        range_bound = self.plot_area_OP.getViewBox().viewRange()[0]
        
        self.plot_area_PV.sigXRangeChanged.disconnect()
        self.plot_area_PV.setXRange(range_bound[0], range_bound[1], padding=0)
        self.display_horizontal_values()
        self.plot_area_PV.sigXRangeChanged.connect(self.update_OP_plot_Xrange)
        
    def activate_line_buttons(self, checked):
        self.plot_area_PV.clear()
        self.plot_area_OP.clear()
        if checked:
            self.ui.pushButton_addHorizonLine.setEnabled(True)
            self.ui.pushButton_addVertLine.setEnabled(True)
            self.ui.pushButton_addSlantedLine.setEnabled(True)
            self.ui.pushButton_RemoveLines.setEnabled(True)
            self.ui.pushButton_RemoveLastLine.setEnabled(True)
            
            self.ui.pushButton_addHorizonLineOP.setEnabled(True)
            self.ui.pushButton_addVertLineOP.setEnabled(True)
            self.ui.pushButton_addSlantedLineOP.setEnabled(True)
            self.ui.pushButton_RemoveLinesOP.setEnabled(True)
            self.ui.pushButton_RemoveLastLineOP.setEnabled(True)
            
            self.ui.radioButton_mousePan.setEnabled(True)
            self.ui.radioButton_mouseRect.setEnabled(True)
            self.ui.radioButton_mousePanOP.setEnabled(True)
            self.ui.radioButton_mouseRectOP.setEnabled(True)
            
            self.ui.checkBox_showSP.setEnabled(True)

            self.plot_area_PV.disableAutoRange()
            self.plot_area_OP.disableAutoRange()
        
            self.plot_area_PV.plot(self.timerecord[:self.dataindex], 
                                 self.PVrecord[:self.dataindex], pen=mkPen('b',width=2))
            self.SPplot = pg.PlotDataItem(self.timerecord[:self.dataindex],
                                          self.SPrecord[:self.dataindex-1],
                                          stepMode=True, pen=mkPen('r',width=2))
            if self.ui.checkBox_showSP.isChecked():
                self.plot_area_PV.addItem(self.SPplot)
            
            self.plot_area_OP.plot(self.timerecord[:self.dataindex], 
                                 self.OPrecord[:self.dataindex-1],
                                 stepMode=True, pen=mkPen('g',width=2))
            
            self.plot_area_PV.sigXRangeChanged.connect(self.update_OP_plot_Xrange)
            self.plot_area_OP.sigXRangeChanged.connect(self.update_PV_plot_Xrange)
        else:
            self.plot_area_PV.sigXRangeChanged.disconnect()
            self.plot_area_OP.sigXRangeChanged.disconnect()
            
            self.ui.pushButton_addHorizonLine.setEnabled(False)
            self.ui.pushButton_addVertLine.setEnabled(False)
            self.ui.pushButton_addSlantedLine.setEnabled(False)
            self.ui.pushButton_RemoveLines.setEnabled(False)
            self.ui.pushButton_RemoveLastLine.setEnabled(False)
            
            self.ui.pushButton_addHorizonLineOP.setEnabled(False)
            self.ui.pushButton_addVertLineOP.setEnabled(False)
            self.ui.pushButton_addSlantedLineOP.setEnabled(False)
            self.ui.pushButton_RemoveLinesOP.setEnabled(False)
            self.ui.pushButton_RemoveLastLineOP.setEnabled(False)
            
            self.ui.radioButton_mousePan.setEnabled(False)
            self.ui.radioButton_mouseRect.setEnabled(False)
            self.ui.radioButton_mousePanOP.setEnabled(False)
            self.ui.radioButton_mouseRectOP.setEnabled(False)
            
            self.ui.checkBox_showSP.setEnabled(False)
            
            self.remove_all_lines()
            self.remove_all_lines_OP()

            self.PVplot = self.plot_area_PV.plot(pen=mkPen('b',width=2))
            self.OPplot = self.plot_area_OP.plot(pen=mkPen('g',width=2))

            self.update_chart_GUI()
            
    def remove_last_line_PV(self):
        if len(self.PV_all_lines_list) == 0:
            return
        
        line_info = self.PV_all_lines_list.pop()
        line_item = line_info['Line']
        text_item = line_info['Text']
                
        if line_info['Type'] == 0:
            try:
                self.PV_horizon_line_list.remove(line_item)
                self.PV_horizon_textitem_list.remove(text_item)    
                self.plot_area_PV.removeItem(line_item)
                self.plot_area_PV.removeItem(text_item)
            except:
                return
        elif line_info['Type'] == 1:
            try:
                self.PV_vert_line_list.remove(line_item)
                self.PV_vert_text_list.remove(text_item)
                self.plot_area_PV.removeItem(line_item)
                self.plot_area_PV.removeItem(text_item)
            except:
                return
        else:
            try:
                self.PV_lineseg_list.remove(line_item)
                self.plot_area_PV.removeItem(line_item)
            except:
                return
            
    def remove_last_line_OP(self):
        if len(self.OP_all_lines_list) == 0:
            return
        
        line_info = self.OP_all_lines_list.pop()
        line_item = line_info['Line']
        text_item = line_info['Text']
        
        if line_info['Type'] == 0:
            try:
                self.OP_horizon_line_list.remove(line_item)
                self.OP_horizon_textitem_list.remove(text_item)
                self.plot_area_OP.removeItem(line_item)
                self.plot_area_OP.removeItem(text_item)
            except:
                return
        elif line_info['Type'] == 1:
            try:
                self.OP_vert_line_list.remove(line_item)
                self.OP_vert_text_list.remove(text_item)
                self.plot_area_OP.removeItem(line_item)
                self.plot_area_OP.removeItem(text_item)
            except:
                return
        else:
            try:
                self.OP_lineseg_list.remove(line_item)
                self.plot_area_OP.removeItem(line_item)
            except:
                return
            
    def remove_all_lines(self):
        for i in range(len(self.PV_horizon_line_list)):
            hline = self.PV_horizon_line_list[i]
            self.plot_area_PV.removeItem(hline)
            
            text_item = self.PV_horizon_textitem_list[i]
            self.plot_area_PV.removeItem(text_item)
        
        self.PV_horizon_line_list = []
        self.PV_horizon_textitem_list = []
        
        for i in range(len(self.PV_vert_line_list)):
            vline = self.PV_vert_line_list[i]
            self.plot_area_PV.removeItem(vline)
            
            text_item = self.PV_vert_text_list[i]
            self.plot_area_PV.removeItem(text_item)
            
        self.PV_vert_line_list = []
        self.PV_vert_text_list = []
        
        for i in range(len(self.PV_lineseg_list)):
            sline = self.PV_lineseg_list[i]
            self.plot_area_PV.removeItem(sline)
            
        self.PV_lineseg_list = []
        
        self.PV_all_lines_list = []
        
    def remove_all_lines_OP(self):
        for i in range(len(self.OP_horizon_line_list)):
            hline = self.OP_horizon_line_list[i]
            self.plot_area_OP.removeItem(hline)
            
            text_item = self.OP_horizon_textitem_list[i]
            self.plot_area_OP.removeItem(text_item)
            
        self.OP_horizon_line_list = []
        self.OP_horizon_textitem_list = []
        
        for i in range(len(self.OP_vert_line_list)):
            vline = self.OP_vert_line_list[i]
            self.plot_area_OP.removeItem(vline)
            
            text_item = self.OP_vert_text_list[i]
            self.plot_area_OP.removeItem(text_item)
            
        self.OP_vert_line_list = []
        self.OP_vert_text_list = []
        
        for i in range(len(self.OP_lineseg_list)):
            sline = self.OP_lineseg_list[i]
            self.plot_area_OP.removeItem(sline)
            
        self.OP_lineseg_list = []
        
        self.OP_all_lines_list = []
        
    def add_horizonline_PV(self):
        gpen = mkPen('y', width=2, style=Qt.DashLine)
        range_bound = self.plot_area_PV.getViewBox().viewRange()[1]
        mid_point = (range_bound[1]-range_bound[0])/2 + range_bound[0]
        h_line = pg.InfiniteLine(pos=mid_point, angle=0, pen=gpen, movable=True)
        h_line.sigDragged.connect(self.display_horizontal_values)
        self.plot_area_PV.addItem(h_line)
        
        text_item = pg.TextItem(text=str(round(h_line.value(), 3)), color=pg.mkColor('y'), anchor=(0, 1))
        range_bound = self.plot_area_PV.getViewBox().viewRange()[0]
        text_item.setPos(range_bound[0], h_line.value())
        self.plot_area_PV.addItem(text_item)
        
        self.PV_horizon_line_list.append(h_line)
        self.PV_horizon_textitem_list.append(text_item)
        
        line_info = {'Line': h_line, 'Text': text_item, 'Type': 0}
        self.PV_all_lines_list.append(line_info)
        
    def add_horizonline_OP(self):
        gpen = mkPen('y', width=2, style=Qt.DashLine)
        range_bound = self.plot_area_OP.getViewBox().viewRange()[1]
        mid_point = (range_bound[1]-range_bound[0])/2 + range_bound[0]
        h_line = pg.InfiniteLine(pos=mid_point, angle=0, pen=gpen, movable=True)
        h_line.sigDragged.connect(self.display_horizontal_values_OP)
        self.plot_area_OP.addItem(h_line)
        
        text_item = pg.TextItem(text=str(round(h_line.value(), 3)), color=pg.mkColor('y'), anchor=(0, 1))
        range_bound = self.plot_area_OP.getViewBox().viewRange()[0]
        text_item.setPos(range_bound[0], h_line.value())
        self.plot_area_OP.addItem(text_item)
        
        self.OP_horizon_line_list.append(h_line)
        self.OP_horizon_textitem_list.append(text_item)
        
        line_info = {'Line': h_line, 'Text': text_item, 'Type': 0}
        self.OP_all_lines_list.append(line_info)
        
    def add_vertline_PV(self):
        gpen = mkPen('y', width=2, style=Qt.DashLine)
        range_bound = self.plot_area_PV.getViewBox().viewRange()[0]
        mid_point = (range_bound[1]-range_bound[0])/2 + range_bound[0]
        v_line = pg.InfiniteLine(pos=mid_point, angle=90, pen=gpen, movable=True)
        v_line.sigDragged.connect(self.display_vertical_values)
        self.plot_area_PV.addItem(v_line)
        
        text_item = pg.TextItem(text=str(round(v_line.value(), 3)), color=pg.mkColor('y'), anchor=(0, 1))
        range_bound = self.plot_area_PV.getViewBox().viewRange()[1]
        text_item.setPos(v_line.value(), range_bound[0])
        self.plot_area_PV.addItem(text_item)
        
        self.PV_vert_line_list.append(v_line)
        self.PV_vert_text_list.append(text_item)
        
        line_info = {'Line': v_line, 'Text': text_item, 'Type': 1}
        self.PV_all_lines_list.append(line_info)
        
    def add_vertline_OP(self):
        gpen = mkPen('y', width=2, style=Qt.DashLine)
        range_bound = self.plot_area_OP.getViewBox().viewRange()[0]
        mid_point = (range_bound[1]-range_bound[0])/2 + range_bound[0]
        v_line = pg.InfiniteLine(pos=mid_point, angle=90, pen=gpen, movable=True)
        v_line.sigDragged.connect(self.display_vertical_values_OP)
        self.plot_area_OP.addItem(v_line)
        
        text_item = pg.TextItem(text=str(round(v_line.value(), 3)), color=pg.mkColor('y'), anchor=(0, 1))
        range_bound = self.plot_area_OP.getViewBox().viewRange()[1]
        text_item.setPos(v_line.value(), range_bound[0])
        self.plot_area_OP.addItem(text_item)
        
        self.OP_vert_line_list.append(v_line)
        self.OP_vert_text_list.append(text_item)
        
        line_info = {'Line': v_line, 'Text': text_item, 'Type': 1}
        self.OP_all_lines_list.append(line_info)
        
    def add_slantedline_PV(self):
        range_boundx = self.plot_area_PV.getViewBox().viewRange()[0]
        range_boundy = self.plot_area_PV.getViewBox().viewRange()[1]
        intervalx = (range_boundx[1]-range_boundx[0])/4
        midpointx = (range_boundx[1]-range_boundx[0])/2
        intervaly = (range_boundy[1]-range_boundy[0])/4
        gpen = mkPen('y', width=2, style=Qt.DashLine)
        s_line = pg.LineSegmentROI(positions=([range_boundx[0]+midpointx,range_boundy[0]+intervaly],
                                              [range_boundx[1]-intervalx,range_boundy[1]-intervaly]))
        s_line.setPen(gpen)
        self.plot_area_PV.addItem(s_line)
        
        self.PV_lineseg_list.append(s_line)
        
        line_info = {'Line': s_line, 'Text': None, 'Type': 2}
        self.PV_all_lines_list.append(line_info)
        
    def add_slantedline_OP(self):
        range_boundx = self.plot_area_OP.getViewBox().viewRange()[0]
        range_boundy = self.plot_area_OP.getViewBox().viewRange()[1]
        intervalx = (range_boundx[1]-range_boundx[0])/4
        midpointx = (range_boundx[1]-range_boundx[0])/2
        intervaly = (range_boundy[1]-range_boundy[0])/4
        gpen = mkPen('y', width=2, style=Qt.DashLine)
        s_line = pg.LineSegmentROI(positions=([range_boundx[0]+midpointx,range_boundy[0]+intervaly],
                                              [range_boundx[1]-intervalx,range_boundy[1]-intervaly]))
        s_line.setPen(gpen)
        self.plot_area_OP.addItem(s_line)
        
        self.OP_lineseg_list.append(s_line)
        
        line_info = {'Line': s_line, 'Text': None, 'Type': 2}
        self.OP_all_lines_list.append(line_info)
        
    def display_horizontal_values(self):
        for i in range(len(self.PV_horizon_line_list)):
            text_item = self.PV_horizon_textitem_list[i]
            self.plot_area_PV.removeItem(text_item)
            
            h_line = self.PV_horizon_line_list[i]
            text_item.setText(str(round(h_line.value(), 3)))
            range_bound = self.plot_area_PV.getViewBox().viewRange()[0]
            text_item.setPos(range_bound[0], h_line.value())
            self.plot_area_PV.addItem(text_item)
            
    def display_horizontal_values_OP(self):
        for i in range(len(self.OP_horizon_line_list)):
            text_item = self.OP_horizon_textitem_list[i]
            self.plot_area_OP.removeItem(text_item)
            
            h_line = self.OP_horizon_line_list[i]
            text_item.setText(str(round(h_line.value(), 3)))
            range_bound = self.plot_area_OP.getViewBox().viewRange()[0]
            text_item.setPos(range_bound[0], h_line.value())
            self.plot_area_OP.addItem(text_item)
            
    def display_vertical_values(self):
        for i in range(len(self.PV_vert_line_list)):
            text_item = self.PV_vert_text_list[i]
            self.plot_area_PV.removeItem(text_item)
            
            v_line = self.PV_vert_line_list[i]
            text_item.setText(str(round(v_line.value(), 3)))
            range_bound = self.plot_area_PV.getViewBox().viewRange()[1]
            text_item.setPos(v_line.value(), range_bound[0])
            self.plot_area_PV.addItem(text_item)
            
    def display_vertical_values_OP(self):
        for i in range(len(self.OP_vert_line_list)):
            text_item = self.OP_vert_text_list[i]
            self.plot_area_OP.removeItem(text_item)
            
            v_line = self.OP_vert_line_list[i]
            text_item.setText(str(round(v_line.value(), 3)))
            range_bound = self.plot_area_OP.getViewBox().viewRange()[1]
            text_item.setPos(v_line.value(), range_bound[0])
            self.plot_area_OP.addItem(text_item)
        
    def update_chart_record(self, t, SP, PV, OP):
        if self.dataindex >= self.nsize:
            self.timerecord[:] = 0.0
            self.SPrecord[:] = 0.0
            self.PVrecord[:] = 0.0
            self.OPrecord[:] = 0.0
            self.dataindex = 0
        self.timerecord[self.dataindex] = t
        self.SPrecord[self.dataindex] = SP
        self.PVrecord[self.dataindex] = PV
        self.OPrecord[self.dataindex] = OP
        self.dataindex += 1   

    def update_chart_GUI(self):
        if self.isVisible() and not self.ui.checkBox_Pause.isChecked():
            dataindex = self.dataindex
            self.timerange = float(self.ui.comboBox.currentText())*60
            nbeforesize = int(self.timerange/self.delt)+1
            self.PVplot.setData(self.timerecord[max(0,dataindex-1-nbeforesize):dataindex], 
                                 self.PVrecord[max(0,dataindex-1-nbeforesize):dataindex])
            self.OPplot.setData(self.timerecord[max(0,dataindex-1-nbeforesize):dataindex], 
                                 self.OPrecord[max(0,dataindex-1-nbeforesize):dataindex])
        
            time = self.timerecord[dataindex-1]
            self.plot_area_PV.setXRange(time-self.timerange, time)
            self.plot_area_OP.setXRange(time-self.timerange, time)
            
            self.plot_area_PV.enableAutoRange(enable=True, y=True)
            self.plot_area_OP.enableAutoRange(enable=True, y=True)
        
            self.ui.label_time.setText("Time: " + str(round(time, 2)) + ' s')
            PV = self.PVrecord[dataindex-1]
            self.ui.label_PV.setText("PV: " + str(round(PV, self.dec_place)))
            OP = self.OPrecord[dataindex-1]
            self.ui.label_OP.setText("OP: " + str(round(OP, self.dec_place)))
            SP = self.SPrecord[dataindex-1]
            self.ui.label_SP.setText("SP: " + str(round(SP, self.dec_place)))
            
    def show_window(self):
        if not self.isVisible():
            self.show()
        else:
            self.activateWindow() 
            
    #def showEvent(self, event):
    #    self.resize(self.width_ui, self.height_ui)