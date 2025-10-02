import network, json, time
from samplee import MQTTClient

SSID = "WE_E243BC"
PASSWORD = "m4333534"
THING_NAME = "ESP32"
ENDPOINT= "a2buymsb62uu50-ats.iot.us-east-1.amazonaws.com"

TOPIC_PUBLISH = "system/response"
TOPIC_SUBSCRIBE = "system/command"
TOPIC_TEMPERATURE = "system/temperature"


SSL_CONFIG = {
    "key": "/Private.pem.key",
    "cert": "/Certificate.pem.crt",
}

mqtt_client = None

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting to WiFi...")
    while not wlan.isconnected():
        time.sleep(1)
        print(".")
    print(f"Connected to WiFi, IP: {wlan.ifconfig()[0]}")

def connect_iot_core(callback):
    global mqtt_client
    mqtt_client = MQTTClient(
        client_id = THING_NAME,
        server = ENDPOINT,
        port = 8883,
        ssl = True,
        ssl_params = SSL_CONFIG
    )
    mqtt_client.set_callback(callback)  
    print("Connecting to AWS IoT Core...")
    mqtt_client.connect()
    print("Connected!")
    mqtt_client.subscribe(TOPIC_SUBSCRIBE)
    print(f"Subscribed to: {TOPIC_SUBSCRIBE}")
    return mqtt_client

def publish_message(mqtt_client, topic, message):
    payload = json.dumps(message)
    mqtt_client.publish(topic, payload)
    print(f"Published to {topic}: {payload}")
