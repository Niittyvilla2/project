from filefifo import Filefifo
from fifo import Fifo
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
from piotimer import Piotimer


class PPG:
    def __init__(self, screen, xMin, yMin, xMax, yMax,):
        self.screen = screen
        self.scale = 0
        self.offset = 0
        self.yMin = yMin
        self.xMin = xMin
        self.yMax = yMax
        self.xMax = xMax

    def adjust(self, y):
        y -= self.offset
        y /= self.scale / self.yMax
        y = int(y)
        y = 29 - y
        return y

    def plot(self, points, squish):
        show = []
        i = 0
        for _ in range(len(points) / squish - 1):
            a = 0
            for _ in range(squish):
                a += points[i]
                i += 1
            squished = a / squish
            show.append(squished)
        self.setScale(show)
        #self.setOffset(show)
        self.screen.fill_rect(self.xMin, self.yMin, self.xMax, self.yMax, 0)
        x = 1
        prev = self.adjust(show[0])
        for y in show[1:127]:
            y = self.adjust(y)
            self.screen.line(x - 1, prev, x, y, 1)
            prev = y
            x += 1

    def setScale(self, list):
        high = list[0]
        low = high
        for i in list:
            if i > high:
                high = i
            if i < low:
                low = i
        scale = high - low
        self.scale = scale
        self.offset = low

    def setOffset(self, list):
        low = list[0]
        for i in list:
            if i < low:
                low = i
        if low < self.offset:
            self.offset = low
