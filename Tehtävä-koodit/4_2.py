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

def draw(points, screen, cursor):
    if cursor < 250:
        scale = getScale(points[0:250])
        offset= getOffset(points[0:250])
    else:
        scale = getScale(points[cursor-250:cursor-1])
        offset= getOffset(points[cursor-250:cursor-1])
    screen.fill(0)
    x = 1
    prev = adjust(int(points[cursor]), scale, offset)
    for y in points[cursor+1:cursor+127]:
        y = adjust(y, scale, offset)
        screen.line(x-1, prev, x, y, 1)
        prev = y
        x += 1
    screen.show()

def getScale(list):
    high = list[0]
    low = high
    for i in list:
        if i > high:
            high = i
        if i < low:
            low = i
    return high - low

def getOffset(list):
    low = list[0]
    for i in list:
        if i < low:
            low = i
    return low

rot = Encoder(10, 11)
data = Filefifo(10, name='capture02_250Hz.txt')
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_w = 128
oled_h = 64
oled = SSD1306_I2C(oled_w, oled_h, i2c)
datas = []
high = data.get()
low = high
datas.append(high)
cursor = 0


for i in range(500):
    a = 0
    for _ in range(5):
        a += data.get()
    d = a / 5
    if d > high:
        high = d
    if d < low:
        low = d
    datas.append(d)
i = 0

for d in datas:
    d -= low
    d /= (high - low) / 64
    d = int(d)
    if d > 63:
        d = 63
    datas[i] = d
    i += 1
    
    
first = datas[0:127]
oled.fill(0)
draw(first, oled, cursor)
oled.show()
print(len(datas))

while True:
    if rot.fifo.has_data():
        while rot.fifo.has_data():
            cursor += rot.fifo.get()
            if cursor > len(datas) - 127:
                cursor = len(datas) - 127
            if cursor < 0:
                cursor = 0
        draw(datas, oled, cursor)