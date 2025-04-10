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
    oled.text("Mesure BPM", 0, 20, 1)
    oled.text("Analysis", 0, 30, 1)
    oled.text("History", 0, 40, 1)
    oled.text("Kubios", 0, 50, 1)
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
                oled.show()
            
            elif place <= 0:
                place = 0
                menu_cursor(20)
                oled.show()
            
            elif place == 2:
                menu_cursor(40)
                oled.show()
                
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
    oled.text("Start/Stop", 0, 46, 1)
    oled.text("Back", 0, 56, 1)
    menu_cursor(45)
    oled.show()
    place = 0
    mesurmentOn = False
    mesureMenu = True
    while mesureMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 1:
                place = 1
                menu_cursor(56)
                oled.show()
            
            elif place <= 0:
                place = 0
                menu_cursor(46)
                oled.show()
        
        if button.onepress():
            if place == 1:
                main_menu()
                mesureMenu = False
            if place == 0:
                if mesurmentOn == False:
                    mesurmentOn == True
                else:
                    mesurmentOn = False
                        
        while mesurmentOn == True:
            #call for method for mesuring, mesurment takes 30 seconds
            #display BPS method and update every 5 seconds
            #call for live PPG method
            #Display live PPG at all times
            #if mesurment is paused manually before 30 seconds, the result will not be saved
            pass
                
def analysis_menu():
    oled.fill(0)
    #Calls for a method that calculates the mean PPI, mean HR, RMSSD and SDNN from the most reacent sucsessful mesurment
    #(possibly a way to select previous data)

    oled.text("Back", 0, 50, 1)
    menu_cursor(20)
    oled.show()
    place = 0
    analasysMenu = True
    while analasysMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 3:
                place = 3
                menu_cursor(50)
                oled.show()
            
            elif place <= 0:
                place = 0
                menu_cursor(20)
                oled.show()
            
            elif place == 1:
                menu_cursor(30)
                oled.show()
                
            else:
                menu_cursor(40)
                oled.show()
        
        if button.onepress():
            if place == 3:
                main_menu()
                analasys_menu = False
    
def history_menu():
    oled.fill(0)
    oled.text("History", 40, 00, 1)
    #Display the time of previous sucsessful mesurment
    
    #When pressed the time the display changes to show that mesurments data
    menu_cursor(20)
    oled.show()
    place = 0
    historyMenu = True
    while historyMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 3:
                place = 3
                menu_cursor(50)
                oled.show()
            
            elif place <= 0:
                place = 0
                menu_cursor(20)
                oled.show()
            
            elif place == 1:
                menu_cursor(30)
                oled.show()
                
            else:
                menu_cursor(40)
                oled.show()
        
        if button.onepress():
            if place == 3:
                main_menu()
                historyMenu = False
    
    
def kubios_menu():
    oled.fill(0)
    oled.text("Kubios", 40, 00, 1)
    #when started collects a new data session
    #(possibly a way to select previous data)
    #when session ends it automatically sends it to the cloud
    #displays the results on the screen
    #data is also saved locally like other data
    menu_cursor(20)
    oled.show()
    place = 0
    kubiosMenu = True
    while kubiosMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 3:
                place = 3
                menu_cursor(50)
                oled.show()
            
            elif place <= 0:
                place = 0
                menu_cursor(20)
                oled.show()
            
            elif place == 1:
                menu_cursor(30)
                oled.show()
                
            else:
                menu_cursor(40)
                oled.show()
        
        if button.onepress():
            if place == 3:
                main_menu()
                kubiosMenu = False
    
def menu_cursor(place):
    oled.fill_rect(120, 20, 10, 50, 0)
    oled.text("<", 120, place, 1)
    

rot = Encoder(10, 11)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
button = Button(12, Pin.IN, Pin.PULL_UP)


main_menu()