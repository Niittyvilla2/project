import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C

button_up = Pin(9, Pin.IN, Pin.PULL_UP)
button_reset = Pin(8, Pin.IN, Pin.PULL_UP)
button_down = Pin(7, Pin.IN, Pin.PULL_UP)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_w = 128
oled_h = 64
oled = SSD1306_I2C(oled_w, oled_h, i2c)

x = 0
y = 32
oled.fill(0)
oled.show()
while True:
    oled.pixel(x, y, 1)
    oled.show()
    if button_up() == 0:
        y += 1
        if y >= 63:
            y = 63
    elif button_down() == 0:
        y -= 1
        if y <= 0:
            y = 0
    x += 1
    if x >= 128:
        x = 0
    if button_reset() == 0:
        x = 0
        y = 32
        oled.fill(0)
        oled.show()