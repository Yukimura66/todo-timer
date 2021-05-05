import sys
import time
import threading
from typing import Tuple, List
import unicodedata
import pathlib

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


class Timer(threading.Thread):
    def __init__(self, task: str, start_time: float) -> None:
        super().__init__(daemon=True)
        self.task = task
        self.start_time = start_time
        self.run_flag = True

    def run(self) -> None:
        while self.run_flag:
            # self.event.wait()
            time_elapsed_str = time.strftime(
                "%H:%M:%S", time.gmtime(time.time() - self.start_time))
            print(f"{self.task} {time_elapsed_str}", flush=True, end="\r")
            time.sleep(UPDATE_CYCLE)

    def stop(self):
        self.run_flag = False


class FileData:
    def __init__(self, filepath: str = DATAFILE):
        self.file = filepath
        self.datalist = None

    def load_data(self) -> Tuple[str, float]:
        task, start_time = None, None
        if pathlib.Path(self.file).exists():
            with open(self.file, "r") as f:
                self.datalist = [[v.strip() for v in line.split(",")]
                                 for line in f.readlines()]
            if len(self.datalist) > 0 and self.datalist[-1][2] == "":
                last_task_data = self.datalist[-1]
                task = last_task_data[0]
                start_time = read_str_time(last_task_data[1])
        else:
            self.datalist = []
        return task, start_time

    def write_start(self, task: str, start_time: str):
        with open(self.file, "a") as f:
            start_time_str = time.strftime("%Y/%m/%d %H:%M:%S",
                                           time.localtime(start_time))
            f.write(f"{task},{start_time_str},")
            self.datalist.append([task, start_time_str, ""])

    def write_end(self, task: str, end_time: float):
        with open(self.file, "a") as f:
            end_time_str = time.strftime("%Y/%m/%d %H:%M:%S",
                                         time.localtime(end_time))
            f.write(f"{end_time_str}\n")
            self.datalist[-1][2] = end_time_str

    def __len__(self):
        return len(self.datalist)

    def delete(self, idx: int) -> None:
        if 0 <= idx < len(self.data):
            entry = self.datalist[idx]
            confirm = input("delete following entry?(y/N)\n" +
                            ",".join(entry)) or "N"
            if confirm == "y":
                del self.datalist[idx]
                with open(self.file, "r") as f:
                    lines = f.readlines()
                del lines[idx]
                with open(self.file, "w") as f:
                    f.writelines(lines)
                print(f"entry {idx} is deleted.")
        else:
            print("there is no data for idx: {idx}")


class REPLHandler:
    def __init__(self):
        self.timer = None
        self.data = FileData()
        self.task = None
        task, start_time = self.data.load_data()
        if task is not None:
            self.timer = Timer(task=task, start_time=start_time)
            self.timer.start()
            # event.set()

    def begin_timer(self, task: str) -> str:
        res = ""
        if self.timer is not None:
            res += f"please end running task: {self.timer.task}"
        else:
            self.task = task.replace(",", "_")
            start_time = time.time()
            self.data.write_start(task, start_time)
            self.timer = Timer(task, start_time)
            self.timer.start()
            # event.set()
        return res

    def end_timer(self) -> str:
        res = ""
        if self.timer is None:
            res += "no task is running."
        else:
            self.timer.stop()
            self.timer = None
            end_time = time.time()
            self.data.write_end(self.task, end_time)
        return res

    def delete(self, idx: int) -> str:
        res = ""
        if len(self.data) == 0:
            res += "there is no data"
        else:
            self.data.delete(idx)
        return res

    def command_eval(self, commands: List[str]) -> str:
        res = ""
        if len(commands) > 0:
            command, *rest = commands
            if command in ("end", "e"):
                res = self.end_timer()
            elif command in ("sum", ):
                res = sum_times(self.data.datalist)
            elif command in ("begin", "b"):
                task = " ".join(rest)
                res = self.begin_timer(task)
            elif command in ("show", "s"):
                res = make_show_str(self.data.datalist)
            elif command in ("quit", "q"):
                quit()
            elif command in ("delete", "d"):
                idx = int(rest[0])
                res = self.delete(idx)  # TODO: delete multiple entry
            else:
                res = f"{command} is not valid command."
        return res

    def command_read(self) -> List[str]:
        if self.timer is None:
            res = input(">>>")
        else:
            res = input()
        return [v.strip() for v in res.split()]

    def repl(self, starting_message) -> None:
        print(starting_message)
        while True:
            commands = self.command_read()
            res = self.command_eval(commands)
            command_print(res)


def command_print(string: str) -> None:
    if string:
        print(string)


def read_str_time(str_time: str) -> float:
    return time.mktime(time.strptime(str_time, TIME_FORMAT))


def make_show_str(data: List[Tuple[str, str, str]],
                  weekly: bool = True) -> str:
    """make summery string"""
    WIDTH_ALL = 4 + 4 + 30 + 4 + 19 + 4 + 19 + 4 + 12
    res = ""
    res += "-" * WIDTH_ALL + "\n"
    res += (f"{'id':4s}  | {'Task name':30s}  | {'Start time':19s}" +
            f"  | {'End time':19s}  | {'Time elapsed':12s}") + "\n"
    res += "=" * WIDTH_ALL + "\n"
    for id, entry in enumerate(data):
        start_time = read_str_time(entry[1])
        if entry[2] == "":
            end_time = time.time()
        else:
            end_time = read_str_time(entry[2])
        time_elapsed = end_time - start_time
        hour = int(time_elapsed // (60 * 60))
        minute = int((time_elapsed % (60 * 60)) // 60)
        second = (time_elapsed % (60 * 60)) % 60
        str_time_elapsed = f"{hour}:{minute:02}:{second:02.0f}"
        w = 30
        for c in entry[0]:
            if unicodedata.east_asian_width(c) in "FWA":
                w -= 1
        res += "{:4d}  | {:{w}.{w}s}  | {:19s}  | {:19s}  | {te:12s}".format(
            id, *entry, w=w, te=str_time_elapsed) + "\n"
    hour, minute, second = _sum_times(data, weekly)
    str_sum_time = SUM_TIME_FORMAT.format(hour=hour, minute=minute,
                                          second=second)
    res += "Total Time Weekly: " + str_sum_time + "\n"
    res += "-" * WIDTH_ALL
    return res


def _sum_times(data: List[Tuple[str, str, str]],
               weekly: bool = True) -> Tuple[int, int, float]:
    summed_time_float = 0.0
    if weekly:
        time_now = time.time()
        now_wday = time.localtime(time_now).tm_wday
        time_wstart = time_now - now_wday * 60 * 60 * 24
    for entry in data:
        start_time = read_str_time(entry[1])
        if entry[2] == "":
            end_time = time.time()
        else:
            end_time = read_str_time(entry[2])
        if not weekly or start_time > time_wstart:
            time_elapsed = end_time - start_time
            summed_time_float += time_elapsed
    hour = int(summed_time_float // (60 * 60))
    minute = int((summed_time_float % (60 * 60)) // 60)
    second = (summed_time_float % (60 * 60)) % 60
    return hour, minute, second


def sum_times(data: List[Tuple[str, str, str]],
              weekly: bool = True) -> str:
    hour, minute, second = _sum_times(data, weekly)
    return SUM_TIME_FORMAT.format(hour=hour, minute=minute, second=second)


def quit() -> None:
    sys.exit()


def modify(idx: int, **kwargs) -> None:
    pass  # TODO


if __name__ == "__main__":
    # event = threading.Event()
    # timer = None
    # data = None

    repl = REPLHandler()
    repl.repl(MESSAGE)


# TODO: add filter


# TODO: add test
#     CRUD部分をリファクタリングで切り出して関数化し、その部分についてテストを行う
#     print部分についてはtestは行わない

# TODO: add tag
#   sum with tag
#   show with tag
# TODO: add ToDo list function


# TODO: タイマー表示部分と、コマンド部分を分ける -> ncurseやstdout操作が必要
#     TODO: 入力コマンドを非表示(input部分を自作inputで置き換える)(上記の代替案)
