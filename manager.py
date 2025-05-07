from umqtt.simple import MQTTClient
import json
from machine import RTC
import math
from hr import HR
import time

class Manager:
    def __init__(self, ppg):
        self.hr = HR(ppg)
        self.intervals = []
        self.collecting = False
        self.timeStart = None
        self.timeEnd = None
        self.minIntervals = 30
        self.rtc = RTC()

    def collect_hr(self):
        interval = self.hr.get_beat_interval()
        self.intervals.append(interval)
        return interval

    def collect_start(self):
        self.timeStart = time.time()
        self.collecting = True

    def collect_end(self):
        self.timeEnd = time.time()
        self.collecting = False
        #if len(self.intervals) > self.minIntervals:
            #self.send_data()
    def calculate_hr(self):
        a = 0
        if len(self.intervals) > 5:
            a += self.intervals[len(self.intervals) - 5]
            a += self.intervals[len(self.intervals) - 4]
            a += self.intervals[len(self.intervals) - 3]
            a += self.intervals[len(self.intervals) - 2]
            a += self.intervals[len(self.intervals) - 1]
            a = a/5
            b = 60*(1000/a)
            b = round(b, 1)
            return b
        else:
            return None

    def send_data(self):
        MQTT_BROKER = "hrm02.asuscomm.com"
        MQTT_PORT = 1883
        TOPIC_RRI = "kubios-request"
        try:
            client = MQTTClient(client_id="hrva3000", server=MQTT_BROKER, port=MQTT_PORT)
            client.connect()

            payload = {
                "id": str(self.timeStart) + '-' + str(self.timeEnd) ,  # Unique ID from current time
                "type": "RRI",
                "data": self.intervals,  # This should be a list of ints
                "analysis": {
                    "type": "readiness"
                }
            }

            client.publish(TOPIC_RRI, json.dumps(payload))
            client.disconnect()
            print("Data uploaded to Kubios Proxy.")

        except Exception as e:
            print("Upload failed:", e)

    def calculate(self):
        #ppi = [5, 3, 5, 6]  # list of ppi's
        #hr = [5, 3, 5, 6]  # list of hr's
        mean_ppi = sum(self.intervals) / len(self.intervals)
        mean_hr = 60000 / mean_ppi
        i = 0
        ppisum = []

        for _ in range(len(self.intervals)):
            a = (self.intervals[i] - mean_ppi) ** 2
            ppisum.append(a)
            i += 1
        sdnn = math.sqrt(sum(ppisum) / (i - 1))
        i = 0
        p = 0

        for o in range((len(self.intervals)) - 1):
            a = (self.intervals[o + 1] - self.intervals[o]) ** 2
            p += a
            i += 1
        rmssd = math.sqrt(p / (i - 1))
        time = self.rtc.datetime()
        date = str(time[0]) + "/" + str(time[1]) + "/" + str(time[2]) + " " + str(time[4]) + "." + str(time[5])
        timestamp = date

        mesurment = {
            "mean_hr": round(mean_hr, 2),
            "mean_ppi": round(mean_ppi, 2),
            "rmssd": round(rmssd, 2),
            "sdnn": round(sdnn, 2),
            "timestamp": timestamp
        }
        return mesurment