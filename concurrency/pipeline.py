"""Share data by passing it through a queue, instead of sharing memory: a producer-consumer pipeline.

    python3 pipeline.py

This is the idea behind Go's channels and the actor model, done with Python's queue.Queue,
which is safe to use from many threads without your own locks. A producer puts orders on
the first queue; two workers take them off, price them, and put results on a second
queue; a collector reads the results. No thread touches another's data, so there is
nothing to lock.

A bounded queue (maxsize) gives back-pressure: if the workers fall behind, the producer
blocks on put() instead of filling memory. A special STOP value tells each worker to finish.
"""

import queue
import threading

STOP = object()   # a value no real order can be equal to


def produce(orders: list[dict], out: queue.Queue, workers: int) -> None:
    for order in orders:
        out.put(order)            # blocks while the queue is full: back-pressure
    for _ in range(workers):
        out.put(STOP)             # one STOP per worker, so each one finishes


def price(inbox: queue.Queue, outbox: queue.Queue, prices: dict[str, int]) -> None:
    while True:
        order = inbox.get()
        if order is STOP:
            outbox.put(STOP)
            return
        outbox.put({"id": order["id"], "total": prices[order["item"]] * order["qty"]})


def run(orders: list[dict], prices: dict[str, int], workers: int = 2, maxsize: int = 3) -> list[dict]:
    todo: queue.Queue = queue.Queue(maxsize=maxsize)
    done: queue.Queue = queue.Queue()
    threads = [threading.Thread(target=produce, args=(orders, todo, workers))]
    threads += [threading.Thread(target=price, args=(todo, done, prices)) for _ in range(workers)]
    for t in threads:
        t.start()
    results, stopped = [], 0
    while stopped < workers:      # collect until every worker has said it is finished
        item = done.get()
        if item is STOP:
            stopped += 1
        else:
            results.append(item)
    for t in threads:
        t.join()
    return sorted(results, key=lambda r: r["id"])   # workers finish in any order; sort to compare


if __name__ == "__main__":
    prices = {"tea": 3, "cake": 5}
    orders = [{"id": i, "item": "tea" if i % 2 else "cake", "qty": i} for i in range(1, 7)]
    for r in run(orders, prices):
        print(f"order {r['id']}: total {r['total']}")
