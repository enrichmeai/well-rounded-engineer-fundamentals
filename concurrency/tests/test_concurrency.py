"""Tests for the concurrency examples. Standard library plus pytest; no network."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import amdahl  # noqa: E402
import deadlock  # noqa: E402
import io_vs_cpu  # noqa: E402
import lost_update  # noqa: E402
import optimistic  # noqa: E402
import pipeline  # noqa: E402


@pytest.mark.parametrize("run", range(5))
def test_unsafe_deposits_always_lose_one_update(run):
    # The barrier forces the bad interleaving, so this is the same on every run.
    assert lost_update.unsafe_deposits() == 100


@pytest.mark.parametrize("run", range(5))
def test_locked_deposits_keep_both(run):
    assert lost_update.locked_deposits() == 200


def test_opposite_lock_orders_deadlock():
    result = deadlock.run(("lock1", "lock2"), ("lock2", "lock1"), timeout=0.2)
    assert result == {
        "A": "holds lock1, stuck waiting for lock2",
        "B": "holds lock2, stuck waiting for lock1",
    }


def test_same_lock_order_does_not_deadlock():
    result = deadlock.run(("lock1", "lock2"), ("lock1", "lock2"), timeout=0.2)
    assert result == {"A": "took lock1 then lock2", "B": "took lock1 then lock2"}


def test_store_rejects_a_stale_version():
    store = optimistic.Store()
    assert store.save_if_version(0, 50) is True
    assert store.save_if_version(0, 999) is False        # version is now 1
    assert store.read() == optimistic.Row(balance=50, version=1)


def test_optimistic_demo_detects_the_conflict_and_loses_nothing():
    row, log = optimistic.demo()
    assert row == optimistic.Row(balance=200, version=2)
    assert any("conflict" in line for line in log)
    assert log[-1].startswith("B: attempt 2 saved 100 -> 200")


def test_deposit_gives_up_after_max_tries():
    class AlwaysConflicts(optimistic.Store):
        """A store where another writer always saves first."""
        def save_if_version(self, expected_version, new_balance):
            return False

    log = []
    with pytest.raises(RuntimeError, match="gave up after 3 conflicts"):
        optimistic.deposit(AlwaysConflicts(), 100, log, "C", max_tries=3)
    assert len(log) == 3 and all("conflict" in line for line in log)


def test_threads_overlap_waits():
    sequential = io_vs_cpu.timed(lambda: io_vs_cpu.sequential(io_vs_cpu.wait_like_io, 8, 0.05))
    threaded = io_vs_cpu.timed(lambda: io_vs_cpu.with_threads(io_vs_cpu.wait_like_io, 8, 0.05))
    assert sequential >= 0.35            # 8 x 0.05 s, one after another
    assert threaded < sequential / 3     # waits overlap; a wide margin so slow CI machines still pass


def test_cpu_task_and_gil_check():
    assert io_vs_cpu.busy_cpu(10) == sum(i * i % 7 for i in range(10))
    assert isinstance(io_vs_cpu.gil_enabled(), bool)


@pytest.mark.parametrize("workers,maxsize", [(1, 1), (2, 3), (4, 1)])
def test_pipeline_prices_every_order_once(workers, maxsize):
    prices = {"tea": 3, "cake": 5}
    orders = [{"id": i, "item": "tea" if i % 2 else "cake", "qty": i} for i in range(1, 21)]
    results = pipeline.run(orders, prices, workers=workers, maxsize=maxsize)
    assert [r["id"] for r in results] == list(range(1, 21))
    assert results[0] == {"id": 1, "total": 3}
    assert results[1] == {"id": 2, "total": 10}


def test_amdahl_matches_the_guide_table():
    assert round(amdahl.speedup(0.9, 2), 2) == 1.82
    assert round(amdahl.speedup(0.9, 8), 2) == 4.71
    assert round(amdahl.speedup(0.9, 64), 2) == 8.77
    assert amdahl.ceiling(0.9) == pytest.approx(10)
    assert amdahl.speedup(0.9, 1) == 1


def test_amdahl_rejects_nonsense():
    with pytest.raises(ValueError):
        amdahl.speedup(1.5, 2)
    with pytest.raises(ValueError):
        amdahl.speedup(0.5, 0)
