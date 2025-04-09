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
    


def main_menu():
    oled.fill(0)
    oled.text("MAIN MENU", 30, 00, 1)
    oled.text("MENU 1", 0, 20, 1)
    oled.text("MENU 2", 0, 30, 1)
    oled.text("MENU 3", 0, 40, 1)
    cursor(20)
    oled.show()
    place = 0
    mainMenu = True
    while mainMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 2:
                place = 2
                cursor(40)
                oled.show()
            
            elif place <= 0:
                place = 0
                cursor(20)
                oled.show()
            
            else:
                cursor(30)
                oled.show()
        
        if button.onepress():
            if place == 0:
                menu1()
                mainMenu = False
            if place == 1:
                menu2()
                mainMenu = False
            if place == 2:
                menu3()
                mainMenu = False
            
 
 
def menu1():
    oled.fill(0)
    oled.text("MENU 1", 40, 00, 1)
    oled.text("Content1", 0, 20, 1)
    oled.text("Content2", 0, 30, 1)
    oled.text("Content3", 0, 40, 1)
    oled.text("Back", 0, 50, 1)
    cursor(20)
    oled.show()
    place = 0
    menu1 = True
    while menu1 == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 3:
                place = 3
                cursor(50)
                oled.show()
            
            elif place <= 0:
                place = 0
                cursor(20)
                oled.show()
            
            elif place == 1:
                cursor(30)
                oled.show()
                
            else:
                cursor(40)
                oled.show()
        
        if button.onepress():
            if place == 3:
                main_menu()
                menu1 = False
        
                
def menu2():
    oled.fill(0)
    oled.text("MENU 2", 40, 00, 1)
    oled.text("Content1", 0, 20, 1)
    oled.text("Content2", 0, 30, 1)
    oled.text("Content3", 0, 40, 1)
    oled.text("Back", 0, 50, 1)
    cursor(20)
    oled.show()
    place = 0
    menu2 = True
    while menu2 == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 3:
                place = 3
                cursor(50)
                oled.show()
            
            elif place <= 0:
                place = 0
                cursor(20)
                oled.show()
            
            elif place == 1:
                cursor(30)
                oled.show()
                
            else:
                cursor(40)
                oled.show()
        
        if button.onepress():
            if place == 3:
                main_menu()
                menu2 = False
    
def menu3():
    oled.fill(0)
    oled.text("MENU 3", 40, 00, 1)
    oled.text("Content1", 0, 20, 1)
    oled.text("Content2", 0, 30, 1)
    oled.text("Content3", 0, 40, 1)
    oled.text("Back", 0, 50, 1)
    cursor(20)
    oled.show()
    place = 0
    menu3 = True
    while menu3 == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 3:
                place = 3
                cursor(50)
                oled.show()
            
            elif place <= 0:
                place = 0
                cursor(20)
                oled.show()
            
            elif place == 1:
                cursor(30)
                oled.show()
                
            else:
                cursor(40)
                oled.show()
        
        if button.onepress():
            if place == 3:
                main_menu()
                menu3 = False
    
    
def cursor(place):
    oled.fill_rect(90, 20, 10, 50, 0)
    oled.text("<", 90, place, 1)
    

rot = Encoder(10, 11)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
button = Button(12, Pin.IN, Pin.PULL_UP)


main_menu()