#!/usr/bin/python

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject
import widget
import sys
import time
import fm
import temperature
import settings
from threading import Event, Thread

path_settings = "settings.ini" # Файл настроек

# Communication temperatureThread with UiApp
class Communicate(QObject):
    signalT = pyqtSignal(str)
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
    
    def freq(self):
        f = self.doubleSpinBoxFreq.value()
        self.labelStatus.setText("freq: " + str(f) +  "MHz")
        settings.update_setting(path_settings, 'Settings', "freq", str(f))
        
    
    def power(self):
        p = self.doubleSpinBoxPow.value()
        self.labelStatus.setText("power: " + str(p)+  "%")
        settings.update_setting(path_settings, 'Settings', "power", str(p))
    
    def rds(self):
        text = self.lineEditRds.text()
        self.labelStatus.setText("rds: " + text)
        settings.update_setting(path_settings, 'Settings', "rds", text)
        
    
    def terminal(self):
        text = text = self.lineEditTerminal.text()
        self.labelStatus.setText("terminal: " + text)
    
    def hello(self, text):
        self.labelStatus.setText(text)
        
    def temperature(self, text):
        self.labelTemp.setText(text)
        
# TEMPERATURE THREAD
class temperatureThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event
        self.cnt = 0

    def run(self):
        while not self.stopped.wait(5):
            self.cnt+=1
            commun.signalT.emit(str(self.cnt))
temperatureTstop = Event()
temperatureT = temperatureThread(temperatureTstop)

###
def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = UiApp()  # Создаём объект 
    window.show()  # Показываем окно 
    temperatureT.start()
    app.exec_()  # и запускаем приложение
    temperatureTstop.set()
    sys.exit()

    
if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()