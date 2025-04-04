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


def draw(points, screen):
    x = 0
    for y in points:
        screen.pixel(x, y, 1)
        x += 1


read = Filefifo(10, name='capture_250Hz_01.txt')
rot = Encoder(10, 11)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_w = 128
oled_h = 64
oled = SSD1306_I2C(oled_w, oled_h, i2c)
data = []
high = read.get()
low = high
data.append(high)
for i in range(999):
    d = read.get()
    if d > high:
        high = d
    if d < low:
        low = d
    data.append(d)
cursor = 64
i = 0
for d in data:
    d -= low
    d /= (high - low) / 64
    d = int(d)
    if d > 63:
        d = 63
    data[i] = d
    i += 1
first = data[0:127]
oled.fill(0)
draw(first, oled)
oled.show()

while True:
    if rot.fifo.has_data():
        cursor += rot.fifo.get()
        if cursor > len(data) - 63:
            cursor = len(data) - 63
        if cursor < 64:
            cursor = 64
        oled.fill(0)
        a = cursor - 64
        b = cursor + 63
        draw(data[a:b], oled)
        oled.show()
