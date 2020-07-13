import sleepscheduler as sl
import my_module

sl.schedule_on_cold_boot(my_module.init_on_cold_boot)
sl.run_forever()
