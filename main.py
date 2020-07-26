# Execute the tests
import sleepscheduler as sl
import test

sl.schedule_on_cold_boot(test.init_on_cold_boot)
sl.run_until_complete()
