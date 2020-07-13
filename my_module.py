import sleepscheduler as sl
import network
from ntptime import settime
import utime
from machine import Pin
import esp32


BUILD_IN_LED_PIN = 2


def init_on_cold_boot():
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
    settime()
    print(utime.localtime())

    first_schedule_time = list(utime.localtime())
    # the time will be in the past so the function is scheduled immeditelly
    # and then again after repeatAfterSec from the time it was supposed to be scheduled (seconds 0)
    first_schedule_time[5] = 0  # seconds
    sl.schedule_at_sec(__name__, led_on_even_minute,
                       utime.mktime(first_schedule_time), 60)
    sl.schedule_at_sec(__name__, raw_temperature_every_half_a_minute,
                       utime.mktime(first_schedule_time), 30)
    sl.schedule_at_sec(__name__, hall_sensor_every_15_seconds,
                       utime.mktime(first_schedule_time), 15)


def function_div0():
    return 1/0


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

    if len(sl.rtc_memory_bytes) == 0:
        print("led_on_even_minute(): rtc_memory_bytes empty")
        value = 1
        sl.rtc_memory_bytes.extend(value.to_bytes(2, 'big'))
    else:
        value = int.from_bytes(sl.rtc_memory_bytes[0:2], 'big')
        if value == 1:
            print("finish led_on_even_minute()")
            sl.remove_all(__name__, led_on_even_minute)


def raw_temperature_every_half_a_minute():
    print("raw_temperature: " + str(esp32.raw_temperature()))
    # sl.remove_all(__name__, raw_temperature_every_half_a_minute)


def hall_sensor_every_15_seconds():
    print("hall_sensor: " + str(esp32.hall_sensor()))
    # sl.remove_all(__name__, hall_sensor_every_15_seconds)
