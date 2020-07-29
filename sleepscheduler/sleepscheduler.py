import machine
import utime


# -------------------------------------------------------------------------------------------------
# Module variables
# -------------------------------------------------------------------------------------------------
initial_deep_sleep_delay_sec = 20
"""Prevents deep sleep within the given amount of seconds after the CPU started from 
hard reset. This gives the user time to press ctrl+c to stop sleepscheduler and e.g. 
upload new files."""
allow_deep_sleep = True
"""Controls if deep sleep is done or not."""
rtc_memory_bytes = bytearray()
"""This library uses machine.RTC().memory() to store the list of tasks while the CPU is in deep sleep.
When a task stores some data there too, it will be overwritten by sleepscheduler.
A task can put data to rtc_memory_bytes instead and sleepscheduler will store and restore
that data before and after deep sleep."""

# private variables
_start_seconds_since_epoch = utime.time()
_tasks = []


# -------------------------------------------------------------------------------------------------
# Public functions
# -------------------------------------------------------------------------------------------------
def schedule_on_cold_boot(function):
    global _start_seconds_since_epoch
    if not machine.wake_reason() is machine.DEEPSLEEP_RESET:
        print("sleepscheduler: schedule_on_cold_boot()")
        function()
        # set _start_seconds_since_epoch in case func() set the time
        _start_seconds_since_epoch = utime.time()


def schedule_at_sec(module_name, function, seconds_since_epoch, repeat_after_sec=0):
    """Schedule a function at seconds since Epoch.

    Schedule the `function` at `seconds_since_epoch` since Unix Epoch in seconds.

    Args:
        module_name (str): Module where the function is defined
        function (callable/str): Function to be called. Can either be a function of a string with the fuction name
        seconds_since_epoch (int): Seconds since Epoch when the function is executed
        repeat_after_sec (int): Repeat the function every given seconds
    Returns:
        None
    """
    if callable(function):
        function_name = function.__name__
    else:
        function_name = function
    new_task = Task(module_name, function_name,
                    seconds_since_epoch, repeat_after_sec)
    inserted = False
    for i in range(len(_tasks)):
        task = _tasks[i]
        if (task.seconds_since_epoch > seconds_since_epoch):
            _tasks.insert(i, new_task)
            inserted = True
            break
    if not inserted:
        _tasks.append(new_task)


def schedule_immediately(module_name, function, repeat_after_sec=0):
    """Schedule a function as soon as possible.

    Args:
        module_name (str): Module where the function is defined
        function (callable/str): Function to be called. Can either be a function of a string with the fuction name
        repeat_after_sec (int): Repeat the function every given seconds
    Returns:
        None
    """
    schedule_at_sec(module_name, function, utime.time(), repeat_after_sec)


def schedule_next_full_minute(module_name, function, repeat_after_sec=0):
    """Schedule a function at the next full minute.

    Args:
        module_name (str): Module where the function is defined
        function (callable/str): Function to be called. Can either be a function of a string with the fuction name
        repeat_after_sec (int): Repeat the function every given seconds afterwards
    Returns:
        None
    """
    local_time = list(utime.localtime())
    # set back to the minute just passed
    local_time[5] = 0  # seconds
    epoch_time = utime.mktime(local_time)
    # increment to the next full minute
    epoch_time = epoch_time + 60
    schedule_at_sec(module_name, function, epoch_time, repeat_after_sec)


def schedule_next_full_hour(module_name, function, repeat_after_sec=0):
    """Schedule a function at the next full hour.

    Args:
        module_name (str): Module where the function is defined
        function (callable/str): Function to be called. Can either be a function of a string with the fuction name
        repeat_after_sec (int): Repeat the function every given seconds afterwards
    Returns:
        None
    """
    local_time = list(utime.localtime())
    # set back to the hour just passed
    local_time[4] = 0  # minutes
    epoch_time = utime.mktime(local_time)
    # increment to the next full hour
    epoch_time = epoch_time + 3600
    schedule_at_sec(module_name, function, epoch_time, repeat_after_sec)


def remove_all(module_name, function):
    """Removes all given functions of module `module_name`.

    Args:
        module_name (str): Module where the function is defined
        function (callable/str): Function to be removed. Can either be a function of a string with the fuction name
    Returns:
        None
    """
    if callable(function):
        function_name = function.__name__
    else:
        function_name = function
    global _tasks
    temp_tasks = []
    for task in _tasks:
        if task.function_name != function_name or task.module_name != module_name:
            temp_tasks.append(task)
    _tasks = temp_tasks


def remove_all_by_function_name(function):
    """Remove all given functions.

    Args:
        function (callable/str): Function to be removed. Can either be a function of a string with the fuction name
    Returns:
        None
    """
    if callable(function):
        function_name = function.__name__
    else:
        function_name = function
    global _tasks
    temp_tasks = []
    for task in _tasks:
        if task.function_name != function_name:
            temp_tasks.append(task)
    _tasks = temp_tasks


def remove_all_by_module_name(module_name):
    """Removes all functions of module `module_name`.

    Args:
        module_name (str): Module where the function is defined
    Returns:
        None
    """
    global _tasks
    temp_tasks = []
    for task in _tasks:
        if task.module_name != module_name:
            temp_tasks.append(task)
    _tasks = temp_tasks


def run_until_complete():
    """Run the scheduler until all scheduled and repeated tasks are finished.

    Args:
        None
    Returns:
        None
    """
    _run_tasks(False)


def run_forever():
    """Run the scheduler until the CPU performs a hard reset.

    Args:
        None
    Returns:
        Will not return
    """
    _run_tasks(True)


def print_tasks():
    """Prints all scheduled tasks. For debug purpose only.

    Args:
        None
    Returns:
        None
    """
    for task in _tasks:
        print("sleepscheduler: print_tasks() { \"module_name\": \"" + task.module_name + "\", \"function_name\": \"" + task.function_name +
              "\", \"seconds_since_epoch\": " + str(task.seconds_since_epoch) + ", \"repeat_after_sec\": " + str(task.repeat_after_sec) + "}")


# -------------------------------------------------------------------------------------------------
# Definitions
# -------------------------------------------------------------------------------------------------
class Task:
    def __init__(self, module_name, function_name, seconds_since_epoch, repeat_after_sec):
        self.module_name = module_name
        self.function_name = function_name
        self.seconds_since_epoch = seconds_since_epoch
        self.repeat_after_sec = repeat_after_sec

    def __str__(self):
        return self.__dict__


# -------------------------------------------------------------------------------------------------
# Encoding/Decoding
# -------------------------------------------------------------------------------------------------
def _encode_task(task):
    bytes = task.module_name.encode() + "\0" + task.function_name.encode() + "\0" + \
        task.seconds_since_epoch.to_bytes(
            4, 'big') + task.repeat_after_sec.to_bytes(4, 'big')
    return bytes


def _decode_task(bytes, start_index, tasks):
    for i in range(start_index, len(bytes)):
        if bytes[i] == 0:
            module_name = bytes[start_index:i].decode()
            end_index = i + 1  # +1 for \0
            break

    start_index = end_index
    for i in range(start_index, len(bytes)):
        if bytes[i] == 0:
            function_name = bytes[start_index:i].decode()
            end_index = i + 1  # +1 for \0
            break

    start_index = end_index
    end_index = start_index + 4
    seconds_since_epoch = int.from_bytes(bytes[start_index:end_index], 'big')

    start_index = end_index
    end_index = start_index + 4
    repeat_after_sec = int.from_bytes(bytes[start_index:end_index], 'big')

    task = Task(module_name, function_name,
                seconds_since_epoch, repeat_after_sec)
    tasks.append(task)
    return end_index


def _encode_tasks():
    bytes = len(_tasks).to_bytes(4, 'big')
    for task in _tasks:
        task_bytes = _encode_task(task)
        bytes = bytes + task_bytes

    # add potential rtc_memory_bytes
    try:
        bytes = bytes + rtc_memory_bytes
    except TypeError as e:
        print("sleepscheduler: ERROR: Cannot store rtc_memory_bytes to RTC memory due to '{}'".format(e))

    # print(bytes)
    return bytes


def _decode_tasks(bytes):
    task_count = int.from_bytes(bytes[0:4], 'big')

    tasks = list()
    start_index = 4
    for _ in range(0, task_count):
        start_index = _decode_task(bytes, start_index, tasks)

    global _tasks
    _tasks = tasks

    # restore potential rtc_memory_bytes
    global rtc_memory_bytes
    rtc_memory_bytes = bytearray(bytes[start_index:len(bytes)])


# -------------------------------------------------------------------------------------------------
# Store/Restore to/from RTC-Memory
# -------------------------------------------------------------------------------------------------
def _store():
    bytes = _encode_tasks()
    rtc = machine.RTC()
    rtc.memory(bytes)


def _restore_from_rtc_memory():
    print("sleepscheduler: Restore from rtc memory")
    rtc = machine.RTC()
    bytes = rtc.memory()
    _decode_tasks(bytes)
    print_tasks()


# -------------------------------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------------------------------
def _deep_sleep_sec(durationSec):
    _store()
    print("sleepscheduler: Deep sleep for {} seconds".format(durationSec))
    machine.deepsleep(durationSec * 1000)


def _execute_task(task):
    try:
        module = __import__(task.module_name)
        func = getattr(module, task.function_name)
        func()
        return True
    except ImportError:
        print("sleepscheduler: ERROR: Cannot schedule task, module '{}' not found.".format(
            task.module_name))
    except AttributeError:
        print("sleepscheduler: ERROR: Cannot schedule task, function '{}' not found in module '{}'.".format(
            task.function_name, task.module_name))
    except SyntaxError:
        print("sleepscheduler: ERROR: Task of function '{}' in module '{}' failed due to syntax error.".format(
            task.function_name, task.module_name))
    except BaseException as e:
        print("sleepscheduler: ERROR: Task of function '{}' in module '{}' failed due to '{}'".format(
            task.function_name, task.module_name, e))
    except:
        print("sleepscheduler: ERROR: Task of function '{}' in module '{}' failed due to unknown failure in function.".format(
            task.function_name, task.module_name))
    return False


def _run_tasks(forever):
    while True:
        if _tasks:
            first_task = _tasks[0]
            time_until_first_task = first_task.seconds_since_epoch - utime.time()
            if time_until_first_task <= 0:
                # remove the first task from the list
                _tasks.pop(0)
                # Schedule the task at the next execution time if it is a repeating task.
                # This needs to be done before executing the task so that it can remove itself
                # from the scheduled tasks if it wants to.
                if first_task.repeat_after_sec != 0:
                    schedule_at_sec(
                        first_task.module_name,
                        first_task.function_name,
                        first_task.seconds_since_epoch + first_task.repeat_after_sec,
                        first_task.repeat_after_sec
                    )
                successful = _execute_task(first_task)
                if not successful and first_task.repeat_after_sec != 0:
                    # the task was added already so on failure we remove it
                    remove_all(first_task.module_name,
                               first_task.function_name)
            else:
                # - 1 below is to wake up one second before the task executes
                if allow_deep_sleep and time_until_first_task > 1:
                    if (not machine.wake_reason() == machine.DEEPSLEEP_RESET
                            and utime.time() < _start_seconds_since_epoch + initial_deep_sleep_delay_sec):
                        # initial deep sleep delay
                        remaining_no_deep_sleep_sec = (
                            _start_seconds_since_epoch + initial_deep_sleep_delay_sec) - utime.time()
                        if (time_until_first_task - 1 > remaining_no_deep_sleep_sec):
                            # deep sleep prevention on cold boot
                            print("sleepscheduler: sleep({}) due to cold boot".format(
                                remaining_no_deep_sleep_sec))
                            utime.sleep(remaining_no_deep_sleep_sec)
                        else:
                            print("sleepscheduler: sleep({}) due to cold boot".format(
                                time_until_first_task - 1))
                            utime.sleep(time_until_first_task - 1)
                    else:
                        _deep_sleep_sec(time_until_first_task - 1)
                else:
                    if time_until_first_task > 1:
                        print("sleepscheduler: sleep({})".format(
                            time_until_first_task - 1))
                        utime.sleep(time_until_first_task - 1)
                    else:
                        # wait in ms to execute the task when the next second starts
                        first_task_seconds_since_epoch = first_task.seconds_since_epoch
                        while first_task_seconds_since_epoch - utime.time() > 0:
                            utime.sleep_ms(1)
        else:
            if forever:
                # deep sleep until an external interrupt occurs (if configured)
                _store()
                print("sleepscheduler: Deep sleep infinitely")
                machine.deepsleep()
            else:
                print("sleepscheduler: All tasks finished, exiting sleepscheduler.")
                break


# -------------------------------------------------------------------------------------------------
# Init
# -------------------------------------------------------------------------------------------------
_restore_from_rtc_memory()
