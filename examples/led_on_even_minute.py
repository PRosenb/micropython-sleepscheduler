# Example usage of sleepscheduler
#
# To use this example, add the following code to main.py
# and put this file onto the ESP32.
#
# import sleepscheduler as sl
# import led_on_even_minute
# sl.schedule_on_cold_boot(led_on_even_minute.init_on_cold_boot)
# sl.run_forever()

import sleepscheduler as sl
import network
from ntptime import settime
import utime
from machine import Pin


BUILD_IN_LED_PIN = 2
WIFI_SSID = "yourSSID"
WIFI_PASSWORD = "yourWifiPassword"


def init_on_cold_boot():
    # configure and connect WLAN
    # the time is kept during deep sleep
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("connecting to network")
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            print(".", end="")
            utime.sleep(1)
    print()
    print('network config:', wlan.ifconfig())

    # set the time from the network
    settime()
    print("time: {}".format(utime.localtime()))

    sl.schedule_next_full_minute(__name__, led_on_even_minute, 60)


def led_on_even_minute():
    print("led_on_even_minute(), time: {}".format(utime.localtime()))

    led_pin = Pin(BUILD_IN_LED_PIN, Pin.OUT)
    # disable pin hold to allow to change it
    led_pin.init(Pin.OUT, pull=None)
    if utime.localtime()[4] % 2 == 0:
        led_pin.on()
    else:
        led_pin.off()
    # enable pin hold to keep the output state during deep sleep
    led_pin.init(Pin.OUT, pull=Pin.PULL_HOLD)
