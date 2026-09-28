# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 11:31:13 2019

@author: nazri
"""
import numpy as np

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, Qt, QObject, QEvent
from PyQt5.QtWidgets import QTreeWidgetItem, QMessageBox, QMainWindow, QApplication
from PyQt5.QtGui import QBrush, QPixmap

from .two_phase_sep import TWO_PHASE_SEP

from . import Level_Widget_Module

from .controller_panel import Controller_Panel

import sys, time, threading

from pathlib import Path


def clickable(widget):
    class Filter(QObject):
        clicked = pyqtSignal()
        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        # The developer can opt for .emit(obj) to get the object within the slot.
                        return True
            return False

    filter_ = Filter(widget)
    widget.installEventFilter(filter_)
    return filter_.clicked

UI_PATH = Path(__file__).parent / 'ProcSimLab_Phase_Separator.ui'
Ui_Window, QtBaseClass = uic.loadUiType(str(UI_PATH))

class My_Two_PhaseSep_Window(QMainWindow):
    update_gui_pysig = pyqtSignal()
    critical_stop_pysig = pyqtSignal(str)

    SIM_IS_RUNNING = False
    SIM_IS_PAUSED = False

    def __init__(self):
        super(My_Two_PhaseSep_Window, self).__init__()
        
        self.ui = Ui_Window()
        self.ui.setupUi(self)

        PIX_PATH = Path(__file__).parent / 'two_phase_separator.png'
        pixmap = QPixmap(str(PIX_PATH))
        self.ui.label_34.setPixmap(pixmap)

        self.level_ind = Level_Widget_Module.LevelWidget(Qt.magenta)
        self.ui.verticalLayout_level.addWidget(self.level_ind) 

        self.update_gui_pysig.connect(self.update_gui)
        self.critical_stop_pysig[str].connect(self.messagebox_critical_show)
        
        self.ui.pushButton_Start_Sim.clicked.connect(self.start_sim_session)
        self.ui.pushButton_Pause_Sim.clicked.connect(self.pause_sim)
        self.ui.pushButton_Stop_Sim.clicked.connect(self.stop_sim) 

        self.ui.time_accel_slider.sliderMoved[int].connect(self.set_time_accel_label)

        self.ui.checkBox_inletDisturbance.toggled[bool].connect(self.activate_inlet_disturbance)

        self.ui.treeWidget_Loop.expandAll()

        self.ui.treeWidget_Loop.resizeColumnToContents(0)
        self.ui.treeWidget_Loop.resizeColumnToContents(1)
        self.ui.treeWidget_Loop.resizeColumnToContents(2)
        self.ui.treeWidget_Loop.resizeColumnToContents(3)
        self.ui.treeWidget_Loop.resizeColumnToContents(4)

    def set_time_accel_label(self, int_slider):
        self.ui.time_accel_label.setText(str(int_slider)+'x')

    def activate_inlet_disturbance(self, checked):
        if checked:
            self.Tinlet = 95
            self.two_phase_sep.set_inlet_disturbance(T=self.Tinlet)
        else:
            self.two_phase_sep.unset_inlet_disturbance()

    def update_gui(self):
        self.ui.label_PIC100_PV.setText("PV: " + str(round(self.P, 2)) + " barg")
        PIC100_SP = self.PIC100.SP
        self.ui.label_PIC100_SP.setText("SP: " + str(round(PIC100_SP, 2)) + " barg")
        PIC100_OP = self.PIC100.OP
        self.ui.label_PCV100_OP.setText("OP: " + str(round(PIC100_OP, 2)) + " %")

        self.ui.label_LIC100_PV.setText("PV: " + str(round(self.hliq, 2)) + " m")
        LIC100_SP = self.LIC100.SP
        self.ui.label_LIC100_SP.setText("SP: " + str(round(LIC100_SP, 2)) + " m")
        LIC100_OP = self.LIC100.OP
        self.ui.label_LCV100_OP.setText("OP: " + str(round(LIC100_OP, 2)) + " %")
        
        self.LIC100.update_GUI()
        self.PIC100.update_GUI()

        h_high = self.two_phase_sep.hlvl_high
        h_low = self.two_phase_sep.hlvl_low
        h_pct = (self.hliq-h_low)/(h_high-h_low)*100
        self.level_ind.setValue(h_pct)
        self.level_ind.repaint() 

        level_loop = self.ui.treeWidget_Loop.topLevelItem(0)
        LIC100_item = level_loop.child(0)
        if self.LIC100.mode == 0:
            LIC100_item.setText(1, "Manual")
            back_brush = QBrush(Qt.red)
            fore_brush = QBrush(Qt.white)
            self.ui.label_LIC100_Mode.setText("Mode: Manual")
        else:
            LIC100_item.setText(1, "Auto")
            back_brush = QBrush(Qt.darkGreen)
            fore_brush = QBrush(Qt.yellow)
            self.ui.label_LIC100_Mode.setText("Mode: Auto")
        LIC100_item.setBackground(1, back_brush)
        LIC100_item.setForeground(1, fore_brush)
        LIC100_item.setText(2, str(round(LIC100_SP, 2)))
        LIC100_item.setText(3, str(round(self.hliq, 2)))
        LIC100_item.setText(4, str(round(LIC100_OP, 2)))
        
        pressure_loop = self.ui.treeWidget_Loop.topLevelItem(1)
        PIC100_item = pressure_loop.child(0)
        if self.PIC100.mode == 0:
            PIC100_item.setText(1, "Manual")
            back_brush = QBrush(Qt.red)
            fore_brush = QBrush(Qt.white)
            self.ui.label_PIC100_Mode.setText("Mode: Manual")
        else:
            PIC100_item.setText(1, "Auto")
            back_brush = QBrush(Qt.darkGreen)
            fore_brush = QBrush(Qt.yellow)
            self.ui.label_PIC100_Mode.setText("Mode: Auto")
        PIC100_item.setBackground(1, back_brush)
        PIC100_item.setForeground(1, fore_brush)
        PIC100_item.setText(2, str(round(PIC100_SP, 2)))
        PIC100_item.setText(3, str(round(self.P, 2)))
        PIC100_item.setText(4, str(round(PIC100_OP, 2)))

        self.ui.treeWidget_Loop.resizeColumnToContents(1)
        self.ui.treeWidget_Loop.resizeColumnToContents(2)
        self.ui.treeWidget_Loop.resizeColumnToContents(3)
        self.ui.treeWidget_Loop.resizeColumnToContents(4)
        
        self.ui.label_C3_in.setText(str(round(self.two_phase_sep.zC3*100, 2)))
        self.ui.label_C4_in.setText(str(round(self.two_phase_sep.zC4*100, 2)))
        self.ui.label_C5_in.setText(str(round(self.two_phase_sep.zC5*100, 2)))
        self.ui.label_C6_in.setText(str(round(self.two_phase_sep.zC6*100, 2)))
        self.ui.label_flowIn.setText(str(round(self.two_phase_sep.F_in, 2)))
        
        self.ui.label_C3_top.setText(str(round(self.two_phase_sep.yC3*100, 2)))
        self.ui.label_C4_top.setText(str(round(self.two_phase_sep.yC4*100, 2)))
        self.ui.label_C5_top.setText(str(round(self.two_phase_sep.yC5*100, 2)))
        self.ui.label_C6_top.setText(str(round(self.two_phase_sep.yC6*100, 2)))
        self.ui.label_flowTop.setText(str(round(self.two_phase_sep.Fvap_out, 2)))
        
        self.ui.label_C3_bot.setText(str(round(self.two_phase_sep.xC3*100, 2)))
        self.ui.label_C4_bot.setText(str(round(self.two_phase_sep.xC4*100, 2)))
        self.ui.label_C5_bot.setText(str(round(self.two_phase_sep.xC5*100, 2)))
        self.ui.label_C6_bot.setText(str(round(self.two_phase_sep.xC6*100, 2)))
        self.ui.label_flowBot.setText(str(round(self.two_phase_sep.Fliq_out, 2)))

    def messagebox_critical_show(self, pv_str):
        self.stop_sim()

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Process limit breached")
        msg.setText("Uh-oh... Limit breached for " + pv_str + ". Simulation is stopped.")
        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec_()

    def update_timer_display(self):
        if self.world_time%1 == 0:
            if self.world_time >= 60:
                seconds = self.world_time%60
                if np.floor(self.world_time/60) >= 60:
                    minutes = np.floor(self.world_time/60)%60
                    hours = np.floor(self.world_time/60/60)
                else:
                    minutes = np.floor(self.world_time/60)
                    hours = 0
            else:
                seconds = self.world_time
                minutes = 0
                hours = 0

            self.ui.lcd_sec.display(seconds)
            self.ui.lcd_min.display(minutes)
            self.ui.lcd_hr.display(hours)   
        
    def start_sim_session(self):
        self.two_phase_sep = TWO_PHASE_SEP()
        
        hliq = self.two_phase_sep.hliq
        self.LIC100 = Controller_Panel("LIC100", hliq, 1.25, 3.75, "m", "LCV100", 0.5, MVmin=0.0, MVmax=1.0, mode=1, Kc=2.0, Ti=15.0)

        Pgauge = self.two_phase_sep.get_Pgauge()
        self.PIC100 = Controller_Panel("PIC100", Pgauge, 0, 10, "barg", "PCV100", 0.5, MVmin=0.0, MVmax=1.0, mode=1, Kc=100.0, Ti=70.0)

        self.ui.time_accel_slider.setValue(1)
        self.set_time_accel_label(1)

        self.SIM_IS_RUNNING = True
        self.SIM_IS_PAUSED = False

        self.run_sim_thread = threading.Thread(target=self.sim_looping)
        self.world_time = 0.0
        self.run_sim_thread.start()
        
        self.ui.pushButton_Pause_Sim.setChecked(False)
        self.ui.pushButton_Pause_Sim.setEnabled(True)
        self.ui.pushButton_Pause_Sim.setText("Pause")
        self.ui.pushButton_Start_Sim.setEnabled(False)
        self.ui.pushButton_Stop_Sim.setEnabled(True)
        self.ui.pushButton_Stop_Sim.setChecked(False)

        self.ui.checkBox_inletDisturbance.setChecked(False)

        clickable(self.ui.label_PIC100_clicked).connect(self.PIC100.show_window)
        clickable(self.ui.label_LIC100_clicked).connect(self.LIC100.show_window)

        self.ui.treeWidget_Loop.itemDoubleClicked[QTreeWidgetItem, int].connect(self.open_control_panel)

    def open_control_panel(self, select_item, col):
        if select_item.text(0) == "LIC100":
            self.LIC100.show_window()
        if select_item.text(0) == "PIC100":
            self.PIC100.show_window()

    def pause_sim(self):
        if self.SIM_IS_RUNNING and not self.SIM_IS_PAUSED:
            self.SIM_IS_PAUSED = True
            self.run_sim_thread.join()
            while self.run_sim_thread.is_alive():
                pass
            self.ui.pushButton_Pause_Sim.setText("Unpause")
        elif self.SIM_IS_PAUSED:
            self.SIM_IS_PAUSED = False
            self.run_sim_thread = threading.Thread(target=self.sim_looping)
            self.run_sim_thread.start()
            self.ui.pushButton_Pause_Sim.setText("Pause")
        return

    def stop_sim(self):
        self.SIM_IS_RUNNING = False
        self.SIM_IS_PAUSED = False
        self.run_sim_thread.join()
        while self.run_sim_thread.is_alive():
            pass
        self.ui.pushButton_Start_Sim.setChecked(False)
        self.ui.pushButton_Start_Sim.setEnabled(True)
        self.ui.pushButton_Stop_Sim.setEnabled(False)
        self.ui.pushButton_Stop_Sim.setChecked(True)
        
    def sim_looping(self):
        while self.SIM_IS_RUNNING and not self.SIM_IS_PAUSED:
            self.update_timer_display()
            
            # read level
            noise = np.random.normal(0, 0.1/2)/100
            self.hliq = self.two_phase_sep.hliq*(1-noise)
            self.LIC100.update(self.world_time, self.hliq)
            LCV100 = self.LIC100.get_OP()
            self.two_phase_sep.set_controlvalve_liq_sig(LCV100)

            # read Pressure
            noise = np.random.normal(0, 0.1/2)/100
            Pgauge = self.two_phase_sep.get_Pgauge()
            self.P = Pgauge*(1-noise)
            self.PIC100.update(self.world_time, self.P)
            PCV100 = self.PIC100.get_OP()
            self.two_phase_sep.set_controlvalve_vap_sig(PCV100)

            self.update_gui_pysig.emit()

            # check liq level conditions
            if self.hliq > self.two_phase_sep.hlvl_high or self.hliq < self.two_phase_sep.hlvl_low:
                self.critical_stop_pysig.emit("Liquid Level")

            if self.P > self.two_phase_sep.Pmaxg:
                self.critical_stop_pysig.emit("Vessel Pressure")

            self.two_phase_sep.step()

            self.world_time += 1
            time_accel_factor = self.ui.time_accel_slider.value()

            time.sleep(1.0/time_accel_factor)

    def closeEvent(self, event):
        if self.SIM_IS_RUNNING:
            self.SIM_IS_RUNNING = False 
            self.run_sim_thread.join()
        app = QApplication.instance()
        app.closeAllWindows()


def main():
    app = QApplication(sys.argv)
    sep_win = My_Two_PhaseSep_Window()
    sep_win.show()
    
    # msg = QMessageBox()
    # msg.setIcon(QMessageBox.Information)
    # msg.setWindowTitle("Information")
    # msg.setText("This software is strictly for evaluation purpose only")
    # msg.setStandardButtons(QMessageBox.Ok)
    
    # msg.exec_()
    
    sys.exit(app.exec_())
            
        
if __name__ == '__main__':
    main()
