from machine import Pin, PWM
from samplee import MQTTClient
import time, dht, json
from newAWS import connect_to_wifi, connect_iot_core, publish_message, mqtt_client, TOPIC_PUBLISH, TOPIC_SUBSCRIBE, TOPIC_TEMPERATURE

# --- Mosquitto Local ---
LOCAL_BROKER = "192.168.1.3"
LOCAL_PORT = 1883

# Topics commands
DOOR_COMMAND_TOPIC = "esp/door/command"
LIGHT_COMMAND_TOPIC = "esp/light/command"
PERSON_COMMAND_TOPIC = "esp/person/command"
CLIMATE_COMMAND_TOPIC = "esp/climate/command"

# Topics status
DOOR_STATUS_TOPIC = "esp/door/status"
LIGHT_STATUS_TOPIC = "esp/light/status"
PERSON_STATUS_TOPIC = "esp/person/status"
CLIMATE_STATUS_TOPIC = "esp/climate/status"

# mosquitto clinet
local_client = MQTTClient("esp32-local", LOCAL_BROKER, port=LOCAL_PORT)

# --- Pins setup ---
DHTPIN = 23
IR_PIN = 13
RELAY_PIN = 22
SERVO_PIN = 21
RELAY_ACTIVE_LOW = True

dht_sensor = dht.DHT22(Pin(DHTPIN))
ir_sensor = Pin(IR_PIN, Pin.IN)
relay = Pin(RELAY_PIN, Pin.OUT)
servo = PWM(Pin(SERVO_PIN), freq=50)

def relay_set(on):
    relay.value(0 if (on and RELAY_ACTIVE_LOW) else 1 if RELAY_ACTIVE_LOW else int(on))

def set_angle(angle):
    min_angle = 1638
    max_angle = 8192
    duty = int(min_angle + (angle / 180) * (max_angle - min_angle))
    servo.duty_u16(duty)

# --- Initial states ---
relay_set(False)
set_angle(0)
last_temp_publish = time.ticks_ms()

# --- Command handler ---
def handle_command(topic, cmd):
    cmd = cmd.strip().lower()
    print(f">>> Command [{topic}]: {cmd}")

    if topic == TOPIC_SUBSCRIBE:
        if cmd == "open":
            set_angle(90)
            publish_message(mqtt_client, TOPIC_PUBLISH, {"response": "opened"})
            publish_message(local_client, DOOR_STATUS_TOPIC, {"door": "opened"})
            
        elif cmd == "close":
            set_angle(0)
            publish_message(mqtt_client, TOPIC_PUBLISH, {"response": "closed"})
            publish_message(local_client, DOOR_STATUS_TOPIC, {"door": "closed"})

        elif cmd == "turn on":
            relay_set(True)
            publish_message(mqtt_client, TOPIC_PUBLISH, {"response": "light on"})
            publish_message(local_client, LIGHT_STATUS_TOPIC, {"light": "light on"})
            
        elif cmd == "turn off":
            relay_set(False)
            publish_message(mqtt_client, TOPIC_PUBLISH, {"response": "light off"})
            publish_message(local_client, LIGHT_STATUS_TOPIC, {"light": "light off"})

        elif cmd == "status":
            if ir_sensor.value() == 0:
                publish_message(mqtt_client, TOPIC_PUBLISH, {"response": "someone"})
                publish_message(local_client, PERSON_STATUS_TOPIC, {"person": "someone"})
            else:
                publish_message(mqtt_client, TOPIC_PUBLISH, {"response": "no one"})
                publish_message(local_client, PERSON_STATUS_TOPIC, {"person": "no one"})

        elif cmd == "indoor climate":
            send_climate_data()


def send_climate_data():
    try:
        dht_sensor.measure()
        temperature = round(dht_sensor.temperature(), 2)
        humidity = round(dht_sensor.humidity(), 2)
        #AWS MQTT
        publish_message(mqtt_client, TOPIC_PUBLISH, {
            "temperature": "{:.2f}".format(temperature),
            "humidity": "{:.2f}".format(humidity)
        })
        #SNS
        publish_message(mqtt_client, TOPIC_TEMPERATURE, {
            "temperature": "{:.2f}".format(temperature)
        })
        #Assistant 
        publish_message(local_client, CLIMATE_STATUS_TOPIC, {
            "temperature": "{:.2f}".format(temperature),
            "humidity": "{:.2f}".format(humidity)
        })
        
    except OSError:
        publish_message(mqtt_client, CLIMATE_STATUS_TOPIC, {"error": "DHT error"})

# --- MQTT callback ---
def mqtt_callback(topic, message):
    try:
        msg_str = message.decode()
        handle_command(topic.decode(), msg_str)
    except Exception as e:
        print("MQTT callback error:", e)

# --- Local Mosquitto callback ---
def local_callback(topic, msg):
    print("Local MQTT msg:", topic.decode(), "=>", msg.decode())

# --- Main ---
connect_to_wifi()
mqtt_client = connect_iot_core(mqtt_callback)
local_client.set_callback(local_callback)
local_client.connect()

#subscibe topics
mqtt_client.subscribe(TOPIC_SUBSCRIBE)

local_client.subscribe(DOOR_COMMAND_TOPIC)
local_client.subscribe(LIGHT_COMMAND_TOPIC)
local_client.subscribe(PERSON_COMMAND_TOPIC)
local_client.subscribe(CLIMATE_COMMAND_TOPIC)

while True:
    mqtt_client.check_msg()
    local_client.check_msg()

 
    if time.ticks_diff(time.ticks_ms(), last_temp_publish) > 7000:
        send_climate_data()
        last_temp_publish = time.ticks_ms()

    time.sleep_ms(100)
