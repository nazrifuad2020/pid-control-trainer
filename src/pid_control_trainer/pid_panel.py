from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

# from PySide2.QtUiTools import QUiLoader
# from PySide2.QtCore import Qt
# from PySide2.QtWidgets import QVBoxLayout, QWidget, QTableWidgetItem, QListWidgetItem, QDialog, QMessageBox
# from PySide2.QtGui import QDoubleValidator

from pathlib import Path

pen_color_list = ['b', 'g', 'y', 'c', 'm']

UI_PATH = Path(__file__).parent / 'pid_panel.ui'
Ui_Window, QtBaseClass = uic.loadUiType(str(UI_PATH))
class PIDInputPanel(QDialog):
    def __init__(self, title_str, Kc, Ti, Td, action=1, form=0):
        super(PIDInputPanel, self).__init__()
        
        self.ui = Ui_Window()
        self.ui.setupUi(self)

        # loader = QUiLoader()
        # self.ui = loader.load('PID_input_form_2.ui', self)
        
        # self.width_ui = self.ui.width()
        # self.height_ui = self.ui.height()

        #self.setGeometry(0, 0, self.ui.size().width(), self.ui.size().height())
        # layout = QVBoxLayout()
        # layout.addWidget(self.ui)
        # self.setLayout(layout)
        # self.resize(self.width_ui, self.height_ui)
        # self.setWindowTitle("PID input: " + title_str)
        
        self.ui.label_Kc_old.setText(str(Kc))
        self.ui.label_Ti_old.setText(str(Ti))
        self.ui.label_Td_old.setText(str(Td))
        
        self.ui.lineEdit_Kc_new.setText(str(Kc))
        self.ui.lineEdit_Ti_new.setText(str(Ti))
        self.ui.lineEdit_Td_new.setText(str(Td))

        if action == 1:
            self.ui.label_Action.setText("Reverse")
        elif action == -1:
            self.ui.label_Action.setText("Direct")
            
        if form == 0:
            self.ui.comboBox_Form.setCurrentIndex(0)
            self.ui.label_16.setText('None')
        else:
            self.ui.comboBox_Form.setCurrentIndex(1)
            self.ui.label_16.setText('Inherent')

        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        
        self.ui.comboBox_Form.currentIndexChanged[int].connect(self.update_form_label)
        
    def update_form_label(self, index):
        if index == 0:
            self.ui.label_16.setText('None')
        else:
            self.ui.label_16.setText('Inherent')