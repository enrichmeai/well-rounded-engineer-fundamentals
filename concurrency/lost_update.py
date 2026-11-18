"""A lost update between two threads, forced to happen every time, and the lock that prevents it.

    python3 lost_update.py

Two threads each deposit 100 into a shared balance that starts at 0. Each one reads the
balance, then writes back (what it read + 100). If both read before either writes, the
second write overwrites the first, and one deposit is lost.

Real races depend on timing, so they come and go. Here a Barrier makes both threads wait
until both have read, so the bad order happens on every run and you can see it.
"""

import threading


class Account:
    def __init__(self) -> None:
        self.balance = 0


def unsafe_deposits(amount: int = 100) -> int:
    """Two deposits with no lock, both reads forced to happen before either write."""
    account = Account()
    both_have_read = threading.Barrier(2)

    def deposit() -> None:
        seen = account.balance          # 1. read
        both_have_read.wait()           # 2. wait until the other thread has read too
        account.balance = seen + amount  # 3. write: based on a value that is now stale

    threads = [threading.Thread(target=deposit) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return account.balance


def locked_deposits(amount: int = 100) -> int:
    """The same two deposits, with read-and-write done together under a lock."""
    account = Account()
    lock = threading.Lock()

    def deposit() -> None:
        with lock:                      # only one thread at a time runs this block
            seen = account.balance
            account.balance = seen + amount

    threads = [threading.Thread(target=deposit) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return account.balance


if __name__ == "__main__":
    print(f"two deposits of 100, unsafe: {unsafe_deposits()}")
    print(f"two deposits of 100, locked: {locked_deposits()}")
