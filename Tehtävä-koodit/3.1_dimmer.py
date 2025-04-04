from machine import Pin
from fifo import Fifo
from led import Led
from time import sleep


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
            if self.release >= 3:
                self.release = 3
                self.state = False

        return self.state

    def single(self):
        if self.down:
            if not self.pressed():
                self.down = False
        else:
            if self.pressed():
                self.down = True
                return True

        return False


class Encoder:
    def __init__(self, rA, rB):
        self.a = Pin(rA, mode=Pin.IN)
        self.b = Pin(rB, mode=Pin.IN)
        self.fifo = Fifo(30, typecode='i')
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)

    def handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)


button = Button(12, mode=Pin.IN, pull=Pin.PULL_UP)
rot = Encoder(10, 11)
led1 = Led(22)
led2 = Led(21)
led3 = Led(20)
brightness = 1

while True:
    if rot.fifo.has_data():
        brightness += rot.fifo.get()
        if brightness > 100:
            brightness = 100
        elif brightness < 1:
            brightness = 1
        led1.brightness(brightness)
    if button.single():
        led1.toggle()
