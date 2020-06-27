import machine
import ujson


class Task:
    def __init__(self, scheduledUptimeMillis, functionName):
        self.scheduledUptimeMillis = scheduledUptimeMillis
        self.functionName = functionName

    def __str__(self):
        return self.__dict__


def obj_to_dict(obj):
    return obj.__dict__


tasks = []


def add_task(functionName):
    tasks.append(Task(1, functionName))


def store():
    # task = Task(0, "func0()")
    # tasks.append(task)
    # tasks.append(Task(1, "func1()"))
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
                Task(task_dict["scheduledUptimeMillis"],
                     task_dict["functionName"])
            )


def sleep():
    store()
    durationSeconds = 3
    print("sleepscheduler: sleep for {} seconds".format(durationSeconds))
    machine.deepsleep(durationSeconds * 1000)


def execute():
    print("execute")


restore_from_rtc_memory()
