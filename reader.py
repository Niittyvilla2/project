from fifo import Fifo
from machine import Pin, ADC
from piotimer import Piotimer


class Reader:
    def __init__(self, pin):
        self.fifo = Fifo(2500, typecode='i')
        self.data = ADC(Pin(27))
        self.tmr = None

    def poll_data(self, tid):
        self.fifo.put(int(self.data.read_u16()))

    def read_next(self):
        return self.fifo.get()

    def has_data(self):
        return self.fifo.has_data()

    def start(self):
        self.tmr = Piotimer(period=4, mode=Piotimer.PERIODIC, callback=self.poll_data)

    def stop(self):
        self.tmr.deinit()
