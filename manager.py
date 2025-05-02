from umqtt.simple import MQTTClient
import json


from hr import HR

class Manager:
    def __init__(self, ppg):
        self.hr = HR(ppg)
        self.intervals = []
        self.collecting = False
        self.timeStart = None
        self.timeEnd = None
        self.minIntervals = 30

    def collect_hr(self):
        interval = self.hr.get_beat_interval()
        self.intervals.append(interval)
        return interval

    def collect_start(self):
        self.timeStart = time()
        self.collecting = True

    def collect_end(self):
        self.timeEnd = time()
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
