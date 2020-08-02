# Example usage of sleepscheduler
#
# To use this example, add the following code to main.py
# and put this file onto the ESP32.
#
# import sleepscheduler as sl
# import execute_3_times
# sl.schedule_on_cold_boot(execute_3_times.init_on_cold_boot)
# sl.run_forever()

import sleepscheduler as sl
import utime


def init_on_cold_boot():
    sl.schedule_immediately(__name__, execute_3_times, 15)


def execute_3_times():
    print("--> execute_3_times(), time: {}".format(utime.time()))

    # Set and increment 'value' to limit how many times this function is executed.
    # 'value' is stored in the array sl.rtc_memory_bytes what is saved/restored
    # by sleepscheduler before/after deep sleep.
    if len(sl.rtc_memory_bytes) == 0:
        value = 1
        sl.rtc_memory_bytes.extend(value.to_bytes(2, 'big'))
    else:
        value = int.from_bytes(sl.rtc_memory_bytes[0:2], 'big')
        value = value + 1
        sl.rtc_memory_bytes[0:2] = value.to_bytes(2, 'big')
        # stop executing led_on_even_minute() when 'value' reaches 3
    print("value: {}".format(value))
    if value >= 3:
        print("finish execute_3_times()")
        sl.remove_all(__name__, execute_3_times)
