import machine
import ujson
import utime


class Task:
    def __init__(self, moduleName, functionName, secondsSinceEpoch, repeatAfterSec):
        self.moduleName = moduleName
        self.functionName = functionName
        self.secondsSinceEpoch = secondsSinceEpoch
        self.repeatAfterSec = repeatAfterSec

    def __str__(self):
        return self.__dict__


def obj_to_dict(obj):
    return obj.__dict__


initial_deep_sleep_delay_sec = 20
allow_deep_sleep = True
_start_seconds_since_epoch = utime.time()
_tasks = []


def schedule_on_cold_boot(moduleName, functionName):
    global _start_seconds_since_epoch
    if not machine.wake_reason() is machine.DEEPSLEEP_RESET:
        print("on_cold_boot")
        module = __import__(moduleName)
        func = getattr(module, functionName)
        func()
        # set _start_seconds_since_epoch in case func() set the time
        _start_seconds_since_epoch = utime.time()


def schedule_at_sec(moduleName, functionName, secondsSinceEpoch, repeatAfterSec=0):
    newTask = Task(moduleName, functionName, secondsSinceEpoch, repeatAfterSec)
    inserted = False
    for i in range(len(_tasks)):
        task = _tasks[i]
        if (task.secondsSinceEpoch > secondsSinceEpoch):
            _tasks.insert(i, newTask)
            inserted = True
            break
    if not inserted:
        _tasks.append(Task(moduleName, functionName,
                           secondsSinceEpoch, repeatAfterSec))


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
                    task_dict["moduleName"],
                    task_dict["functionName"],
                    task_dict["secondsSinceEpoch"],
                    task_dict["repeatAfterSec"]
                )
            )


def print_tasks():
    for task in _tasks:
        print(task.moduleName + "." + task.functionName +
              ": " + str(task.secondsSinceEpoch))


def deep_sleep_sec(durationSec):
    store()
    print("sleepscheduler: deepSleep for {} seconds".format(durationSec))
    machine.deepsleep(durationSec * 1000)


def execute_first_task():
    task = _tasks.pop(0)
    execute_task(task)


def execute_task(task):
    module = __import__(task.moduleName)
    func = getattr(module, task.functionName)
    func()


def run_forever():
    print("run_forever()")
    while True:
        if _tasks:
            first_task = _tasks[0]
            time_until_first_task = first_task.secondsSinceEpoch - utime.time()
            if time_until_first_task <= 0:
                execute_first_task()
                if first_task.repeatAfterSec != 0:
                    schedule_at_sec(
                        first_task.moduleName,
                        first_task.functionName,
                        first_task.secondsSinceEpoch + first_task.repeatAfterSec,
                        first_task.repeatAfterSec
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
                        first_task_secondsSinceEpoch = first_task.secondsSinceEpoch
                        while first_task_secondsSinceEpoch - utime.time() > 0:
                            utime.sleep_ms(1)
        else:
            break


restore_from_rtc_memory()
