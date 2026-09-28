# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 12:12:44 2019

@author: nazri
"""
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtGui import QDoubleValidator

# from PySide2.QtUiTools import QUiLoader
# from PySide2.QtCore import Qt
# from PySide2.QtWidgets import QVBoxLayout, QWidget, QTableWidgetItem, QListWidgetItem, QDialog, QMessageBox
# from PySide2.QtGui import QDoubleValidator

from .level_widget import LevelBarWidget

from .data_logger_panel import DataLogger
from .pid_panel import PIDInputPanel

import numpy as np

from pathlib import Path

pen_color_list = ['b', 'g', 'y', 'c', 'm']        

UI_PATH = Path(__file__).parent / 'controller_panel.ui'
Ui_Window, QtBaseClass = uic.loadUiType(str(UI_PATH))
class ControllerPanel(QWidget):
    def __init__(self, control_str, PV, PVmin, PVmax, unit_str, valve_str, 
                 MV, MVmin=0.0, MVmax=100.0, Ts=1.0, 
                 mode=0, action=-1, Kc=1.0, Ti=0.0, Td=0.0, simtime=4.0,
                 isSlave=False, masterLoopObj=None):
        super(ControllerPanel, self).__init__()
        
        self.ui = Ui_Window()
        self.ui.setupUi(self)

        # loader = QUiLoader()
        # self.ui = loader.load('Controller_Panel.ui', self)

        self.setWindowTitle(control_str)
        # layout = QVBoxLayout()
        # layout.addWidget(self.ui)
        # self.setLayout(layout)
        #self.setGeometry(0, 0, self.ui.size().width(), self.ui.size().height())
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, on=False)
        
        self.desc = control_str
        self.unit_str = unit_str
        self.ui.label_OP.setText('OP (' + valve_str + '):')
        
        self.Ts = Ts
        #self.ui.label_Ts.setText(str(self.Ts))
        
        self.OPmin = 0
        self.OPmax = 100
        self.OP_bar = LevelBarWidget(Qt.green, minval=self.OPmin, maxval=self.OPmax)
        self.ui.verticalLayout_OP.addWidget(self.OP_bar)
        OP = (MV-MVmin)/(MVmax-MVmin)*100    # in percentage
        if OP < self.OPmin:
            OP = self.OPmin
        if OP > self.OPmax:
            OP = self.OPmax
        self.OP = OP
        self.OPbias = OP
        self.MVmin = MVmin
        self.MVmax = MVmax
        self.ui.lineEdit_OP.setText(str(np.round(self.OP, 2)))
        double_validator = QDoubleValidator()
        self.ui.lineEdit_OP.setValidator(double_validator)
        self.ui.lineEdit_OP.editingFinished.connect(self.change_OP)
        self.ui.label_OPvalue.setText(str(np.round(self.OP, 2)))
        self.ui.label_OPmin.setText(str(round(self.OPmin, 2)))
        self.ui.label_OPmax.setText(str(round(self.OPmax, 2)))
        
        self.OP_bar.setValue(self.OP/100)
        self.OP_bar.repaint()
        
        self.Kc = Kc
        self.Ti = Ti
        self.Td = Td
        self.action = action
        #self.ui.label_Kc.setText(str(self.Kc))
        #self.ui.label_Ti.setText(str(self.Ti))
        #self.ui.label_Td.setText(str(self.Td))
        
        if PV < PVmin:
            PV = PVmin
        if PV > PVmax:
            PV = PVmax
        self.PV = PV
        self.PVprev = self.PV
        self.PVmin = PVmin
        self.PVmax = PVmax
        self.PV_bar = LevelBarWidget(Qt.blue, minval=self.PVmin, maxval=self.PVmax)
        self.ui.vert_LayoutPV.addWidget(self.PV_bar)
        self.SP_bar = LevelBarWidget(Qt.red, minval=self.PVmin, maxval=self.PVmax)
        self.ui.vert_LayoutSP.addWidget(self.SP_bar)
        self.ui.label_PVmin.setText(str(round(self.PVmin, 2)))
        self.ui.label_PVmax.setText(str(round(self.PVmax, 2)))
        
        self.SP = self.PV
        self.ui.lineEdit_SP.setText(str(round(self.SP, 2)))
        double_validator = QDoubleValidator()
        self.ui.lineEdit_SP.setValidator(double_validator)
        self.ui.lineEdit_SP.editingFinished.connect(self.change_SP)
        self.ui.label_SPmin.setText(str(round(self.PVmin, 2)))
        self.ui.label_SPmax.setText(str(round(self.PVmax, 2)))
        
        self.mode = mode
        self.ierror = 0
        self.pidform = 0
        
        self.tk = 0
        self.tk_plus_1 = self.Ts
        
        if self.mode == 0:
            self.ui.radioButton_manual.setChecked(True)
        else:
            self.ui.radioButton_auto.setChecked(True)
        self.set_control_mode()
        self.ui.radioButton_manual.toggled.connect(self.set_control_mode)
        
        PV_indic = (self.PV-PVmin)/(PVmax-PVmin)
        self.PV_bar.setValue(PV_indic)
        self.PV_bar.repaint()
        self.ui.label_PV.setText(str(round(self.PV, 2)))
        self.ui.label_PVvalue.setText(str(round(self.PV, 2)))
        
        SP_indic = PV_indic
        self.SP_bar.setValue(SP_indic)
        self.SP_bar.repaint()
        self.ui.label_SPvalue.setText(str(round(self.SP, 2)))
        
        self.ui.label_57.setText(unit_str)
        self.ui.label_58.setText(unit_str)
        
        nsize = int(simtime*3600/self.Ts)
        
        self.data_logger = DataLogger(self.desc, self.PVmin, self.PVmax, self.unit_str, nsize)
        self.ui.pushButton_Datalogger.clicked.connect(self.data_logger.show_window)
        
        self.ui.pushButton_changePID.clicked.connect(self.open_pid_input_form)

        self.isSlave = isSlave
        if not self.isSlave:
            self.ui.widget_SPRef.setEnabled(False)
        else:
            self.ui.radioButton_Local.toggled.connect(self.activate_SP_textbox)
            self.ui.widget_SPRef.setEnabled(True)
            self.master_loop = masterLoopObj
            self.ui.radioButton_Remote.setChecked(True)
            #self.activate_SP_textbox()

    def activate_SP_textbox(self):
        if self.ui.radioButton_Local.isChecked():
            self.ui.lineEdit_SP.setEnabled(True)
            self.ui.lineEdit_SP.editingFinished.connect(self.change_SP)
        else:
            self.ui.lineEdit_SP.editingFinished.disconnect()
            self.ui.lineEdit_SP.setEnabled(False)
        
    def open_pid_input_form(self):
        pid_input_dlg = PIDInputPanel(self.desc, self.Kc, self.Ti, self.Td, action=self.action, form=self.pidform)
        if pid_input_dlg.exec_():
            self.Kc = float(pid_input_dlg.ui.lineEdit_Kc_new.text())
            self.Ti = float(pid_input_dlg.ui.lineEdit_Ti_new.text())
            self.Td = float(pid_input_dlg.ui.lineEdit_Td_new.text())
            self.pidform = pid_input_dlg.ui.comboBox_Form.currentIndex()
            
            #self.ui.label_Kc.setText(str(self.Kc))
            #self.ui.label_Ti.setText(str(self.Ti))
            #self.ui.label_Td.setText(str(self.Td))
        
    def change_OP(self):
        self.ui.lineEdit_OP.editingFinished.disconnect()
        OP = float(self.ui.lineEdit_OP.text())
        
        self.set_OP(OP)
        
        self.ui.lineEdit_OP.clearFocus()
        self.ui.lineEdit_OP.editingFinished.connect(self.change_OP)
        
    def set_OP(self, OP):
        if OP > self.OPmax or OP < self.OPmin:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Variable beyond range")
            msg.setText("The entered value is beyond the instrumentation range")
            msg.setStandardButtons(QMessageBox.Ok)

            msg.exec_()
        else:
            self.OP = OP
            self.OP_bar.setValue(self.OP/100)
            self.OP_bar.repaint()
            self.ui.label_OPvalue.setText(str(round(self.OP, 2)))
        self.ui.lineEdit_OP.setText(str(round(self.OP, 2)))
        
    def change_SP(self):
        self.ui.lineEdit_SP.editingFinished.disconnect()
        SP = float(self.ui.lineEdit_SP.text())
        
        self.set_SP(SP)        
        
        self.ui.lineEdit_SP.clearFocus()
        self.ui.lineEdit_SP.editingFinished.connect(self.change_SP)
        
    def set_SP(self, SP):
        if SP > self.PVmax or SP < self.PVmin:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Variable beyond range")
            msg.setText("The entered value is beyond the instrumentation range")
            msg.setStandardButtons(QMessageBox.Ok)

            msg.exec_()
        else:
            self.SP = SP
            SP_indic = (self.SP-self.PVmin)/(self.PVmax-self.PVmin)
            self.SP_bar.setValue(SP_indic)
            self.SP_bar.repaint()
            self.ui.label_SPvalue.setText(str(round(self.SP, 2)))
        self.ui.lineEdit_SP.setText(str(round(self.SP, 2)))
        
    def set_control_mode(self, checked=False):
        if self.ui.radioButton_manual.isChecked():
            self.mode = 0
            self.ui.lineEdit_OP.setEnabled(True)
            self.ui.lineEdit_OP.editingFinished.connect(self.change_OP)
        else:
            self.ui.lineEdit_OP.editingFinished.disconnect()
            if self.ui.radioButton_Local.isChecked():
                # bumpless transfer
                self.ui.lineEdit_SP.setText(str(round(self.PV, 2)))
                self.change_SP()
                self.OPbias = self.OP
            
            self.mode = 1
            self.ierror = 0
            
            self.ui.lineEdit_OP.setEnabled(False)
        
    def update(self, time, value):
        self.PVprevminus1 = self.PVprev
        self.PVprev = self.PV
        self.PV = value

        if self.ui.radioButton_Remote.isChecked() and self.isSlave and self.master_loop is not None:
            self.SP = self.master_loop.get_OP()
            
        if self.mode == 1:
            error = (self.SP-self.PV)/(self.PVmax-self.PVmin)*(self.OPmax-self.OPmin)
            if self.pidform == 0: # positional form
                dpv = (self.PV-self.PVprev)/(self.PVmax-self.PVmin)*(self.OPmax-self.OPmin)
                if self.Ti != 0.0:
                    self.ierror += error
                    self.OP = self.OPbias + self.action*self.Kc*(error + 
                                                                 self.Ts/self.Ti*self.ierror - 
                                                                 self.Td/self.Ts*dpv)
                else:
                    self.OP = self.OPbias + self.action*self.Kc*(error -
                                                                 self.Td/self.Ts*dpv)
            else: # velocity form
                errorprev = (self.SP-self.PVprev)/(self.PVmax-self.PVmin)*(self.OPmax-self.OPmin)
                pv = self.PV/(self.PVmax-self.PVmin)*(self.OPmax-self.OPmin)
                pvprev = self.PVprev/(self.PVmax-self.PVmin)*(self.OPmax-self.OPmin)
                pvprevminus1 = self.PVprevminus1/(self.PVmax-self.PVmin)*(self.OPmax-self.OPmin)
                if self.Ti != 0.0:
                    delOP = self.action*self.Kc*(error-errorprev + 
                                                 self.Ts/self.Ti*error - 
                                                 self.Td/self.Ts*(pv-2*pvprev+pvprevminus1))
                else:
                    delOP = self.action*self.Kc*(error-errorprev - 
                                                 self.Td/self.Ts*(pv-2*pvprev+pvprevminus1))
                self.OP += delOP
            
            if self.OP > self.OPmax:
                self.OP = self.OPmax
            if self.OP < self.OPmin:
                self.OP = self.OPmin
            
        self.tk = time
        self.tk_plus_1 = self.tk + self.Ts

        self.data_logger.update_chart_record(self.tk, self.SP, self.PV, self.OP)

    def update_GUI(self):
        self.ui.label_PV.setText(str(round(self.PV, 2)))
        self.ui.label_PVvalue.setText(str(round(self.PV, 2)))
        
        PV_indic = (self.PV-self.PVmin)/(self.PVmax-self.PVmin)
        self.PV_bar.setValue(PV_indic)
        self.PV_bar.repaint()

        if self.mode == 1:
            self.ui.lineEdit_OP.setText(str(round(self.OP, 2)))
        self.ui.label_OPvalue.setText(str(round(self.OP, 2)))
        self.OP_bar.setValue(self.OP/100)
        self.OP_bar.repaint()

        if self.ui.radioButton_Remote.isChecked() and self.isSlave and self.master_loop is not None:
            self.ui.lineEdit_SP.setText(str(round(self.SP, 2)))
            self.ui.label_SPvalue.setText(str(round(self.SP, 2)))
            SP_indic = (self.SP-self.PVmin)/(self.PVmax-self.PVmin)
            self.SP_bar.setValue(SP_indic)
            self.SP_bar.repaint()
        
        self.data_logger.update_chart_GUI()
                    
    def get_OP(self):
        return self.OP/100*(self.MVmax-self.MVmin) + self.MVmin
    
    def get_MV(self):
        return self.OP/100*(self.MVmax-self.MVmin) + self.MVmin
    
    def show_window(self):
        if not self.isVisible():
            self.show()
        else:
            self.activateWindow() 
            
#    def showEvent(self, event):
#        self.re
        
        


                
                
        
        
        
        