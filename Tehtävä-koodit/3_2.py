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
    

 
rot = Encoder(10, 11)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
button = Button(12, Pin.IN, Pin.PULL_UP)
led1 = Led(22)
led2 = Led(21)
led3 = Led(20)
leds= [led1, led2, led3]

def cursor(place):
    oled.fill_rect(90, 0, 10, 30, 0)
    oled.text("<", 90, place, 1)

def off(place):
    oled.fill_rect(55, place, 30, 10, 0)
    oled.text("OFF", 55, place, 1)
    oled.show()
    
def on(place):
    
    oled.fill_rect(55, place, 30, 10, 0)
    oled.text("ON", 55, place, 1)
    oled.show()

led1.off()
led2.off()
led3.off()
        
oled.fill(0)
oled.text("LED1 - OFF", 0, 00, 1)
oled.text("LED2 - OFF", 0, 10, 1)
oled.text("LED3 - OFF", 0, 20, 1)
cursor(0)
oled.show()

place = 0

while True:
    if rot.fifo.has_data():
        i = rot.fifo.get()
        place += i
        if place >= 2:
            place = 2
            cursor(20)
            oled.show()
            
        elif place <= 0:
            place = 0
            cursor(0)
            oled.show()
            
        else:
            cursor(10)
            oled.show()
        
    if button.onepress():
        i = place
        if leds[i].value() == 0:
            on(i*10)
            leds[i].on()
        elif leds[i].value() == 1:
            leds[i].off()
            off(i*10)
        
