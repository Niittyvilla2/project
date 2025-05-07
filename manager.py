from pip._internal import network
from umqtt.simple import MQTTClient
import json
from machine import RTC
import math
from hr import HR
import time
import os
import ujson

class Manager:
    def __init__(self, ppg):
        self.hr = HR(ppg)
        self.intervals = []
        self.collecting = False
        self.timeStart = None
        self.timeEnd = None
        self.minIntervals = 30
        self.rtc = RTC()
        self.mqtt_broker = "hrm02.asuscomm.com"
        self.mqtt_port = 1883
        self.mqtt_topic_request = "kubios-request"
        self.mqtt_topic_response = "kubios-response"
        self.wifi_ssid = 'KMD652_Group_2'
        self.wifi_password = 'N4fSLAzxu7VvEm8'
        self.connect_wifi()
        if not self.history_dir():
            os.mkdir("/history")

    def connect_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.wifi_ssid, self.wifi_password)
        while not wlan.isconnected():
            time.sleep(1)

    def history_dir(self):
        try:
            return "history" in os.listdir("/")
        except Exception as e:
            return False

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
        try:
            client = MQTTClient(client_id="hrva3000", server=self.mqtt_broker, port=self.mqtt_port)
            client.connect()

            payload = {
                "id": str(self.timeStart) + '-' + str(self.timeEnd) ,  # Unique ID from current time
                "type": "RRI",
                "data": self.intervals,  # This should be a list of ints
                "analysis": {
                    "type": "readiness"
                }
            }

            client.publish(self.mqtt_topic_request, json.dumps(payload))
            client.disconnect()
            print("Data uploaded to Kubios Proxy.")

        except Exception as e:
            print("Upload failed: ", e)

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

    def get_data(self):
        message = None

        def callback(topic, msg):
            nonlocal message
            message = msg

        client = MQTTClient(client_id="hrva3000", server=self.mqtt_broker, port=self.mqtt_port)
        client.set_callback(callback)
        client.connect()
        client.subscribe(self.mqtt_topic_response)
        while message is None:
            client.wait_msg()
        client.disconnect()
        self.save_history(message)
        return message

    def get_history(self):
        history_list = os.listdir("/history")
        return history_list

    def save_history(self, topic, response):
        name = '/' + response['id'] + '.json'
        if os.path.exists(name):
            print("History file already exists")
            return
        with open(name, 'w') as json_file:
            ujson.dump(response, json_file)

    def read_history(self, file):
        with open(file, 'r') as json_file:
            return ujson.load(json_file)