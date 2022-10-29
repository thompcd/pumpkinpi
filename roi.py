#!/usr/bin/env python

import sys, signal
sys.path.insert(0, "build/lib.linux-armv7l-2.7/")
from gpiozero import Servo, Device
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import VL53L1X
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

#use pigpio to reduce servo jitter
Device.pin_factory = PiGPIOFactory()

#time of flight sensor setup
tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
servo = Servo(4)
print("Python: Initialized")
tof.open()
print("Python: Opened")

# Left, right, top and bottom are relative to the SPAD matrix coordinates,
# which will be mirrored in real scene coordinates.
# (or even rotated, depending on the VM53L1X element alignment on the board and on the board position)
#
# ROI in SPAD matrix coords:
#
# 15  top-left
# |  X____
# |  |    |
# |  |____X
# |        bottom-right
# 0__________15
#

def scan(type="w"):
    if type == "w":
        # Wide scan forward ~30deg angle
        print("Scan: wide")
        return VL53L1X.VL53L1xUserRoi(0, 15, 15, 0)
    elif type == "c":
        # Focused scan forward
        print("Scan: center")
        return VL53L1X.VL53L1xUserRoi(6, 9, 9, 6)
    elif type == "t":
        # Focused scan top
        print("Scan: top")
        return VL53L1X.VL53L1xUserRoi(6, 15, 9, 12)
    elif type == "b":
        # Focused scan bottom
        print("Scan: bottom")
        return VL53L1X.VL53L1xUserRoi(6, 3, 9, 0)
    elif type == "l":
        # Focused scan left
        print("Scan: left")
        return VL53L1X.VL53L1xUserRoi(0, 9, 3, 6)
    elif type == "r":
        # Focused scan right
        print("Scan: right")
        return VL53L1X.VL53L1xUserRoi(12, 9, 15, 6)
    else:
        print("Scan: wide (default)")
        return VL53L1X.VL53L1xUserRoi(0, 15, 15, 0)

def laugh(duration):
    for x in range(duration):
        servo.value = 0.7
        time.sleep(0.2)
        servo.value = -0.7
        time.sleep(0.2)

def service_servo(inRange):
    if(inRange == True):
        print("laughing")
        #publish laugh on mqtt
        try:
            publish.single("porch/pumpkin1/laugh", payload=True, qos=0, retain=False, hostname="outpost.local", protocol=mqtt.MQTTv311)
        except:
            print("failed to publish mqtt message")
        laugh(3)
    else:
        print("out of range")

if len(sys.argv) == 2:
    roi = scan(sys.argv[1])
else:
    roi = scan("default")

tof.set_user_roi(roi)

tof.start_ranging(1)

def exit_handler(signal, frame):
    tof.stop_ranging()
    tof.close()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_handler)

while True:
    distance_mm = tof.get_distance()
    if distance_mm < 0:
        # Error -1185 may occur if you didn't stop ranging in a previous test
        print("Error: {}".format(distance_mm))
    elif distance_mm < 200:
        service_servo(False)
    else:
        service_servo(True)
    print("Distance: {}cm".format(distance_mm/10))
    time.sleep(0.5)
