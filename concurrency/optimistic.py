"""Optimistic concurrency: no lock while you work; check a version number when you save.

    python3 optimistic.py

Databases often do this with a `version` column:

    UPDATE accounts SET balance = :new, version = version + 1
    WHERE id = :id AND version = :version_you_read

If someone else saved first, the version has moved on, no row matches, and you must
read again and retry. Here a tiny in-memory store does the same thing, so you can see
each step: two writers read version 0, the first save wins, the second is rejected and
retries with fresh data. Nothing is lost, and nobody waited on a lock.
"""

import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class Row:
    balance: int
    version: int


class Store:
    """One row, with a compare-and-set save: it succeeds only if the version is unchanged."""

    def __init__(self) -> None:
        self._row = Row(balance=0, version=0)
        self._guard = threading.Lock()  # protects the store's own internals, like a database does

    def read(self) -> Row:
        with self._guard:
            return self._row

    def save_if_version(self, expected_version: int, new_balance: int) -> bool:
        with self._guard:
            if self._row.version != expected_version:
                return False                         # someone else saved first: conflict
            self._row = Row(new_balance, expected_version + 1)
            return True


def deposit(store: Store, amount: int, log: list[str], name: str, max_tries: int = 5,
            before_save=None) -> None:
    """Read, compute, try to save; on a conflict, read again and retry."""
    for attempt in range(1, max_tries + 1):
        row = store.read()
        if before_save:
            before_save()                            # in the demo: wait so both writers read first
        if store.save_if_version(row.version, row.balance + amount):
            log.append(f"{name}: attempt {attempt} saved {row.balance} -> {row.balance + amount} "
                       f"(version {row.version} -> {row.version + 1})")
            return
        log.append(f"{name}: attempt {attempt} conflict (read version {row.version}, it has changed); retrying")
        before_save = None                           # only force the clash on the first attempt
    raise RuntimeError(f"{name}: gave up after {max_tries} conflicts")


def demo() -> tuple[Row, list[str]]:
    """Two writers deposit 100 each; both read before either saves, as in lost_update.py.

    A Barrier makes both read version 0 first; an Event makes A save before B, so the
    printout is the same on every run.
    """
    store = Store()
    log: list[str] = []
    both_have_read = threading.Barrier(2)
    a_saved = threading.Event()

    def writer_a() -> None:
        deposit(store, 100, log, "A", before_save=both_have_read.wait)
        a_saved.set()

    def writer_b() -> None:
        def wait_for_a() -> None:
            both_have_read.wait()
            a_saved.wait()
        deposit(store, 100, log, "B", before_save=wait_for_a)

    a, b = threading.Thread(target=writer_a), threading.Thread(target=writer_b)
    a.start(); b.start(); a.join(); b.join()
    return store.read(), log


if __name__ == "__main__":
    row, log = demo()
    for line in log:
        print(line)
    print(f"final balance {row.balance}, version {row.version}")
