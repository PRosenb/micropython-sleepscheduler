# Example usage of sleepscheduler
#
# To use this example, add the following code to main.py
# and put this file onto the ESP32.
#
# import sleepscheduler as sl
# import sensors_every_minute
# sl.schedule_on_cold_boot(sensors_every_minute.init_on_cold_boot)
# sl.run_forever()

import sleepscheduler as sl
import utime
import esp32


def init_on_cold_boot():
    sl.schedule_immediately(__name__, sensor_every_minute, 60)


def sensor_every_minute():
    print("sensor_every_minute: {}ºC, hall sensor: {}".format(
        (esp32.raw_temperature() * 90 / 256 - 10), esp32.hall_sensor()))
