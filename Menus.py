import framebuf
from led import Led
from machine import Pin, UART, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import time
from fifo import Fifo


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
            self.fifo.put(1)
        else:
            self.fifo.put(-1)


def menu_cursor(place):
    oled.fill_rect(0, 0, 10, 70, 0)
    oled.text(">", 0, place, 1)

def mesure_cursor(place):
    oled.fill_rect(0, 0, 10, 20, 0)
    oled.text(">", 0, place, 1)

def main_menu():
    #menu UI
    oled.fill(0)
    oled.text("HRM 3000", 35, 0, 1)
    oled.text("Mesure", 10, 20, 1)
    oled.text("Analasys", 10, 30, 1)
    oled.text("History", 10, 40, 1)
    oled.text("Kubios", 10, 50, 1)
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
                mesure_menu()
                mainMenu = False
            if place == 1:
                analysis_menu()
                mainMenu = False
            if place == 2:
                history_menu()
                mainMenu = False
            if place == 3:
                kubios_menu()
                mainMenu = False


def mesure_menu():
    oled.fill(0)
    oled.text("Start/Stop", 10, 0, 1)
    oled.text("Back", 10, 10, 1)
    oled.text("BPM: ", 0, 20, 1) #call method that shows BPM and updates every 5 seconds
    oled.fill_rect(0, 30, 128, 64, 1) #place holder for Live PPG
    mesure_cursor(0)
    oled.show()
    place = 0
    mesureMenu = True
    while mesureMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 1:
                place = 1
                mesure_cursor(10)
            
            elif place <= 0:
                place = 0
                mesure_cursor(0)
            
        oled.show()
        if button.onepress():
            if place == 1:
                main_menu()
                mesureMenu = False
            if place == 0:
                #call method that starts mesuring when pressed and stops when pressed again
                pass

def analysis_menu():
    pass
    
def history_menu():
    pass


#defining stuff
rot = Encoder(10, 11)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
button = Button(12, Pin.IN, Pin.PULL_UP)

mesure_menu()