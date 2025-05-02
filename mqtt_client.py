from umqtt.simple import MQTTClient
import json

# MQTT settings
MQTT_BROKER = "hrm02.asuscomm.com"
MQTT_PORT = 1883
TOPIC_RRI = "kubios-request"

def upload_rr_intervals(timestamp, rr_intervals):
    MQTT_BROKER = "hrm02.asuscomm.com"
    MQTT_PORT = 1883
    TOPIC_RRI = "kubios-request"
    try:
        client = MQTTClient(client_id="hrva3000", server=MQTT_BROKER, port=MQTT_PORT)
        client.connect()

        payload = {
            "id": timestamp,  # Unique ID from current time
            "type": "RRI",
            "data": rr_intervals,  # This should be a list of ints
            "analysis": {
                "type": "readiness"
            }
        }

        client.publish(TOPIC_RRI, json.dumps(payload))
        client.disconnect()
        print("Data uploaded to Kubios Proxy.")

    except Exception as e:
        print("Upload failed:", e)

