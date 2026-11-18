"""A deadlock between two threads, detected instead of hanging, and the fix: one lock order.

    python3 deadlock.py

Thread A takes lock 1 then wants lock 2; thread B takes lock 2 then wants lock 1. Each
holds what the other needs, so neither can go on: the four Coffman conditions (mutual
exclusion, hold and wait, no preemption, circular wait) all hold.

So the demo does not hang your terminal, each thread asks for its second lock with a
timeout. A timeout that expires is how we *detect* the deadlock. The fix breaks the
circular wait: every thread takes the locks in the same order.
"""

import threading


def run(order_a: tuple[str, str], order_b: tuple[str, str], timeout: float = 0.5) -> dict[str, str]:
    """Run two threads that each take two locks in the given orders. Returns what each one managed."""
    locks = {"lock1": threading.Lock(), "lock2": threading.Lock()}
    both_hold_first = threading.Barrier(2, timeout=timeout)
    both_have_tried = threading.Barrier(2, timeout=timeout)
    result: dict[str, str] = {}

    def worker(name: str, order: tuple[str, str]) -> None:
        first, second = locks[order[0]], locks[order[1]]
        with first:
            try:
                # Wait until the other thread holds its first lock too (forces the bad timing).
                both_hold_first.wait()
            except threading.BrokenBarrierError:
                # With the SAME order, the other thread is blocked waiting for our first lock,
                # so it never reaches the barrier and the barrier times out. That is expected
                # and harmless: it is why the same-order run takes a little longer.
                pass
            if second.acquire(timeout=timeout):
                second.release()
                result[name] = f"took {order[0]} then {order[1]}"
            else:
                result[name] = f"holds {order[0]}, stuck waiting for {order[1]}"
            try:
                # Keep holding the first lock until the other thread has tried too, so a
                # thread that gives up cannot hand its lock to the other one mid-attempt.
                both_have_tried.wait()
            except threading.BrokenBarrierError:
                pass

    a = threading.Thread(target=worker, args=("A", order_a))
    b = threading.Thread(target=worker, args=("B", order_b))
    a.start(); b.start(); a.join(); b.join()
    return result


if __name__ == "__main__":
    print("opposite orders (A: 1 then 2, B: 2 then 1):")
    for name, what in sorted(run(("lock1", "lock2"), ("lock2", "lock1")).items()):
        print(f"  {name} {what}")
    print("same order (both: 1 then 2):")
    for name, what in sorted(run(("lock1", "lock2"), ("lock1", "lock2")).items()):
        print(f"  {name} {what}")
