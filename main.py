import framebuf
from led import Led
from machine import Pin, UART, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import time
from fifo import Fifo
from PPG import PPG
from hr import HR
from reader import Reader
from piotimer import Piotimer
import micropython
from manager import Manager


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

    def onepress(self):
        if self.down:
            if not self.pressed():
                self.down = False

        else:
            if self.pressed():
                self.down = True
                return True

        return False


class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, mode=Pin.IN)
        self.b = Pin(rot_b, mode=Pin.IN)
        self.fifo = Fifo(100, typecode="i")
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)

    def handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)


class Progressbar:
    def __init__(self, screen):
        self.prog = 0
        self.max = 120
        self.screen = screen
        self.timer = None

    def progress(self, tid):
        self.prog += 4
        self.screen.fill_rect(4, 52, self.prog, 8, 1)
        if self.prog == self.max:
            self.stop()
            return

    def stop(self):
        self.timer.deinit()
        self.prog = 0

    def start(self):
        self.prog = 0
        self.timer = Timer(period=1000, mode=Piotimer.PERIODIC, callback=self.progress)
        self.screen.rect(2, 50, 124, 12, 1)
        self.screen.fill_rect(4, 52, 1, 8, 1)


def menu_cursor(place):
    oled.fill_rect(0, 0, 10, 64, 0)
    oled.text(">", 0, place, 1)


def hrv_cursor(place):
    oled.fill_rect(0, 56, 10, 64, 0)
    oled.fill_rect(60, 56, 10, 64, 0)
    oled.text(">", place, 56, 1)


def kubios_cursor(place):
    oled.fill_rect(0, 56, 10, 64, 0)
    oled.fill_rect(60, 56, 10, 64, 0)
    oled.text(">", place, 56, 1)


def main_menu():
    # menu UI
    oled.fill(0)
    oled.text("HRM 3000", 35, 0, 1)
    oled.text("Mesure BPM", 10, 20, 1)
    oled.text("HRV analysis", 10, 30, 1)
    oled.text("Kubios", 10, 40, 1)
    oled.text("History", 10, 50, 1)
    menu_cursor(20)
    oled.show()

    place = 0
    mainMenu = True
    while mainMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place >= 3:
                place = 3
                menu_cursor(50)

            elif place <= 0:
                place = 0
                menu_cursor(20)

            elif place == 2:
                menu_cursor(40)

            else:
                menu_cursor(30)
        oled.show()
        if button.onepress():
            if place == 0:
                bpm_start()
                mainMenu = False
            if place == 1:
                hrv_start()
                mainMenu = False
            if place == 2:
                kubios_start()
                mainMenu = False
            if place == 3:
                history_menu()
                mainMenu = False


def bpm_start():
    oled.fill(0)
    oled.text("Start/Stop", 10, 54, 1)
    oled.text("Back", 10, 44, 1)
    oled.text("BPM: ", 10, 34, 1)
    menu_cursor(44)
    oled.show()
    bpmStart = True
    place = 0
    while bpmStart == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place <= 0:
                place = 0
                menu_cursor(54)
            elif place >= 1:
                place = 1
                menu_cursor(44)
        oled.show()
        if button.onepress():
            if place == 0:
                collect = True
                manager.hr.reader.start(4)
                manager.hr.set_show_ppg(True)
                time.sleep(.5)
                while collect:
                    if button.onepress():
                        print('Stopped')
                        manager.hr.reader.stop()
                        collect = False
                        continue

                    interval = manager.collect_hr()
                    print('interval ' + str(interval))
                    manager.calculate_hr()
            if place == 1:
                manager.hr.set_show_ppg(False)
                bpmStart = False
                main_menu()


def hrv_start():
    global state
    oled.fill(0)
    oled.text("Start meruring", 0, 0, 1)
    oled.text("by placing your", 0, 10, 1)
    oled.text("finger on the", 0, 20, 1)
    oled.text("sensor and press", 0, 30, 1)
    oled.text("start.", 0, 40, 1)
    oled.text("Start", 10, 56, 1)
    oled.text("Back", 70, 56, 1)
    hrv_cursor(0)
    oled.show()
    hrvStart = True
    place = 0
    while hrvStart == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place <= 0:
                place = 0
                hrv_cursor(0)
            elif place >= 1:
                place = 1
                hrv_cursor(60)
        oled.show()
        if button.onepress():
            if place == 1:
                state = None
                main_menu()
            if place == 0:
                hrv_mesuring()


def hrv_mesuring():
    global state
    state = 'hrvMeasuring'
    oled.fill(0)
    oled.text("Mesuring. Press", 0, 0, 1)
    oled.text("the button to", 0, 10, 1)
    oled.text("stop early.", 0, 20, 1)
    oled.show()
    timer.init(mode=Timer.ONE_SHOT, period=30000, callback=hrv_end)
    bar.start()
    manager.collect_start()
    manager.hr.reader.start(4)
    time.sleep(.5)
    while state == 'hrvMeasuring':
        manager.collect_hr()
        oled.show()
        if button.onepress() or len(manager.intervals) >= 35:
            timer.deinit()
            bar.stop()
            manager.hr.reader.stop()
            if len(manager.intervals) < 35:
                oled.fill(0)
                oled.text("Mesurment", 0, 20, 1)
                oled.text("stopped", 0, 30, 1)
                oled.show()
                time.sleep(3)
            else:
                state = 'hrvResults'
            state = 'hrvStart'
            hrv_start()
    oled.fill(0)
    timer.deinit()
    bar.stop()
    manager.collect_end()
    values = manager.calculate()
    oled.show()
    oled.fill(0)
    hrv_cursor(0)
    oled.text(f"Mean PPI {values['mean_ppi']}", 0, 0, 1)
    oled.text(f"Mean HR {values['mean_hr']}", 0, 9, 1)
    oled.text(f"RMSSD {values['rmssd']}", 0, 19, 1)
    oled.text(f"SDNN {values['sdnn']}", 0, 28, 1)
    oled.text(f"{values['timestamp']}", 0, 37, 1)
    oled.text("Back", 10, 56, 1)
    oled.show()
    manager.save_local(values)
    while hrvResults == True:
        if button.onepress():
            hrvResults = False
            hrv_start()

def hrv_end(tid):
    global state
    state = 'hrvResults'


def kubios_start():
    global state
    oled.fill(0)
    oled.text("Start meruring", 0, 0, 1)
    oled.text("by placing your", 0, 10, 1)
    oled.text("finger on the", 0, 20, 1)
    oled.text("sensor and press", 0, 30, 1)
    oled.text("start.", 0, 40, 1)
    oled.text("Start", 10, 56, 1)
    oled.text("Back", 70, 56, 1)
    kubios_cursor(0)
    oled.show()
    state = 'kubiosStart'
    place = 0
    while state == 'kubiosStart':
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place <= 0:
                place = 0
                kubios_cursor(0)
            elif place >= 1:
                place = 0
                kubios_cursor(60)
        oled.show()
        if button.onepress():
            if place == 0:
                kubios_mesuring()
            if place == 1:
                state = None
                main_menu()


def kubios_mesuring():
    global state
    oled.fill(0)
    state = 'kubiosMeasuring'
    manager.kubios = True
    manager.collect_start()
    oled.text("Mesuring. Press", 0, 0, 1)
    oled.text("the button to", 0, 10, 1)
    oled.text("stop early.", 0, 20, 1)
    oled.show()
    timer.init(mode=Timer.ONE_SHOT, period=30000, callback=end_kubios)
    manager.hr.reader.start(4)
    time.sleep(.5)
    bar.start()

    while state == 'kubiosMeasuring':
        manager.collect_hr()
        oled.show()
        if button.onepress():
            # stop mesurment and dont save it
            manager.kubios = False
            bar.stop()
            timer.deinit()
            manager.collect_end()
            kubios_start()

    print(manager.kubios)
    oled.fill(0)
    if not manager.collect_end():
        menu_cursor(0)
        oled.text("Back", 10, 0, 1)
        oled.text("Not enough", 8, 9, 1)
        oled.text("intervals for", 8, 18, 1)
        oled.text("Kubios analysis", 8, 27, 1)
        oled.show()
        while True:
            if button.onepress():
                kubios_start()
    # display kubios data
    kubios_cursor(0)
    oled.show()
    oled.fill(0)
    oled.text("Waiting results", 0, 0, 1)
    oled.text("Please wait", 0, 9, 1)
    oled.show()
    data = manager.get_data()
    print("TEST")
    while state == 'kubiosResults':
        oled.fill(0)
        oled.text(f"Mean PPI:{data['data']['analysis']['mean_rr_ms']}", 0, 0, 1)
        oled.text(f"Mean HR:{data['data']['analysis']['mean_hr_bpm']:.2f}", 0, 9, 1)
        oled.text(f"RMSSD:{data['data']['analysis']['rmssd_ms']:.2f}", 0, 19, 1)
        oled.text(f"SDNN:{data['data']['analysis']['sdnn_ms']:.2f}", 0, 28, 1)
        oled.text(f"SNS:{data['data']['analysis']['sns_index']:.2f}", 0, 37, 1)
        oled.text(f"PNS:{data['data']['analysis']['stress_index']:.2f}", 0, 46, 1)
        oled.text("Back", 10, 56, 1)
        menu_cursor(56)
        oled.show()
        if button.onepress():
            state = 'kubiosStart'
            kubios_start()


def end_kubios(tid):
    global state
    state = 'kubiosResults'


def history_menu():
    oled.fill(0)
    oled.text("Back", 10, 0, 1)
    y = 0
    count = 0
    history = manager.get_history()

    for m in history:
        y += 10
        count += 1
        oled.text(m[0:len(m) - 5], 10, y, 1)
        if count > 5:
            continue

    menu_cursor(0)
    oled.show()
    historyMenu = True
    place = 0
    while historyMenu == True:
        if rot.fifo.has_data():
            i = rot.fifo.get()
            place += i
            if place <= 0:
                place = 0
                menu_cursor(0)

            elif place == 1 and count >= 1:
                menu_cursor(10)

            elif place == 2 and count >= 2:
                menu_cursor(20)

            elif place == 3 and count >= 3:
                menu_cursor(30)

            elif place == 4 and count >= 4:
                menu_cursor(40)

            elif place == 5 and count >= 5:
                menu_cursor(50)

        oled.show()
        if place > count:
            place = count
        if button.onepress():
            time.sleep(0.1)
            print(place)
            if place == 0:
                historyMenu = False
                main_menu()

            if place == 1 and count >= 1:
                historyMenu = False
                history_show(history[0])

            if place == 2 and count >= 2:
                historyMenu = False

                history_show(history[1])

            if place == 3 and count >= 3:
                historyMenu = False

                history_show(history[2])

            if place == 4 and count >= 4:
                historyMenu = False

                history_show(history[3])

            if place == 5 and count >= 5:
                historyMenu = False

                history_show(history[4])


def history_show(alloy):
    oled.fill(0)
    menu_cursor(0)
    oled.text("Back", 10, 0, 1)
    file = "history/" + str(alloy)
    data = manager.read_history(file)
    oled.text(f"Mean PPI:{data['data']['analysis']['mean_rr_ms']}", 0, 9, 1)
    oled.text(f"Mean HR:{data['data']['analysis']['mean_hr_bpm']:.2f}", 0, 19, 1)
    oled.text(f"RMSSD:{data['data']['analysis']['rmssd_ms']:.2f}", 0, 28, 1)
    oled.text(f"SDNN:{data['data']['analysis']['sdnn_ms']:.2f}", 0, 37, 1)
    oled.text(f"SNS:{data['data']['analysis']['sns_index']:.2f}", 0, 46, 1)
    oled.text(f"PNS:{data['data']['analysis']['stress_index']:.2f}", 0, 55, 1)
    oled.show()
    historyShow = True
    while historyShow == True:
        if button.onepress():
            history_menu()
            historyShow = False


# defining stuff
micropython.alloc_emergency_exception_buf(200)
# placeholder = [5, 2]
state = None
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
bar = Progressbar(oled)
ppg = PPG(oled, 0, 0, 127, 30)
manager = Manager(ppg)
button = Button(12, Pin.IN, Pin.PULL_UP)
rot = Encoder(10, 11)
timer = Timer()

main_menu()


