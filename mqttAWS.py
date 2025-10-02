import json
import paho.mqtt.client as mqtt
import time
import threading

ENDPOINT= "a2buymsb62uu50-ats.iot.us-east-1.amazonaws.com"
PORT = 8883
TOPIC_COMMAND = "system/command"
TOPIC_RESPONSE = "system/response"

CA_PATH = "AmazonRootCA1.pem"
CERT_PATH = "Certificate.pem.crt"
KEY_PATH = "Private.pem.key"


mqtt_client = None
mqtt_response = None
mqtt_lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to AWS IoT")
        client.subscribe(TOPIC_RESPONSE)
    else:
        print(f"Connection failed: {rc}")

def on_message(client, userdata, msg):
    global mqtt_response
    with mqtt_lock:
        mqtt_response = msg.payload.decode()

def init_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.tls_set(ca_certs=CA_PATH, certfile=CERT_PATH, keyfile=KEY_PATH)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(ENDPOINT, PORT, 60)
    thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
    thread.start()

def sendToESP(command, timeout=5):
    global mqtt_response
    with mqtt_lock:
        mqtt_response = None
    try:
        mqtt_client.publish(TOPIC_COMMAND, command)
        start = time.time()
        while time.time() - start < timeout:
            with mqtt_lock:
                if mqtt_response is not None:
                    try:                        
                        response_json = json.loads(mqtt_response)
                        return response_json
                    except:
                        return {"response": mqtt_response}
            time.sleep(0.1)
        return "No response received."
    except Exception as e:
        return f"MQTT error: {e}"
