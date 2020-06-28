import sleepscheduler as sl
import utime


def scheduled_recurrently():
    sl.schedule_delayed_ms("my_module", "scheduled_recurrently", 30000)
    print("ticks: " + str(utime.ticks_ms()))
    print("print_tasks:")
    sl.print_tasks()
