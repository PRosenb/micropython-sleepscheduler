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


tasks = []


def schedule_on_cold_boot(moduleName, functionName):
    if not machine.wake_reason() is machine.DEEPSLEEP_RESET:
        print("on_cold_boot")
        module = __import__(moduleName)
        func = getattr(module, functionName)
        func()


def schedule_at_sec(moduleName, functionName, secondsSinceEpoch, repeatAfterSec=0):
    newTask = Task(moduleName, functionName, secondsSinceEpoch, repeatAfterSec)
    inserted = False
    for i in range(len(tasks)):
        task = tasks[i]
        if (task.secondsSinceEpoch > secondsSinceEpoch):
            tasks.insert(i, newTask)
            inserted = True
            break
    if not inserted:
        tasks.append(Task(moduleName, functionName,
                          secondsSinceEpoch, repeatAfterSec))


def store():
    mappedTasks = list(map(obj_to_dict, tasks))
    state = ujson.dumps(mappedTasks)

    print("state: {}".format(state))
    rtc = machine.RTC()
    rtc.memory(bytes(state, 'utf-8'))


def restore_from_rtc_memory():
    print("sleepscheduler: restore from rtc memory")
    rtc = machine.RTC()
    state = str(rtc.memory(), 'utf-8')
    if state:
        print("state: {}".format(state))
        parsed = ujson.loads(state)
        for task_dict in parsed:
            print(task_dict["functionName"])
            tasks.append(
                Task(
                    task_dict["moduleName"],
                    task_dict["functionName"],
                    task_dict["secondsSinceEpoch"],
                    task_dict["repeatAfterSec"]
                )
            )


def print_tasks():
    for task in tasks:
        print(task.moduleName + "." + task.functionName +
              ": " + str(task.secondsSinceEpoch))


def sleep():
    store()
    durationSeconds = 3
    print("sleepscheduler: sleep for {} seconds".format(durationSeconds))
    machine.deepsleep(durationSeconds * 1000)


def execute_first_task():
    task = tasks.pop(0)
    execute_task(task)


def execute_task(task):
    module = __import__(task.moduleName)
    func = getattr(module, task.functionName)
    func()


def run_forever():
    print("run_forever()")
    while True:
        if tasks:
            first_task = tasks[0]
            timeUntilFirstTask = first_task.secondsSinceEpoch - utime.time()
            if timeUntilFirstTask <= 0:
                execute_first_task()
                if first_task.repeatAfterSec != 0:
                    schedule_at_sec(
                        first_task.moduleName,
                        first_task.functionName,
                        first_task.secondsSinceEpoch + first_task.repeatAfterSec,
                        first_task.repeatAfterSec
                    )
            else:
                utime.sleep_ms(timeUntilFirstTask)
        else:
            break


restore_from_rtc_memory()
