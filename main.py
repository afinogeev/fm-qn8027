#!/usr/bin/python
#-*- coding: utf-8 -*-

#FM 

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject
import widget
import sys
import time
from ds18b20 import DS18B20
import settings
from threading import Event, Thread
import qn8027

path_settings = "settings.ini" # Файл настроек

# Communication temperatureThread with UiApp
class Communicate(QObject):
    signalT = pyqtSignal(str)
    signalRds = pyqtSignal(str)
commun = Communicate()

## UI
class UiApp(QtWidgets.QWidget, widget.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self) 
        
        # INIT WIDGET
        self.doubleSpinBoxFreq.setValue(float(settings.get_setting(path_settings, 'Settings', 'freq')))
        self.doubleSpinBoxPow.setValue(float(settings.get_setting(path_settings, 'Settings', 'power')))
        self.lineEditRds.setText(settings.get_setting(path_settings, 'Settings', 'rds'))
        
        # SLOTS
        commun.signalT.connect(self.temperature)
        self.doubleSpinBoxFreq.valueChanged.connect(self.freq)
        self.doubleSpinBoxPow.valueChanged.connect(self.power)
        self.pushButtonRds.clicked.connect(self.rds)
        self.pushButtonTerminal.clicked.connect(self.terminal)
        
        # QN8027
        qn8027.init()
        self.freq()
        self.power()
        self.rds()
        
        #OVERHEAT
        self.overheat = False
    
    def freq(self):
        f = self.doubleSpinBoxFreq.value()
        qn8027.setFrequency(int(self.doubleSpinBoxFreq.value()*100))
        self.labelStatus.setText("freq: " + str(f) +  "MHz")
        settings.update_setting(path_settings, 'Settings', "freq", str(f))        
    
    def power(self):
        p = self.doubleSpinBoxPow.value()
        qn8027.setPower(self.doubleSpinBoxPow.value())
        self.labelStatus.setText("power: " + str(p)+  "%")
        settings.update_setting(path_settings, 'Settings', "power", str(p))
    
    def rds(self):
        text = self.lineEditRds.text()
        qn8027.setRDS(text)
        if(len(text)>8):
            text = text[0:8:1]
        else:
            text = text.center(8," ")
        commun.signalRds.emit(text)
        self.labelStatus.setText("rds: " + text)
        settings.update_setting(path_settings, 'Settings', "rds", text)
        
    
    def terminal(self):
        text = self.lineEditTerminal.text().split(",")
        if(len(text)==3):
            reg = int(text[0])
            mask = int(text[1])
            data = int(text[2])
            #print(reg)
            #print(mask)
            #print(data)
            qn8027.writeData(reg, mask, data)
        self.labelStatus.setText("Terminal: "+str(qn8027.readData(reg, 0xFF)))
        
    
    def hello(self, text):
        self.labelStatus.setText(text)
        
    def temperature(self, text):
        self.labelTemp.setText(text)
        if(float(text)>=70. and self.overheat==False):
            qn8027.setPower(0.)
            self.overheat = True
        if(float(text)<70. and self.overheat):
            qn8027.setPower(self.doubleSpinBoxPow.value())
            self.overheat = False
            
        
        
#TEMPERATURE THREAD
class temperatureThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event
        self.ds18b20 = DS18B20()

    def run(self):
        while not self.stopped.wait(5):
            commun.signalT.emit(str(self.ds18b20.tempC(0)))
temperatureTstop = Event()
temperatureT = temperatureThread(temperatureTstop)

#RDS THREAD
class rdsThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event
        self.text = ""
        commun.signalRds.connect(self.setText)

    def run(self):
        while not self.stopped.wait(9):
            qn8027.setRDS(self.text)
    def setText(self, textui):
        self.text = textui   
rdsTstop = Event()
rdsT = rdsThread(rdsTstop)

###
def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = UiApp()  # Создаём объект 
    window.show()  # Показываем окно 
    temperatureT.start()
    rdsT.start()
    app.exec_()  # и запускаем приложение
    temperatureTstop.set()
    rdsTstop.set()
    sys.exit()

    
if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
