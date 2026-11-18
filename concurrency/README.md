# concurrency: what goes wrong when work overlaps, and the tools that stop it

Two threads changing the same data can lose an update, wait for each other for ever, or slow each other down.
These bugs depend on timing, so they come and go, and they can vanish when you add a print statement. Here each
example **forces** the bad timing (with a `Barrier` or an `Event`), so it happens on every run and you can see
exactly why. Then it shows the fix. Standard library only; one idea per file.

| File | The idea | What you will see |
|---|---|---|
| [`lost_update.py`](lost_update.py) | A race condition, and a lock | Two deposits of 100 give 100 without a lock, 200 with one |
| [`deadlock.py`](deadlock.py) | Deadlock, and lock ordering | Opposite lock orders: both threads stuck; the same order: both finish |
| [`optimistic.py`](optimistic.py) | Optimistic concurrency (a version number) | The second writer is told its data is stale, reads again and retries |
| [`io_vs_cpu.py`](io_vs_cpu.py) | Threads, the GIL, and processes | Threads speed up waiting, not arithmetic; processes speed up arithmetic |
| [`pipeline.py`](pipeline.py) | Passing data through queues instead of sharing it | Orders flow producer → workers → collector with no locks of your own |
| [`amdahl.py`](amdahl.py) | Amdahl's law | 90% parallel work can never go more than 10× faster |

## Run it

You need Python 3.10 or newer. From this folder:

```bash
python3 lost_update.py
python3 deadlock.py        # about two seconds: the timeouts are how it detects the deadlock
python3 optimistic.py
python3 io_vs_cpu.py       # timings depend on your machine: compare the rows, not the numbers
python3 pipeline.py
python3 amdahl.py          # or: python3 amdahl.py 0.5
```

Run the tests:

```bash
python3 -m pip install pytest
python3 -m pytest
```

## What happens, step by step

**Lost update.** Each thread reads the balance (0), then the barrier holds it until the other thread has read too,
then each writes `0 + 100`. The second write overwrites the first. The lock version makes read-and-write one step
that only one thread can be inside at a time.

```text
two deposits of 100, unsafe: 100
two deposits of 100, locked: 200
```

**Deadlock.** A takes lock 1 and wants lock 2; B takes lock 2 and wants lock 1. Each holds what the other needs.
A deadlock needs all four of Coffman's conditions: mutual exclusion, hold and wait, no preemption, and circular wait.
Taking the locks in one agreed order removes the circular wait. The demo asks for the second lock with a timeout,
so instead of hanging your terminal it reports who was stuck.

```text
opposite orders (A: 1 then 2, B: 2 then 1):
  A holds lock1, stuck waiting for lock2
  B holds lock2, stuck waiting for lock1
same order (both: 1 then 2):
  A took lock1 then lock2
  B took lock1 then lock2
```

**Optimistic concurrency.** No lock is held while working. The save succeeds only if the version is still the one
you read, which is what `UPDATE ... WHERE id = ? AND version = ?` does in a database. A conflict is not an error: you
read again and retry.

```text
A: attempt 1 saved 0 -> 100 (version 0 -> 1)
B: attempt 1 conflict (read version 0, it has changed); retrying
B: attempt 2 saved 100 -> 200 (version 1 -> 2)
final balance 200, version 2
```

**Threads, the GIL and processes.** A thread that waits (on the network, a disk, or here `time.sleep`) lets another
run, so ten waits overlap. In standard CPython only one thread runs Python code at a time (the global interpreter lock),
so threads do not speed up arithmetic; separate processes do, because each has its own interpreter. One run on a
4-core machine:

```text
Python 3.13.18, GIL enabled: True
1. ten waits of 0.2 s (I/O-bound)
   one after another : 2.00 s
   ten threads       : 0.20 s
2. four chunks of arithmetic (CPU-bound)
   one after another : 0.54 s
   four threads      : 0.59 s
   four processes    : 0.16 s
```

**Pipeline.** Each thread owns its data and passes results on through a `queue.Queue`, which does its own locking. A
bounded queue makes a fast producer wait for slow workers (back-pressure). One `STOP` value per worker shuts it down.

**Amdahl's law.** With a fraction `p` that can run in parallel on `s` processors, the speed-up is
`1 / ((1 - p) + p / s)`. The serial part sets the ceiling.

## Try next

1. In `lost_update.py`, delete the `both_have_read.wait()` line and run the unsafe version many times. How often do
   you see 100 now? The race is still there; it just became rare, which is what makes it dangerous in real code.
2. In `deadlock.py`, give each thread a third lock and three different orders. Which orders deadlock?
3. In `optimistic.py`, add a third writer. How many retries happen in total?
4. In `io_vs_cpu.py`, replace the threads in part 1 with `asyncio.gather` and `asyncio.sleep`. One thread, the same
   overlap.
5. In `pipeline.py`, make one worker slow (`time.sleep(0.1)` per order) and watch the producer block on `put()`.
6. Run `python3 amdahl.py 0.99`. How many processors does it take to get half of the ceiling?

## Read

- [Concurrency](https://enrichmeai.com/well-rounded-engineer/concurrency/) in the guide.
- [Distributed Systems](https://enrichmeai.com/well-rounded-engineer/distsys/): the same problems across machines.
- Python docs: [`threading`](https://docs.python.org/3/library/threading.html),
  [`queue`](https://docs.python.org/3/library/queue.html),
  [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html).
