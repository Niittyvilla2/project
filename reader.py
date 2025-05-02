from fifo import Fifo
from machine import Pin, ADC
from piotimer import Piotimer


class Reader:
    def __init__(self, pin):
        self.fifo = Fifo(250, typecode='i')
        self.data = ADC(Pin(27))
        self.tmr = None
        self.interval = 4

    def poll_data(self, tid):
        data = int(self.data.read_u16())
        self.fifo.put(data)

    def read_next(self):
        return self.fifo.get()

    def has_data(self):
        return self.fifo.has_data()

    def start(self, interval):
        self.interval = interval
        self.tmr = Piotimer(period=interval, mode=Piotimer.PERIODIC, callback=self.poll_data)

    def stop(self):
        self.tmr.deinit()
