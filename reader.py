from fifo import Fifo
from machine import Pin
from piotimer import Piotimer


class Reader:
    def __init__(self, pin):
        self.fifo = Fifo(333, typecode='i')
        self.data = Pin(pin, mode=Pin.IN)
        self.tmr = None
        self.timer()

    def poll_data(self, tid):
        self.fifo.put(int(self.data.value()))

    def read_next(self):
        return self.fifo.get()

    def has_data(self):
        return self.fifo.has_data()

    def timer(self):
        self.tmr = Piotimer(period=10, mode=Piotimer.PERIODIC, callback=self.poll_data)