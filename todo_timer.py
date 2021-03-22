import sys
import time
import threading
from typing import Tuple, List
import unicodedata

DATAFILE = "./timer_data.csv"
UPDATE_CYCLE = 1
TIME_FORMAT = "%Y/%m/%d %H:%M:%S"
MESSAGE = """
start task: begin (or b) {TaskName}
show summary: show (or s)
sum time: sum
end task: end (or e)
quit: quit (or q)
"""
SUM_TIME_FORMAT = "{hour:d}:{minute:02d}:{second:02.0f}"

event = threading.Event()
timer = None
data = None


class Timer(threading.Thread):
    def __init__(self, task: str, start_time: float,
                 daemon: bool = True) -> None:
        super().__init__(daemon=daemon)
        self.task = task
        self.start_time = start_time
        self.run_flag = True

    def run(self) -> None:
        while self.run_flag:
            event.wait()
            time_elapsed_str = time.strftime(
                "%H:%M:%S", time.gmtime(time.time() - self.start_time))
            print(f"{self.task} {time_elapsed_str}", flush=True, end="\r")
            time.sleep(UPDATE_CYCLE)

    def stop(self) -> None:
        self.stop_flag = False


def read_str_time(str_time: str):
    return time.mktime(time.strptime(str_time, TIME_FORMAT))


def show_times(weekly: bool = True) -> None:
    WIDTH_ALL = 4 + 4 + 30 + 4 + 19 + 4 + 19 + 4 + 12
    print("-" * WIDTH_ALL)
    print(f"{'id':4s}  | {'Task name':30s}  | {'Start time':19s}" +
          f"  | {'End time':19s}  | {'Time elapsed':12s}")
    print("=" * WIDTH_ALL)
    for id, entry in enumerate(data):
        entry_arr = [v.strip() for v in entry.split(",")]
        start_time = read_str_time(entry_arr[1])
        if entry_arr[2] == "":
            end_time = time.time()
        else:
            end_time = read_str_time(entry_arr[2])
        time_elapsed = end_time - start_time
        hour = int(time_elapsed // (60 * 60))
        minute = int((time_elapsed % (60 * 60)) // 60)
        second = (time_elapsed % (60 * 60)) % 60
        str_time_elapsed = f"{hour}:{minute:02}:{second:02.0f}"
        w = 30
        for c in entry_arr[0]:
            if unicodedata.east_asian_width(c) in "FWA":
                w -= 1
        print("{:4d}  | {:{w}.{w}s}  | {:19s}  | {:19s}  | {te:12s}".format(
            id, *entry_arr, w=w, te=str_time_elapsed))
    hour, minute, second = _sum_times(weekly)
    str_sum_time = SUM_TIME_FORMAT.format(hour=hour, minute=minute,
                                          second=second)
    print("\nTotal Time Weekly: " + str_sum_time)
    print("-" * WIDTH_ALL)


def _sum_times(weekly: bool = True) -> Tuple[int, int, float]:
    summed_time_float = 0.0
    if weekly:
        time_now = time.time()
        now_wday = time.localtime(time_now).tm_wday
        time_wstart = time_now - now_wday * 60 * 60 * 24
    for entry in data:
        entry_arr = [v.strip() for v in entry.split(",")]
        start_time = read_str_time(entry_arr[1])
        if entry_arr[2] == "":
            end_time = time.time()
        else:
            end_time = read_str_time(entry_arr[2])
        if not weekly or start_time > time_wstart:
            time_elapsed = end_time - start_time
            summed_time_float += time_elapsed
    hour = int(summed_time_float // (60 * 60))
    minute = int((summed_time_float % (60 * 60)) // 60)
    second = (summed_time_float % (60 * 60)) % 60
    return hour, minute, second


def sum_times(weekly: bool = True) -> None:
    hour, minute, second = _sum_times(weekly)
    str_sum_time = SUM_TIME_FORMAT.format(hour=hour, minute=minute,
                                          second=second)
    print(str_sum_time)


def end_timer() -> None:
    global timer
    if timer is None:
        print("no task is running.")
    else:
        event.clear()
        timer.stop()
        timer = None
        end_time = time.time()
        with open(DATAFILE, "a") as f:
            end_time_str = time.strftime("%Y/%m/%d %H:%M:%S",
                                         time.localtime(end_time))
            f.write(f"{end_time_str}\n")
            data[-1] += f"{end_time_str}"


def begin_timer(*task: str) -> None:
    global timer
    if timer is not None:
        print(f"please end running task: {timer.task}")
    if not task:
        print("please input Task Name also.")
        timer = None
    else:
        print(task)
        task_str = " ".join(task).replace(",", "_")
        start_time = time.time()
        with open(DATAFILE, "a") as f:
            start_time_str = time.strftime("%Y/%m/%d %H:%M:%S",
                                           time.localtime(start_time))
            f.write(f"{task_str},{start_time_str},")
        data.append(f"{task_str},{start_time_str},")
        timer = Timer(task=task_str, start_time=start_time)
        timer.start()
        event.set()


def quit() -> None:
    sys.exit()


def delete(idx_str: str = None) -> None:
    if idx_str is None:
        print("please input index.")
    idx = int(idx_str)
    if not data:
        print("there is no data")
    else:
        entry = data[idx]
        confirm = (input("delete following entry?(y/N)\n" +
                         entry) or "N")
        if confirm == "y":
            _delete_entry(idx)
            print(f"entry {idx} is deleted.")


def _delete_entry(idx: int) -> None:
    global data
    if 0 <= idx < len(data):
        del data[idx]
        with open(DATAFILE, "r") as f:
            lines = f.readlines()
        del lines[idx]
        with open(DATAFILE, "w") as f:
            f.writelines(lines)
    else:
        print("there is no data for idx: {idx}")


def modify(idx_str: str = None) -> None:
    if idx_str is None:
        print("please input index.")
    else:
        global data
        idx = int(idx_str)
        if (idx < 0) or (idx >= len(data)):
            print("There is no index: {idx}")
        else:
            entry = data[idx]
            print("modify: ", entry)
            task, start_time, end_time, *_ = map(lambda x: x.strip(),
                                                 entry.split(","))
            task_new = input(f"Task name(default={task})>>>") or task
            start_time_new = read_time("Start time", start_time)
            end_time_new = read_time("End time", end_time)
            new_entry = ",".join([task_new, start_time_new, end_time_new])
            data[idx] = new_entry


def read_time(time_name: str, default: str) -> str:
    time_str = (input(f"{time_name}({TIME_FORMAT})(default={default})>>>")
                or default)
    try:
        time.strptime(time_str, TIME_FORMAT)
    except ValueError:
        print(f"please input with format {TIME_FORMAT}")
        time_str = default
    return time_str


def load_data(datafile: str) -> None:
    with open(datafile, "r") as f:
        global data
        data = f.readlines()
    if len(data) > 0 and not data[-1].endswith("\n"):
        last_task_data = data[-1].split(",")
        if len(last_task_data) == 3:
            task = last_task_data[0]
            start_time = read_str_time(last_task_data[1])
            global timer
            timer = Timer(task=task, start_time=start_time)
            timer.start()
            event.set()
        else:
            raise ValueError("Last entry seems broken.")


def run_command(*args: List[str]) -> None:
    if len(args) > 0:
        command, *rest = args
        if command in ["end", "e"]:
            end_timer()
        elif command in ["sum"]:
            sum_times(*rest)
        elif command in ["begin", "b"]:
            begin_timer(*rest)
        elif command in ["show", "s"]:
            show_times(*rest)
        elif command in ["quit", "q"]:
            quit()
        elif command in ["delete", "d"]:
            delete(*rest)
        elif command in ["modify", "m"]:
            modify(*rest)
        else:
            print(f"{command} is not valid command.")


load_data(DATAFILE)
print(MESSAGE)

while True:
    if timer is None:
        res = input(">>>")
    else:
        res = input()
    input_str = [v.strip() for v in res.split()]
    run_command(*input_str)

# TODO: time を datetime型に変更
# TODO: add test
#     CRUD部分をリファクタリングで切り出して関数化し、その部分についてテストを行う
#     print部分についてはtestは行わない

# TODO: modify entry
#   modify with index
# TODO: add tag
#   sum with tag
#   show with tag
# TODO: add ToDo list function


# TODO: タイマー表示部分と、コマンド部分を分ける -> ncurseやstdout操作が必要
#     TODO: 入力コマンドを非表示(input部分を自作inputで置き換える)(上記の代替案)
