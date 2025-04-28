from filefifo import Filefifo
from fifo import Fifo
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
from piotimer import Piotimer

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
    y /= scale / 30
    y = int(y)
    y = 29 - y
    return y

def draw(points, screen, cursor):
    show = []
    i = 0
    for _ in range(len(points)/10-1):
        a = 0
        for _ in range(10):
            a += points[i]
            i += 1
        show.append(a/5)
    scale = getScale(show[cursor:cursor+127])
    offset= getOffset(show[cursor:cursor+127])
    screen.fill(0)
    x = 1
    prev = adjust(int(show[int(cursor/10)]), scale, offset)
    for y in show[cursor+1:cursor+127]:
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

def advance(tid):
    global cursor
    cursor += 1
    if cursor > 900:
        tmr.deinit()

data = Filefifo(10, name='capture01_250Hz.txt')
cursor = 0
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_w = 128
oled_h = 64
oled = SSD1306_I2C(oled_w, oled_h, i2c)
datas = []
high = data.get()
low = high
datas.append(high)
for _ in range(9999):
    datas.append(data.get())
tmr = Piotimer(period=50, mode=Piotimer.PERIODIC, callback=advance)

while cursor < len(datas) - 128:
    draw(datas, oled, cursor)