# Example usage of sleepscheduler
#
# To use this example, add the following code to main.py
# and put this file onto the ESP32.
#
# import sleepscheduler as sl
# import my_module
#
# sl.schedule_on_cold_boot(my_module.init_on_cold_boot)
# sl.run_forever()

import sleepscheduler as sl
import network
from ntptime import settime
import utime
from machine import Pin
import esp32


BUILD_IN_LED_PIN = 2


def init_on_cold_boot():
    # configure and connect WLAN
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("connecting to network")
        wlan.active(True)
        wlan.connect("yourSSID", "yourPassword")
        while not wlan.isconnected():
            print(".", end="")
            utime.sleep(1)
    print()
    print('network config:', wlan.ifconfig())

    # set the time from the network
    settime()
    print("time: {}".format(utime.localtime()))

    sl.schedule_next_full_minute(__name__, led_on_even_minute, 60)
    sl.schedule_next_full_minute(
        __name__, raw_temperature_every_30_seconds, 30)
    sl.schedule_next_full_minute(__name__, hall_sensor_every_15_seconds, 15)
    sl.schedule(__name__, print_every_day, 17, 17, 0, sl.SECONDS_PER_DAY)


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

    # Set and increment 'value' to limit how many times this function is executed.
    # 'value' is stored in the array sl.rtc_memory_bytes what is saved/restored
    # by sleepscheduler before/after deep sleep.
    if len(sl.rtc_memory_bytes) == 0:
        print("led_on_even_minute(): rtc_memory_bytes empty")
        value = 1
        sl.rtc_memory_bytes.extend(value.to_bytes(2, 'big'))
    else:
        value = int.from_bytes(sl.rtc_memory_bytes[0:2], 'big')
        value = value + 1
        sl.rtc_memory_bytes[0:2] = value.to_bytes(2, 'big')
        # stop executing led_on_even_minute() when 'value' reaches 3
        if value >= 3:
            print("finish led_on_even_minute()")
            sl.remove_all(__name__, led_on_even_minute)


def raw_temperature_every_30_seconds():
    print("raw_temperature_every_30_seconds: " + str(esp32.raw_temperature()))
    # sl.remove_all(__name__, raw_temperature_every_30_seconds)


def hall_sensor_every_15_seconds():
    print("hall_sensor_every_15_seconds: " + str(esp32.hall_sensor()))
    # sl.remove_all(__name__, hall_sensor_every_15_seconds)


def print_every_day():
    print("print_every_day(), time: {}".format(utime.localtime()))
    # sl.remove_all(__name__, hall_sensor_every_15_seconds)
