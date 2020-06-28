import sleepscheduler as sl
import utime


def init_on_cold_boot():
    sl.schedule_at_sec("my_module", "scheduled_recurrently", 0, 10)


def scheduled_recurrently():
    print("scheduled_recurrently, time: " + str(utime.time()))
    utime.sleep(2)
    print("print_tasks:")
    sl.print_tasks()
