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
    sl.schedule_at_sec("my_module", "scheduled_recurrently",
                       utime.mktime(first_schedule_time), 60)


def scheduled_recurrently():
    print("scheduled_recurrently(), time: {}".format(utime.localtime()))

    led_pin = Pin(BUILD_IN_LED_PIN, Pin.OUT)
    esp32.rtc_gpio_hold_dis(led_pin)
    if utime.localtime()[4] % 2 == 0:
        led_pin.on()
    else:
        led_pin.off()
    esp32.rtc_gpio_hold_en(led_pin)
