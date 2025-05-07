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

def progressbar():
    prog = 0
    def progress(tid):
        nonlocal prog
        prog += 1
        length = 104 / 30 * prog - 1
        oled.fill_rect(10, 52, int(length), 8, 1)
        oled.show()
    oled.rect(8, 50, 108, 12, 1)
    oled.fill_rect(10,52,1,8,1)
    oled.show()
    timer = Piotimer(period=1000, mode=Piotimer.PERIODIC, callback=progress)
        
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
                main_menu()
                bpmStart = False


def hrv_start():
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
                hrvStart = False
                main_menu()
            if place == 0:
                hrvStart = False
                hrv_mesuring()


def hrv_mesuring():
    oled.fill(0)
    oled.text("Mesuring. Press", 0, 0, 1)
    oled.text("the button to", 0, 10, 1)
    oled.text("stop early.", 0, 20, 1)
    oled.show()
    timer.init(mode=Timer.ONE_SHOT, period=30000, callback=hrv_results)
    progressbar()
    manager.collect_start()
    hrvMesure = True
    while hrvMesure == True:
        manager.collect_hr()
        if button.onepress():
            oled.fill(0)
            oled.text("Mesurment", 0, 20, 1)
            oled.text("stopped", 0, 30, 1)
            oled.show()
            time.sleep(3)
            hrvMesure = False
            hrv_start()


def hrv_results(tid):
    oled.fill(0)
    manager.collect_end()
    data = manager.calculate()
    oled.text(f"Mean PPI:{data['data']['mean_rr_ms']}", 0, 0, 1)
    oled.text("Mean HR:" + str(values["mean_hr"]), 0, 10, 1)
    oled.text("RMSSD:" + str(values["rmssd"]), 0, 20, 1)
    oled.text("SDNN:" + str(values["sdnn"]), 0, 30, 1)
    oled.text("Back", 10, 56, 1)
    hrv_cursor(0)
    oled.show()
    hrvResults = True
    while hrvResults == True:
        
        if button.onepress():
            hrvResults = False
            hrv_start()


def kubios_start():
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
    kubiosStart = True
    place = 0
    while kubiosStart == True:
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
                kubiosStart = False
                main_menu()
            if place == 1:
                kubiosStart = False
                kubios_mesuring()


def kubios_mesuring():
    oled.fill(0)
    manager.kubios = True
    manager.collect_start()
    oled.text("Mesuring. Press", 0, 0, 1)
    oled.text("the button to", 0, 10, 1)
    oled.text("stop early.", 0, 20, 1)
    oled.show()
    progressbar()
    # Progressbar?
    # gather data for 30s
    # send and recive data from Kubios, save mesurment with timestamp
    # save data
    # move to kubios_results
    kubiosMesure = True
    while kubiosMesure == True:
        if button.onepress():
            # stop mesurment and dont save it
            manager.kubios = False
            kubiosMesure = False
            manager.collect_end()
            kubios_start()


def kubios_results():
    oled.fill(0)
    # display kubios data
    kubios_cursor(0)
    oled.show()
    kubiosResults = True
    waiting = True
    while kubiosResults == True:
        while waiting == True:
            oled.fill(0)
            oled.text("Waiting results", 0, 0, 1)
            oled.text("Please wait", 0, 9, 1)
            oled.show()
            data = manager.get_data()
        oled.text(f"Mean PPI:{data['data']['mean_rr_ms']}", 0, 0, 1)
        oled.text(f"Mean HR:{data['data']['mean_hr_bpm']:.2f}", 0, 9, 1)
        oled.text(f"RMSSD:{data['data']['rmssd_ms']:.2f}", 0, 19, 1)
        oled.text(f"SDNN:{data['data']['sdnn_ms']:.2f}", 0, 28, 1)
        oled.text(f"SNS:{data['data']['sns_index']:.2f}", 0, 37, 1)
        oled.text(f"PNS:{data['data']['stress_index']:.2f}", 0, 46, 1)
        oled.text("Back", 10, 56, 1)
        menu_cursor(56)
        waiting = False
        if button.onepress():
            kubiosResults = False
            kubios_start()


def history_menu():
    oled.fill(0)
    oled.text("Back", 10, 0, 1)
    y = 0
    count = 0
    history = manager.get_history()

    for m in history:
        y += 10
        count += 1
        oled.text(m[0:len(m)-6], 10, y, 1)
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
#placeholder = [5, 2]
rot = Encoder(10, 11)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
ppg = PPG(oled, 0, 0, 127, 30)
manager = Manager(ppg)
button = Button(12, Pin.IN, Pin.PULL_UP)
timer = Timer()

main_menu()

