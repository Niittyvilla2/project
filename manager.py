import network
from umqtt.simple import MQTTClient
import json
from machine import RTC
import ntptime
import math
from hr import HR
import time
import os
import ujson

class Manager:
    def __init__(self, ppg):
        self.hr = HR(ppg)
        self.screen = self.hr.ppg.screen
        self.intervals = []
        self.collecting = False
        self.timeStart = None
        self.minIntervals = 15
        self.rtc = RTC()
        self.mqtt_broker = "192.168.2.253"
        self.mqtt_port = 21883
        self.mqtt_topic_request = "kubios-request"
        self.mqtt_topic_response = "kubios-response"
        self.mqtt_topic_save = "hr-data"
        self.wifi_ssid = 'KMD652_Group_2'
        self.wifi_password = 'N4fSLAzxu7VvEm8'
        self.screen.text("Connecting", 10, 24, 1)
        self.screen.text("to Wi-Fi", 10, 32, 1)
        self.screen.show()
        self.connect_wifi()
        self.bpm = 0
        self.kubios = False
        self.rct = RTC()
        if not self.history_dir():
            os.mkdir("/history")
        ntptime.settime()

    def connect_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.wifi_ssid, self.wifi_password)
        while not wlan.isconnected():
            print('wifi retry')
            time.sleep(3)

    def history_dir(self):
        try:
            return "history" in os.listdir("/")
        except Exception as e:
            return False

    def collect_hr(self):
        interval = self.hr.get_beat_interval()
        if 315 < interval < 1400:
            self.intervals.append(interval)
            print(interval)
        return interval

    def collect_start(self):
        time = self.rtc.datetime()
        self.timeStart = str(time[0])[2:4] + "-" + str(time[1]) + "-" + str(time[2]) + " " + str(time[4]) + str(
            time[5])
        self.intervals.clear()
        self.collecting = True

    def collect_end(self):
        self.collecting = False
        self.hr.reader.stop()
        if self.kubios:
            if len(self.intervals) >= self.minIntervals:
                self.send_data()
                return True
            else:
                return False
        else:
            return True

    def calculate_hr(self):
        a = 0
        self.screen.text(str(self.bpm), 50, 34, 0)
        if len(self.intervals) > 5:
            a += self.intervals[len(self.intervals) - 5]
            a += self.intervals[len(self.intervals) - 4]
            a += self.intervals[len(self.intervals) - 3]
            a += self.intervals[len(self.intervals) - 2]
            a += self.intervals[len(self.intervals) - 1]
            a = a / 5
            b = 60 * (1000 / a)
            b = round(b, 1)
            self.bpm = b
        self.screen.text(str(self.bpm), 50, 34, 1)
        self.screen.show()
        if len(self.intervals) > 200:
            for _ in self.intervals[0:len(self.intervals) - 6]:
                self.intervals.pop()

    def connect_mqtt(self):
        try:
            client = MQTTClient(client_id="hrva3000", server=self.mqtt_broker, port=self.mqtt_port)
            client.connect()
            print("Connected to MQTT broker")
            return client
        except Exception as e:
            print("Upload failed: ", e)
            return None

    def send_proxy(self, values):
        client = None
        date = time.time()
        data = {"id": self.timeStart,
                "timestamp": date,
                "mean_hr": values['mean_hr'],
                "mean_ppi": values['mean_ppi'],
                "rmssd": values['rmssd'],
                "sdnn": values['sdnn']}
        if 'sns' in values:
            data['sns'] = values['sns']
        if 'pns' in values:
            data['pns'] = values['pns']
        while client is None:
            client = self.connect_mqtt()
            if client:
                try:
                    client.publish(self.mqtt_topic_save, ujson.dumps(data))
                    client.disconnect()
                    print('Data saved to proxy')
                except Exception as e:
                    print("Upload failed: ", e)
            time.sleep(5)

    def send_data(self):
        print('waiting kubios')
        client = None
        while client is None:
            client = self.connect_mqtt()
            if client:
                try:
                    payload = {
                        "id": self.timeStart,  # Unique ID from current time
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
            time.sleep(5)

    def calculate(self):
        # ppi = [5, 3, 5, 6]  # list of ppi's
        # hr = [5, 3, 5, 6]  # list of hr's
        print('starting calc')
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
        time_str = "{:02d}-{:02d}-{:02d}-{:02d}-{:02d}".format(time[0] % 100, time[1], time[2], time[4], time[5])
        timestamp = time_str
        self.intervals.clear()

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
        client = None
        counter = 0

        def callback(topic, msg):
            nonlocal message
            print('Kubios analysis retrieved')
            message = msg

        while client is None:
            client = self.connect_mqtt()
            if client:
                client.set_callback(callback)
                client.subscribe(self.mqtt_topic_response)
                while message is None:
                    print(f"waiting for response {counter}s")
                    client.check_msg()
                    time.sleep(5)
                    counter += 5
                client.disconnect()
                self.save_history(message)
                return message
            time.sleep(5)

    def get_history(self):
        history_list = os.listdir("/history")
        return history_list

    def save_history(self, response):
        path = '/history/'
        file = response['id'] + '.json'
        files = os.listdir(path)
        if not file in files:
            with open(path[1:len(path)] + file, 'w') as json_file:
                ujson.dump(response, json_file)
            print("History saved")
        else:
            print("History already exists")
        values = {"id": response['id'],
                  "mean_hr": response['data']['analysis']['mean_hr_bpm'],
                  "mean_ppi": response['data']['analysis']['mean_rr_ms'],
                  "rmssd": response['data']['analysis']['rmssd_ms'],
                  "sdnn": response['data']['analysis']['sdnn_ms']}
        if 'sns_index' in response:
            values['sns'] = response['data']['analysis']['sns_index']
        if 'stress_index' in response:
            values['pns'] = response['data']['analysis']['stress_index']
        print(f"History: {values}")
        self.send_proxy(values)

    def read_history(self, file):
        with open(file, 'r') as json_file:
            return ujson.load(json_file)

    def save_local(self, measurements):
        analysis = {'mean_rr_ms': measurements['mean_ppi'],
                    'mean_hr_bpm': measurements['mean_hr'],
                    'rmssd_ms': measurements['rmssd'],
                    'sdnn_ms': measurements['sdnn'],
                    'sns_index': 0.00,
                    'stress_index': 0.00}
        data = {'analysis': analysis}
        json = {'id': measurements['timestamp'], 'data': data}
        print(f"Local : {json}")
        self.save_history(json)

