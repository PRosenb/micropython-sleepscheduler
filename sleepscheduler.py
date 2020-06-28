import machine
import ujson
import utime


class Task:
    def __init__(self, moduleName, functionName, scheduledTicksMs):
        self.moduleName = moduleName
        self.functionName = functionName
        self.scheduledTicksMs = scheduledTicksMs

    def __str__(self):
        return self.__dict__


def obj_to_dict(obj):
    return obj.__dict__


tasks = []


def schedule_delayed_ms(moduleName, functionName, delayMs):
    scheduledTicksMs = utime.ticks_add(utime.ticks_ms(), delayMs)
    newTask = Task(moduleName, functionName, scheduledTicksMs)
    inserted = False
    for i in range(len(tasks)):
        task = tasks[i]
        if (task.scheduledTicksMs > scheduledTicksMs):
            tasks.insert(i, newTask)
            inserted = True
            break
    if not inserted:
        tasks.append(Task(moduleName, functionName, scheduledTicksMs))


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
                    task_dict["scheduledTicksMs"]
                )
            )


def print_tasks():
    for task in tasks:
        print(task.moduleName + "." + task.functionName +
              ": " + str(task.scheduledTicksMs))


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
            timeUntilFirstTaskMs = utime.ticks_diff(
                first_task.scheduledTicksMs, utime.ticks_ms())
            if timeUntilFirstTaskMs <= 0:
                execute_first_task()
            else:
                utime.sleep_ms(timeUntilFirstTaskMs)
        else:
            break


restore_from_rtc_memory()
