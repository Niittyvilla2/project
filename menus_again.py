import framebuf
from led import Led
from machine import Pin, UART, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import time
from fifo import Fifo
from PPG import PPG
from hr import HR
from reader import Reader
from piotimer import Piotimer

class Button(Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.press = 0
        self.release = 0
        self.state = False
        self.down = False
        
    
    def pressed(self):
        if self.value() == 0:
            self.release = 0
            self.press += 1
            if self.press >= 3:
                self.press = 3
                self.state = True
                
        else:
            self.press = 0
            self.release += 1
            if self.release >=3:
                self.release = 3
                self.state = False
            
        return self.state
    
    def onepress(self):
        if self.down:
            if not self.pressed():
                self.down = False
                
        else:
            if self.pressed():
                self.down = True
                return True
        
        return False
    
    
    
class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, mode = Pin.IN)
        self.b = Pin(rot_b, mode = Pin.IN)
        self.fifo = Fifo(100, typecode = "i")
        self.a.irq(handler = self.handler, trigger = Pin.IRQ_RISING, hard = True)
        
    def handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)


def menu_cursor(place):
    oled.fill_rect(0, 0, 10, 64, 0)
    oled.text(">", 0, place, 1)
    
def hrv_cursor(place):
    oled.fill_rect(0, 56, 10, 64, 0)
    oled.fill_rect(60, 56, 10, 64, 0)
    oled.text(">", place, 56, 1)

def kubios_cursor(place):
    oled.fill_rect(0, 56, 10, 64, 0)
    oled.fill_rect(60, 56, 10, 64, 0)
    oled.text(">", place, 56, 1)


    
def main_menu():
    #menu UI
    oled.fill(0)
    oled.text("HRM 3000", 35, 0, 1)
    oled.text("Mesure BPM", 10, 20, 1)
    oled.text("HRV analysis", 10, 30, 1)
    oled.text("Kubios", 10, 40, 1)
    oled.text("History", 10, 50, 1)
    menu_cursor(20)
    oled.show()
    
    place = 0
    mainMenu = True
    while mainMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 3:
                place = 3
                menu_cursor(50)
            
            elif place <= 0:
                place = 0
                menu_cursor(20)
            
            elif place == 2:
                menu_cursor(40)
                
            else:
                menu_cursor(30)
        oled.show()
        if button.onepress():
            if place == 0:
                bpm_start()
                mainMenu = False
            if place == 1:
                hrv_start()
                mainMenu = False
            if place == 2:
                kubios_start()
                mainMenu = False
            if place == 3:
                history_menu()
                mainMenu = False

def bpm_start():
    oled.fill(0)
    oled.text("Start/Stop", 10, 54, 1)
    oled.text("Back", 10, 44, 1)
    oled.text("BPM: ", 10, 34, 1) #update bpm every 5 seconds
    #oled.fill_rect(0, 0, 127, 30, 1) #Import PPG graph and display here
    menu_cursor(44)
    oled.show()
    bpmStart = True
    place = 0
    while bpmStart == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place <= 0:
                place = 0
                menu_cursor(54)
            elif place >= 1:
                place = 1
                menu_cursor(44)
        oled.show()
        if button.onepress():
            if place == 0:
                collect = True
                reader.start()
                hrv_data = []
                while collect:
                    hrv_data.append(reader.read_next())
                    if len(hrv_data) > 128*10+1:
                        hrv_data.pop(0)
                    if len(hrv_data) > 128*10-1:
                        ppg.plot(hrv_data)
                    oled.show()
                    if button.onepress():
                        collect = False
            if place == 1:
                main_menu()
                bpmStart = False
                
    

def hrv_start():
    oled.fill(0)
    oled.text("Start meruring", 0, 0, 1)
    oled.text("by placing your", 0, 10, 1)
    oled.text("finger on the", 0, 20, 1)
    oled.text("sensor and press", 0, 30, 1)
    oled.text("start.", 0, 40 , 1)
    oled.text("Start", 10, 56, 1)
    oled.text("Back", 70, 56, 1)
    hrv_cursor(0)
    oled.show()
    hrvStart = True
    place = 0
    while hrvStart == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place <= 0:
                place = 0
                hrv_cursor(0)
            elif place >= 1:
                place = 1
                hrv_cursor(60)
        oled.show()
        if button.onepress():
            if place == 1:
                main_menu()
                hrvStart = False
            if place == 0:
                hrv_mesuring()
                hrvStart = False

def hrv_mesuring():
    oled.fill(0)
    oled.text("Mesuring. Press", 0, 0, 1)
    oled.text("the button to", 0, 10, 1)
    oled.text("stop early.", 0, 20, 1)
    oled.show()
    #Progressbar?
    #gather data for 30s then analyze and save the gathered data here or in diffrent method, also save the timestamp
    #show "Analysis compleate" for 5 or so seconds after the previous step is complete before moving to hrv_results
    hrvMesure = True
    while hrvMesure == True:
        if button.onepress():
            #stop mesurment and dont save it
            hrv_start()
            hrvMesure = False
            
def hrv_results():
    oled.fill(0)
    #display mean PPI, mean HR, RMSSD and SDNN
    oled.text("Mean PPI", 0, 0, 1)
    oled.text("Mean HR", 0, 10, 1)
    oled.text("RMSDD", 0, 20, 1)
    oled.text("SDNN", 0, 30, 1)
    oled.text("Back", 10, 56, 1)
    hrv_cursor(0)
    oled.show()
    hrvResults = True
    while hrvResults == True:
        if button.onepress():
            hrv_start()
            hrvResults = False
    
def kubios_start():
    oled.fill(0)
    oled.text("Start meruring", 0, 0, 1)
    oled.text("by placing your", 0, 10, 1)
    oled.text("finger on the", 0, 20, 1)
    oled.text("sensor and press", 0, 30, 1)
    oled.text("start.", 0, 40 , 1)
    oled.text("Start", 10, 56, 1)
    oled.text("Back", 70, 56, 1)
    kubios_cursor(0)
    oled.show()
    kubiosStart = True
    place = 0
    while kubiosStart == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place +=i
            if place <= 0:
                place = 0
                kubios_cursor(0)
            elif place >= 1:
                place = 0
                kubios_cursor(60)
        oled.show()
        if button.onepress():
            if place == 0:
                main_menu()
                kubiosStart = False
            if place == 1:
                kubios_mesuring()
                kubiosStart = False
                
def kubios_mesuring():
    oled.fill(0)
    oled.text("Mesuring. Press", 0, 0, 1)
    oled.text("the button to", 0, 10, 1)
    oled.text("stop early.", 0, 20, 1)
    oled.show()
    #Progressbar?
    #gather data for 30s
    #send and recive data from Kubios, save mesurment with timestamp
    #save data
    #move to kubios_results
    kubiosMesure = True
    while kubiosMesure == True:
        if button.onepress():
            #stop mesurment and dont save it
            kubios_start()
            kubiosMesure = False
    
def kubios_results():
    oled.fill(0)
    #display kubios data
    oled.text("Mean PPI", 0, 0, 1)
    oled.text("Mean HR", 0, 9, 1)
    oled.text("RMSDD", 0, 19, 1)
    oled.text("SDNN", 0, 28, 1)
    oled.text("SNS", 0, 37, 1)
    oled.text("PNS", 0, 46, 1)
    oled.text("Back", 10, 56, 1)
    kubios_cursor(0)
    oled.show()
    kubiosResults = True
    while kubiosResults == True:
        if button.onepress():
            kubios_start()
            kubiosResults = False

def history_menu():
    oled.fill(0)
    oled.text("Back", 10, 0, 1)
    y = 0
    alloy = 0

    if len(placeholder) < 5:
        for a in range(len(placeholder)):
            y +=10
            alloy+=1
            oled.text("Mesurment " + str(alloy), 10, y, 1)
    elif len(placeholder) >= 5:
        for a in range(5):
            y +=10
            alloy+=1
            oled.text("Mesurment " + str(alloy), 10, y, 1)

    menu_cursor(0)
    oled.show()
    historyMenu = True
    place = 0
    while historyMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place +=i
            if place <= 0:
                place = 0
                menu_cursor(0)
                
            elif place == 1 and alloy > 0:
                menu_cursor(10)

            elif place == 2 and alloy >1:
                menu_cursor(20)

            elif place == 3 and alloy >2:
                menu_cursor(30)
                
            elif place == 4 and alloy >3:
                menu_cursor(40)
                
            elif place == 5 and alloy >4:
                menu_cursor(50)
                
            if place >= alloy:
                place = alloy
        oled.show()
        if button.onepress():
            if place == 0:
                main_menu()
                historyMenu = False
            if place == 1:
                history_show(1)
                historyMenu = False
            if place == 2:
                history_show(2)
                historyMenu = False
            if place == 3:
                history_show(3)
                historyMenu = False
            if place == 4:
                history_show(4)
                historyMenu = False
            if place == 5:
                history_show(5)
                historyMenu = False

def history_show(alloy):

    oled.fill(0)
    oled.text("Back", 0, 0, 1)
    oled.text(str(placeholder[alloy-1]), 0, 10) #show the content of chosen alloy
    oled.show()
    historyShow = True
    while historyShow == True:
        if button.onepress():
            history_menu()
            historyShow = False
    
            
#defining stuff
placeholder = [5, 2]
rot = Encoder(10, 11)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
reader = Reader(27)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
ppg = PPG(oled, 0, 0, 127, 30, 10)
button = Button(12, Pin.IN, Pin.PULL_UP)

main_menu()