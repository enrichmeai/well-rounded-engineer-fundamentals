"""Tests for the data structures examples: each one agrees with Python's own version, and the
step counts grow the way Big O says they should."""

import heapq
import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import big_o  # noqa: E402
import graph  # noqa: E402
import hash_table  # noqa: E402
import heap  # noqa: E402
import lru  # noqa: E402
import sorting  # noqa: E402


# --- Big O ---------------------------------------------------------------------------------------

def test_searches_find_the_right_index():
    items = list(range(0, 200, 2))
    for target in (0, 98, 198):
        assert big_o.linear_search(items, target)[0] == items.index(target)
        assert big_o.binary_search(items, target)[0] == items.index(target)
    assert big_o.binary_search(items, 7)[0] == -1


def test_binary_search_steps_are_logarithmic():
    for n in (10, 1000, 100_000):
        _, steps = big_o.binary_search(list(range(n)), n)
        assert steps <= math.floor(math.log2(n)) + 1


def test_growth_matches_big_o():
    rows = big_o.table()
    (n0, lin0, _, nest0, set0), (n1, lin1, _, nest1, set1) = rows[0], rows[-1]
    assert lin1 / lin0 == n1 / n0 and set1 / set0 == n1 / n0          # linear
    assert nest1 == n1 * (n1 - 1) // 2                                # every pair once: n(n-1)/2


def test_duplicate_checks_agree():
    assert big_o.has_duplicate_set([3, 1, 4, 1, 5])[0] is True
    assert big_o.has_duplicate_nested([3, 1, 4, 1, 5])[0] is True
    assert big_o.has_duplicate_set([1, 2, 3])[0] is big_o.has_duplicate_nested([1, 2, 3])[0] is False


# --- Hash table ----------------------------------------------------------------------------------

def test_fnv1a_follows_the_published_algorithm():
    assert hash_table.fnv1a("") == 0x811C9DC5                          # the 32-bit offset basis
    assert hash_table.fnv1a("a") == ((0x811C9DC5 ^ ord("a")) * 0x01000193) & 0xFFFFFFFF


def test_hash_table_behaves_like_a_dict():
    t, d = hash_table.HashTable(), {}
    rng = random.Random(1)
    for _ in range(2000):
        k, v = f"k{rng.randint(0, 500)}", rng.random()
        t.put(k, v)
        d[k] = v
    assert t.size == len(d)
    assert all(t.get(k)[0] == v for k, v in d.items())
    with pytest.raises(KeyError):
        t.get("missing")


def test_resizing_keeps_buckets_short():
    t = hash_table.fill(1000)
    assert t.size / len(t.buckets) <= 0.75
    assert t.longest_bucket() <= 8


def test_a_bad_hash_makes_lookup_linear():
    t = hash_table.fill(500, hash_table.bad_hash)
    assert t.longest_bucket() == 500
    assert t.get("user-499")[1] == 500


# --- Heap ----------------------------------------------------------------------------------------

def test_heap_pops_in_the_same_order_as_heapq():
    rng = random.Random(7)
    values = [rng.randint(0, 100) for _ in range(300)]
    h, ref = heap.MinHeap(), []
    for v in values:
        h.push(v)
        heapq.heappush(ref, v)
    assert [h.pop() for _ in range(len(values))] == [heapq.heappop(ref) for _ in range(len(values))]
    with pytest.raises(IndexError):
        h.pop()


def test_top_k():
    rng = random.Random(3)
    values = [rng.randint(0, 10**6) for _ in range(1000)]
    assert heap.top_k_largest(values, 5) == sorted(values, reverse=True)[:5]


# --- Graphs --------------------------------------------------------------------------------------

def test_bfs_finds_fewest_hops_and_dijkstra_lowest_cost():
    assert graph.bfs_path(graph.CALLS, "gateway", "ledger") == ["gateway", "ledger"]
    assert graph.dijkstra(graph.CALLS, "gateway", "ledger") == (65, ["gateway", "orders", "payments", "ledger"])


def test_unreachable_returns_none():
    assert graph.bfs_path(graph.CALLS, "users", "ledger") is None
    assert graph.dijkstra(graph.CALLS, "users", "ledger") is None


# --- LRU cache -----------------------------------------------------------------------------------

def test_lru_evicts_the_least_recently_used():
    c = lru.LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1               # a is now the most recent
    c.put("c", 3)                        # evicts b, not a
    assert c.evicted == ["b"]
    assert c.get("b") is None and c.get("a") == 1 and c.get("c") == 3
    assert c.order() == ["c", "a"]


def test_lru_update_does_not_grow():
    c = lru.LRUCache(2)
    c.put("a", 1)
    c.put("a", 2)
    assert len(c.map) == 1 and c.get("a") == 2


# --- Sorting -------------------------------------------------------------------------------------

@pytest.mark.parametrize("n", [0, 1, 2, 50, 500])
def test_sorts_agree_with_sorted(n):
    rng = random.Random(n)
    data = [rng.randint(-1000, 1000) for _ in range(n)]
    assert sorting.insertion_sort(data)[0] == sorted(data)
    assert sorting.merge_sort(data)[0] == sorted(data)


def test_merge_sort_stays_within_n_log_n():
    rng = random.Random(9)
    for n in (100, 1000, 4000):
        data = [rng.random() for _ in range(n)]
        assert sorting.merge_sort(data)[1] <= n * math.ceil(math.log2(n))


def test_insertion_sort_is_quadratic_on_reversed_input():
    n = 300
    assert sorting.insertion_sort(list(range(n, 0, -1)))[1] == n * (n - 1) // 2
