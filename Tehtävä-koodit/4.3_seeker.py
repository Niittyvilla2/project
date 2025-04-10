from filefifo import Filefifo
from fifo import Fifo
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C


class Encoder:
    def __init__(self, rA, rB):
        self.a = Pin(rA, mode=Pin.IN)
        self.b = Pin(rB, mode=Pin.IN)
        self.fifo = Fifo(1000, typecode='i')
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)

    def handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

def adjust(y, scale, offset):
    y -= offset
    y /= scale / 64
    y = int(y)
    y = 63 - y
    return y
            
def draw(points, screen, scale, offset):
    screen.fill(0)
    x = 1
    prev = adjust(int(points[0]), scale, offset)
    for y in points[1:len(points)-1]:
        y = adjust(y, scale, offset)
        screen.line(x-1, prev, x, y, 1)
        prev = y
        x += 1
    screen.show()

button0 = Pin(9, Pin.IN, Pin.PULL_UP)
button1 = Pin(8, Pin.IN, Pin.PULL_UP)
button2 = Pin(7, Pin.IN, Pin.PULL_UP)
rot = Encoder(10, 11)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_w = 128
oled_h = 64
oled = SSD1306_I2C(oled_w, oled_h, i2c)
read = Filefifo(10, name='capture03_250Hz.txt')
data = []
cursor = 0
scale = 1
mScale = [0.1, 25000]
offset = 0
mOffset = [0, 2**16]

while True:
    if len(data) == 0:
        m = 'Press SW_1'
        oled.fill(0)
        oled.text(m, 50, 28, 1)
        oled.show()
    if button1.value() == 0 and len(data) == 0:
        for _ in range(360):
            d = 0
            for _ in range(5):
                d = d + read.get()
            d = d / 5
            data.append(d)
        high = data[0]
        low = high
        for d in data:
            if d > high:
                high = d
            if d < low:
                low = d
        scale = high - low
        offset = low
        draw(data[0:127], oled, scale, offset)
    if rot.fifo.has_data():
        while rot.fifo.has_data() and button0.value() == 1 and button2.value() == 1 and len(data) > 0:
            cursor += rot.fifo.get()
            if cursor > len(data) - 127:
                cursor = len(data) - 127
            if cursor < 0:
                cursor = 0
        while rot.fifo.has_data() and button0.value() == 0 and button2.value() == 1 and len(data) > 0:
            print('offset: '+str(offset))
            value = rot.fifo.get()
            offset = offset + value * 100
            if offset < mOffset[0]:
                offset = mOffset[0]
            if offset > mOffset[1]:
                offset = mOffset[1]
        while rot.fifo.has_data() and button0.value() == 1 and button2.value() == 0 and len(data) > 0:
            print('scale: '+str(scale))
            value = rot.fifo.get()
            scale = scale + value * 250
            if scale < mScale[0]:
                scale = mScale[0]
            if scale > mScale[1]:
                scale = mScale[1]
        if len(data) > 0:
            draw(data[cursor:cursor+127], oled, scale, offset)
    