import machine
import ujson
import utime


class Task:
    def __init__(self, module_name, function_name, seconds_since_epoch, repeat_after_sec):
        self.module_name = module_name
        self.function_name = function_name
        self.seconds_since_epoch = seconds_since_epoch
        self.repeat_after_sec = repeat_after_sec

    def __str__(self):
        return self.__dict__


def obj_to_dict(obj):
    return obj.__dict__


initial_deep_sleep_delay_sec = 20
allow_deep_sleep = True
_start_seconds_since_epoch = utime.time()
_tasks = []


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
    newTask = Task(module_name, function_name, seconds_since_epoch, repeat_after_sec)
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


def store():
    mappedTasks = list(map(obj_to_dict, _tasks))
    tasks_json = ujson.dumps(mappedTasks)

    print("tasks_json: {}".format(tasks_json))
    rtc = machine.RTC()
    rtc.memory(bytes(tasks_json, 'utf-8'))


def restore_from_rtc_memory():
    print("sleepscheduler: restore from rtc memory")
    rtc = machine.RTC()
    tasks_json = str(rtc.memory(), 'utf-8')
    if tasks_json:
        print("tasks_json: {}".format(tasks_json))
        parsed_tasks = ujson.loads(tasks_json)
        for task_dict in parsed_tasks:
            _tasks.append(
                Task(
                    task_dict["module_name"],
                    task_dict["function_name"],
                    task_dict["seconds_since_epoch"],
                    task_dict["repeat_after_sec"]
                )
            )


def print_tasks():
    for task in _tasks:
        print(task.module_name + "." + task.function_name +
              ": " + str(task.seconds_since_epoch))


def deep_sleep_sec(durationSec):
    store()
    print("sleepscheduler: deepSleep for {} seconds".format(durationSec))
    machine.deepsleep(durationSec * 1000)


def execute_first_task():
    task = _tasks.pop(0)
    execute_task(task)


def execute_task(task):
    module = __import__(task.module_name)
    func = getattr(module, task.function_name)
    func()


def run_until_complete():
    run_tasks(False)
def run_forever():
    run_tasks(True)

def run_tasks(forever):
    while True:
        if _tasks:
            first_task = _tasks[0]
            time_until_first_task = first_task.seconds_since_epoch - utime.time()
            if time_until_first_task <= 0:
                execute_first_task()
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
                        remaining_no_deep_sleep_sec = (_start_seconds_since_epoch + initial_deep_sleep_delay_sec) - utime.time()
                        if (time_until_first_task - 1 > remaining_no_deep_sleep_sec):
                            # deep sleep prevention on cold boot
                            print("sleep({}) due to cold boot".format(remaining_no_deep_sleep_sec))
                            utime.sleep(remaining_no_deep_sleep_sec)
                        else:
                            print("sleep({}) due to cold boot".format(time_until_first_task - 1))
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
                machine.deepsleep()
            else:
                break


restore_from_rtc_memory()
