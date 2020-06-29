import sleepscheduler as sl
import network
from ntptime import settime
import utime


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

    sl.schedule_at_sec("my_module", "scheduled_recurrently", utime.time(), 10)
    # sl.allow_deep_sleep = False


def scheduled_recurrently():
    print("scheduled_recurrently, time: " + str(utime.time()))
    print(utime.localtime())
    utime.sleep(2)
    # print("print_tasks:")
    # sl.print_tasks()
