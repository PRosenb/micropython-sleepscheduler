import sleepscheduler as sl
import utime


def init_on_cold_boot():
    sl.schedule_at_sec("my_module", "scheduled_recurrently", 0)


def scheduled_recurrently():
    sl.schedule_at_sec("my_module", "scheduled_recurrently", utime.time() + 10)
    print("time: " + str(utime.time()))
    print("print_tasks:")
    sl.print_tasks()
