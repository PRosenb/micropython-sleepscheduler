import machine
import utime


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
# Module variables
# -------------------------------------------------------------------------------------------------
initial_deep_sleep_delay_sec = 20
allow_deep_sleep = True
_start_seconds_since_epoch = utime.time()
_tasks = []


# -------------------------------------------------------------------------------------------------
# Encoding/Decoding
# -------------------------------------------------------------------------------------------------
def encode_task(task):
    bytes = task.module_name.encode() + "\0" + task.function_name.encode() + "\0" + \
        task.seconds_since_epoch.to_bytes(
            4, 'big') + task.repeat_after_sec.to_bytes(4, 'big')
    return bytes


def decode_task(bytes, start_index, tasks):
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


def encode_tasks():
    bytes = len(_tasks).to_bytes(4, 'big')
    for task in _tasks:
        task_bytes = encode_task(task)
        bytes = bytes + task_bytes
    # print(bytes)
    return bytes


def decode_tasks(bytes):
    task_count = int.from_bytes(bytes[0:4], 'big')

    tasks = list()
    start_index = 4
    for _ in range(0, task_count):
        start_index = decode_task(bytes, start_index, tasks)

    global _tasks
    _tasks = tasks


# -------------------------------------------------------------------------------------------------
# Public functions
# -------------------------------------------------------------------------------------------------
def schedule_on_cold_boot(module_name, function_name):
    global _start_seconds_since_epoch
    if not machine.wake_reason() is machine.DEEPSLEEP_RESET:
        print("on_cold_boot")
        module = __import__(module_name)
        func = getattr(module, function_name)
        func()
        # set _start_seconds_since_epoch in case func() set the time
        _start_seconds_since_epoch = utime.time()


def schedule_at_sec(module_name, function_name, seconds_since_epoch, repeat_after_sec=0):
    newTask = Task(module_name, function_name,
                   seconds_since_epoch, repeat_after_sec)
    inserted = False
    for i in range(len(_tasks)):
        task = _tasks[i]
        if (task.seconds_since_epoch > seconds_since_epoch):
            _tasks.insert(i, newTask)
            inserted = True
            break
    if not inserted:
        _tasks.append(Task(module_name, function_name,
                           seconds_since_epoch, repeat_after_sec))


def run_until_complete():
    run_tasks(False)


def run_forever():
    run_tasks(True)


def print_tasks():
    for task in _tasks:
        print("{ \"module_name\": \"" + task.module_name + "\", \"function_name\": \"" + task.function_name +
              "\", \"seconds_since_epoch\": " + str(task.seconds_since_epoch) + ", \"repeat_after_sec\": " + str(task.repeat_after_sec) + "}")


# -------------------------------------------------------------------------------------------------
# Store/Restore to/from RTC-Memory
# -------------------------------------------------------------------------------------------------
def store():
    bytes = encode_tasks()
    rtc = machine.RTC()
    rtc.memory(bytes)


def restore_from_rtc_memory():
    print("sleepscheduler: restore from rtc memory")
    rtc = machine.RTC()
    bytes = rtc.memory()
    decode_tasks(bytes)
    print_tasks()


# -------------------------------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------------------------------
def deep_sleep_sec(durationSec):
    store()
    print("sleepscheduler: deepSleep for {} seconds".format(durationSec))
    machine.deepsleep(durationSec * 1000)


def execute_first_task():
    task = _tasks.pop(0)
    return execute_task(task)


def execute_task(task):
    try:
        module = __import__(task.module_name)
        func = getattr(module, task.function_name)
        func()
        return True
    except ImportError:
        print("ERROR: Cannot schedule task, module '{}' not found.".format(task.module_name))
    except AttributeError:
        print("ERROR: Cannot schedule task, function '{}' not found in module '{}'.".format(task.function_name, task.module_name))
    except SyntaxError:
        print("ERROR: Task of function '{}' in module '{}' failed due to syntax error.".format(task.function_name, task.module_name))
    except BaseException as e:
        print("ERROR: Task of function '{}' in module '{}' failed due to '{}'".format(task.function_name, task.module_name, e))
    except:
        print("ERROR: Task of function '{}' in module '{}' failed due to unknown failure in function.".format(task.function_name, task.module_name))
    return False

def run_tasks(forever):
    while True:
        if _tasks:
            first_task = _tasks[0]
            time_until_first_task = first_task.seconds_since_epoch - utime.time()
            if time_until_first_task <= 0:
                successful = execute_first_task()
                if successful:
                    if first_task.repeat_after_sec != 0:
                        schedule_at_sec(
                            first_task.module_name,
                            first_task.function_name,
                            first_task.seconds_since_epoch + first_task.repeat_after_sec,
                            first_task.repeat_after_sec
                        )
            else:
                if allow_deep_sleep and time_until_first_task > 1:
                    if (not machine.wake_reason() == machine.DEEPSLEEP_RESET
                            and utime.time() < _start_seconds_since_epoch + initial_deep_sleep_delay_sec):
                        # initial deep sleep delay
                        remaining_no_deep_sleep_sec = (
                            _start_seconds_since_epoch + initial_deep_sleep_delay_sec) - utime.time()
                        if (time_until_first_task - 1 > remaining_no_deep_sleep_sec):
                            # deep sleep prevention on cold boot
                            print("sleep({}) due to cold boot".format(
                                remaining_no_deep_sleep_sec))
                            utime.sleep(remaining_no_deep_sleep_sec)
                        else:
                            print("sleep({}) due to cold boot".format(
                                time_until_first_task - 1))
                            utime.sleep(time_until_first_task - 1)
                    else:
                        deep_sleep_sec(time_until_first_task - 1)
                else:
                    if time_until_first_task > 1:
                        print("sleep({})".format(time_until_first_task - 1))
                        utime.sleep(time_until_first_task - 1)
                    else:
                        first_task_seconds_since_epoch = first_task.seconds_since_epoch
                        while first_task_seconds_since_epoch - utime.time() > 0:
                            utime.sleep_ms(1)
        else:
            if forever:
                # deep sleep until an external interrupt occurs (if configured)
                store()
                machine.deepsleep()
            else:
                break


# -------------------------------------------------------------------------------------------------
# Init
# -------------------------------------------------------------------------------------------------
restore_from_rtc_memory()
