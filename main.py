# Execute the tests
###################
import sleepscheduler as sl
import test
sl.schedule_on_cold_boot(test.init_on_cold_boot)
sl.run_until_complete()

# Examples
###########
# import sleepscheduler as sl

# import execute_3_times
# sl.schedule_on_cold_boot(execute_3_times.init_on_cold_boot)

# import led_on_even_minute
# sl.schedule_on_cold_boot(led_on_even_minute.init_on_cold_boot)

# import sensors_every_minute
# sl.schedule_on_cold_boot(sensors_every_minute.init_on_cold_boot)

# import temp_diff
# sl.schedule_on_cold_boot(temp_diff.init_on_cold_boot)

# sl.run_forever()
