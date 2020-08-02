# Example usage of sleepscheduler
#
# To use this example, add the following code to main.py
# and put this file onto the ESP32.
#
# import sleepscheduler as sl
# import temp_diff
# sl.schedule_on_cold_boot(temp_diff.init_on_cold_boot)
# sl.run_forever()

import sleepscheduler as sl
import network
import utime
from machine import Pin
import dht
import urequests
import ujson


WIFI_SSID = "yourSSID"
WIFI_PASSWORD = "yourWifiPassword"
BUILD_IN_LED_PIN = 2
DHT_DATA_PIN = 4
# openweathermap constants
APP_ID = "yourOpenWeatherMapToken"
CITY = "Affoltern am Albis"
URL = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid={}"
on_cold_boot = False


def init_on_cold_boot():
    sl.schedule_immediately(__name__, check_temp, sl.SECONDS_PER_MINUTE * 10)
    global on_cold_boot
    on_cold_boot = True


def check_temp():
    # configure and connect WLAN
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

    inside_temp = read_dht_temp()
    outside_temp = get_outside_temp()
    print("inside: {}ºC, outside: {}ºC".format(inside_temp, outside_temp))
    if outside_temp <= inside_temp and outside_temp >= inside_temp - 1:
        switch_led(True)
    else:
        if on_cold_boot and outside_temp < inside_temp:
            # switch the LED on for 10 secs show that the windows can be opened
            switch_led(True)
            sl.schedule_delayed(__name__, switch_led_off, 10)
        else:
            switch_led(False)


def switch_led_off():
    switch_led(False)


def read_dht_temp():
    try:
        d = dht.DHT22(Pin(DHT_DATA_PIN))
        d.measure()
        return d.temperature()
    except OSError as e:
        print("ERROR: OSError: AM2303/DHT22 not connected?")
        raise e


def get_outside_temp():
    # connect Wifi
    # import upip
    # upip.install('urequests')
    response = urequests.get(URL.format(CITY, APP_ID))
    parsed = ujson.loads(response.text)
    response.close()
    return parsed["main"]["temp"]


def switch_led(led_on):
    led_pin = Pin(BUILD_IN_LED_PIN, Pin.OUT)
    # disable pin hold to allow to change it
    led_pin.init(Pin.OUT, pull=None)
    if led_on:
        led_pin.on()
    else:
        led_pin.off()
    # enable pin hold to keep the output state during deep sleep
    led_pin.init(Pin.OUT, pull=Pin.PULL_HOLD)
