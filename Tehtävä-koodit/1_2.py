from machine import Pin, UART, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import time

button = Pin(9, Pin.IN, Pin.PULL_UP)
i2c = I2C(1, scl = Pin(15), sda = Pin(14), freq = 400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

oled.fill(0) #clean up screen
pixel_row = 0 #row of pixels where the text prints
while True:
    if pixel_row >= 63:
        oled.scroll(0, -8)
        oled.rect(0, 55, 127, 8, 0, True)
        pixel_row = 55 #move the pixel row so it stays on screen
    text = input("")
    oled.text(text, 0, pixel_row, 1) #put the row the pixels print lower
    oled.show()
    pixel_row += 8