#!/usr/bin/env python

import sys, signal
sys.path.insert(0, "build/lib.linux-armv7l-2.7/")
from gpiozero import Servo, Device
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

#use pigpio to reduce servo jitter
Device.pin_factory = PiGPIOFactory()

servo = Servo(18)
print("Python: Initialized")

def laugh(duration):
    global laughing
    try:
        laughing = True
        for x in range(duration):
            servo.value = 0.7
            time.sleep(0.2)
            servo.value = -0.7
            time.sleep(0.2)
    finally:
        laughing = False

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("porch/+/laugh")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    laugh(8)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("outpost.local")

def exit_handler(signal, frame):
    client.loop_stop()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_handler)
client.loop_forever()
