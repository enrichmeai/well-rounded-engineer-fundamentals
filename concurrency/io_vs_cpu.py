"""Threads help when work waits (I/O); in standard CPython they do not speed up pure CPU work.

    python3 io_vs_cpu.py

Part 1 does ten "requests" that each wait 0.2 s (time.sleep stands in for a network or
disk wait). One after another they take about 2 s; with ten threads they overlap and take
about 0.2 s, because a waiting thread releases the interpreter.

Part 2 does four chunks of pure arithmetic. In the standard CPython build, the global
interpreter lock (GIL) lets only one thread run Python code at a time, so four threads take
about as long as doing the chunks one by one. Four processes, each with its own interpreter,
can use four CPU cores. (Python 3.13 added an experimental free-threaded build, a separate
executable without the GIL; on that build the thread timings change. The script prints
which build you have.)

Timings depend on your machine, so your numbers will differ; compare the rows, not the values.
"""

import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def wait_like_io(seconds: float = 0.2) -> None:
    time.sleep(seconds)


def busy_cpu(n: int = 3_000_000) -> int:
    total = 0
    for i in range(n):
        total += i * i % 7
    return total


def timed(fn) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def sequential(task, count: int, arg) -> None:
    for _ in range(count):
        task(arg)


def with_threads(task, count: int, arg) -> None:
    with ThreadPoolExecutor(max_workers=count) as pool:
        list(pool.map(task, [arg] * count))


def with_processes(task, count: int, arg) -> None:
    with ProcessPoolExecutor(max_workers=count) as pool:
        list(pool.map(task, [arg] * count))


def gil_enabled() -> bool:
    check = getattr(sys, "_is_gil_enabled", None)   # added in Python 3.13
    return True if check is None else check()


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]}, GIL enabled: {gil_enabled()}")
    print("1. ten waits of 0.2 s (I/O-bound)")
    print(f"   one after another : {timed(lambda: sequential(wait_like_io, 10, 0.2)):.2f} s")
    print(f"   ten threads       : {timed(lambda: with_threads(wait_like_io, 10, 0.2)):.2f} s")
    print("2. four chunks of arithmetic (CPU-bound)")
    print(f"   one after another : {timed(lambda: sequential(busy_cpu, 4, 3_000_000)):.2f} s")
    print(f"   four threads      : {timed(lambda: with_threads(busy_cpu, 4, 3_000_000)):.2f} s")
    print(f"   four processes    : {timed(lambda: with_processes(busy_cpu, 4, 3_000_000)):.2f} s")
