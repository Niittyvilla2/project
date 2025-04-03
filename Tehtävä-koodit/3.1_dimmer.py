from machine import Pin
from fifo import Fifo
from led import Led

button = Pin(12, mode = Pin.IN, pull = Pin.PULL_UP)
led1 = Led(22, mode = Pin.OUT)
led2 = Led(21, mode = Pin.OUT)
led3 = Led(20, mode = Pin.OUT)

class Encoder:
    def __init__(self, rA, rB):
        self.a = Pin(rA, mode = Pin.IN)
        self.b = Pin(rB, mode = Pin.IN)
        self.fifo = Fifo(30, typecode = 'i')
        self.a.irq(handler = self.handler, trigger = Pin.IRQ_RISING, hard = True)
        
    def handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)
            
rot = Encoder(10, 11)

while True:
    if rot.fifo.has_data():
        