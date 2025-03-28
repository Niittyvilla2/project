import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C

SW0 = Pin(9, Pin.IN, Pin.PULL_UP)
SW2 = Pin(7, Pin.IN, Pin.PULL_UP)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

oled.fill(0)

y = 63-8 # Aloitus y-koordinaatti
x = 63-12 # Aloitus x-koordinaatti
UFO = "<=>"

while True:
    oled.fill(0) #Tyhjennetään näyttö
    oled.text(UFO, x, y, 1)
    oled.show() #Näytetään UFO
    if SW2() == 0: #SW2-nappia painetaan alas
        x-=1 #siirretään yhdellä pikselillä vasemalle
        if x <= 0: #OlED-näytön vasemman sivun raja
            x = 0
    if SW0() == 0: #SW0-nappia painetaan alas
        x+=1 # siirretään yhdellä pikselillä oikealle
        if x >= 127-24: #OLED-näytön oikean sivun raja
            x = 127-24
    


