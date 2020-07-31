import sleepscheduler as sl
import utime


INITIAL_DEEP_SLEEP_DELAY = 20
set_on_cold_boot = False


def init_on_cold_boot():
    # test that a function with an exception it not scheduled anymore
    sl.schedule_immediately(__name__, function_div0, 10)

    global set_on_cold_boot
    set_on_cold_boot = True
    sl.schedule_delayed(__name__, check_no_deep_sleep,
                        INITIAL_DEEP_SLEEP_DELAY)
    # also test with function_name
    sl.schedule_delayed(__name__, "check_deep_sleep", 49)

    sl.schedule_immediately(__name__, every_14_seconds, 14)
    # also test with function_name
    sl.schedule_immediately(__name__, "every_29_seconds", 29)

    sl.schedule_next_full_minute(__name__, next_full_minute)
    # also test with function_name, will execute within the same second
    sl.schedule_next_full_minute(__name__, "next_full_minute")

    sl.schedule(__name__, at_hour_minutes_seconds, 0, 0, 17)
    sl.schedule(__name__, "at_hour_minutes_seconds_function_name", 0, 0, 18)

    sl.print_tasks()

    # finish and evaluate test in the end
    sl.schedule_delayed(__name__, finish_test, 61)


def function_div0():
    store_current_time()
    return 1/0


def check_no_deep_sleep():
    print("check_no_deep_sleep(), time: {}".format(utime.time()))
    if set_on_cold_boot:
        store_current_time()
    else:
        sl.remove_all_by_module_name(__name__)
        print("TEST_ERROR Deep sleep done within first '{}' seconds".format(
            INITIAL_DEEP_SLEEP_DELAY))


def check_deep_sleep():
    print("check_deep_sleep(), time: {}".format(utime.time()))
    if not set_on_cold_boot:
        store_current_time()
    else:
        sl.remove_all_by_module_name(__name__)
        print("TEST_ERROR Deep sleep not done")


def every_14_seconds():
    print("every_14_seconds(), time: {}".format(utime.time()))
    store_current_time()


def every_29_seconds():
    print("every_29_seconds(), time: {}".format(utime.time()))
    store_current_time()


def next_full_minute():
    print("next_full_minute(), time: {}".format(utime.time()))
    store_current_time()


def at_hour_minutes_seconds():
    print("at_hour_minutes_seconds(), time: {}".format(utime.time()))
    store_current_time()


def at_hour_minutes_seconds_function_name():
    print("at_hour_minutes_seconds(), time: {}".format(utime.time()))
    store_current_time()


def finish_test():
    print("finish_test(), time: {}".format(utime.time()))
    # test removal with function and function_name
    sl.remove_all(__name__, every_14_seconds)
    sl.remove_all(__name__, "every_29_seconds")

    # also test other remove functions with adding a task back
    # remove_all_by_function_name() with function and function_name
    sl.schedule_immediately(__name__, every_14_seconds, 14)
    sl.remove_all_by_function_name(every_14_seconds)
    sl.schedule_immediately(__name__, every_14_seconds, 14)
    sl.remove_all_by_function_name("every_14_seconds")
    # remove_all_by_module_name()
    sl.schedule_immediately(__name__, every_14_seconds, 14)
    sl.remove_all_by_module_name(__name__)

    expected = [0, 0, 0, 14, 17, 18,
                INITIAL_DEEP_SLEEP_DELAY, 28, 29, 42, 49, 56, 58, 60, 60]
    results = []

    index = 0
    while index < len(sl.rtc_memory_bytes):
        result = int.from_bytes(sl.rtc_memory_bytes[index:index + 4], 'big')
        results.append(result)
        index = index + 4

    failure = False
    if len(expected) == len(results):
        for i in range(len(expected)):
            if expected[i] != results[i]:
                failure = True
                print("TEST_ERROR wrong value at index '{}',' expected '{}', was '{}'".format(
                    i, expected[i], results[i]))
    else:
        print("TEST_ERROR Wrong amount of results. Expected '{}', was '{}'".format(
            len(expected), len(results)))
        expected_str = ""
        for i in range(len(expected)):
            expected_str = expected_str + str(expected[i]) + " "
        print("expected: {}".format(expected_str))
        results_str = ""
        for i in range(len(results)):
            results_str = results_str + str(results[i]) + " "
        print("results: {}".format(results_str))
        failure = True

    if not failure:
        print("TEST_SUCCESS")


def store_current_time():
    bytes = utime.time().to_bytes(4, 'big')
    sl.rtc_memory_bytes = sl.rtc_memory_bytes + bytes
