import sys
# import select
import time
import threading
import getpass
from typing import Tuple, List

DATAFILE = "./timer_data.csv"
UPDATE_CYCLE = 1
MESSAGE = """
start task: start {TaskName}
show summary: sum
end task: end
"""

event = threading.Event()


def print_timer(task: str, start_time: float) -> None:
    while True:
        event.wait()
        time_elapsed_str = time.strftime("%H:%M:%S",
                                         time.gmtime(time.time() - start_time))
        print(f"{task} {time_elapsed_str}", flush=True, end="\r")
        time.sleep(UPDATE_CYCLE)


def load_data(datafile: str) -> Tuple[List[str], str, float]:
    with open(datafile, "r") as f:
        data = f.readlines()
    if len(data) > 0 and not data[-1].endswith("\n"):
        last_task_data = data[-1].split(",")
        if len(last_task_data) == 3:
            task = last_task_data[0]
            start_time = time.mktime(time.strptime(last_task_data[1],
                                                   "%Y/%m/%d %H:%M:%S"))
            th = threading.Thread(target=print_timer,
                                  args=(task, start_time),
                                  daemon=True)
            th.start()
            event.set()
        else:
            print("Last entry seems broken.")
            sys.exit()
    else:
        task = start_time = None
    return data, task, start_time


def sum_time(data: List[str], weekly: bool = True) -> str:
    summed_time_float = 0.0
    if weekly:
        time_now = time.time()
        now_wday = time.localtime(time_now).tm_wday
        time_wstart = time_now - now_wday * 60 * 60 * 24
    for entry in data:
        entry_arr = [v.strip() for v in entry.split(",")]
        start_time = time.mktime(time.strptime(entry_arr[1],
                                               "%Y/%m/%d %H:%M:%S"))
        end_time = time.mktime(time.strptime(entry_arr[2],
                                             "%Y/%m/%d %H:%M:%S"))
        if not weekly or start_time > time_wstart:
            time_elapsed = end_time - start_time
            summed_time_float += time_elapsed
    hour = int(summed_time_float // (60 * 60))
    minute = int((summed_time_float % (60 * 60)) // 60)
    second = (summed_time_float % (60 * 60)) % 60
    return f"{hour}:{minute}:{second:.0f}"


def show_data(data: List[str]) -> None:
    for entry in data:
        # TODO: formatに変更
        print(entry.replace(",", "\t"))


data, task, start_time = load_data(DATAFILE)
print(MESSAGE)

while True:
    if task is None:
        input_str = input(">>>")
        input_arr = input_str.strip().split()
        command = input_arr[0]
        if command == "start":
            if len(input_arr) < 2:
                print("please input Task Name also.")
            else:
                task = " ".join(input_arr[1:]).replace(",", "_")
                start_time = time.time()
                with open(DATAFILE, "a") as f:
                    start_time_str = time.strftime("%Y/%m/%d %H:%M:%S",
                                                   time.localtime(start_time))
                    f.write(f"{task},{start_time_str},")
                data.append(f"{task},{start_time_str},")
                th = threading.Thread(target=print_timer,
                                      args=(task, start_time),
                                      daemon=True)
                th.start()
                event.set()
        elif command == "sum":
            print(sum_time(data))
        elif command == "end":
            print("no task is running.")
        elif command == "show":
            show_data(data)
        else:
            print(f"{command} is not valid command.")
    else:
        input_arr = input().strip().split()
        if len(input_arr) > 0:
            command = input_arr[0]
        else:
            continue
        if command == "end":
            event.clear()
            end_time = time.time()
            with open(DATAFILE, "a") as f:
                end_time_str = time.strftime("%Y/%m/%d %H:%M:%S",
                                             time.localtime(end_time))
                f.write(f"{end_time_str},\n")
                data[-1] += f"{end_time_str}"
            task = None
        elif command == "sum":
            print(sum_time(data))
        elif command == "start":
            print(f"please end running task: {task}")
        elif command == "show":
            show_data(data)
        else:
            print(f"{command} is not valid command.")