# dsa: data structures and algorithms, written out and counted

The structures every program leans on: lists, hash tables, heaps, graphs and caches. Each file builds one from
scratch in plain Python, small enough to read top to bottom, and **counts its own steps**. Timings change from machine
to machine; step counts do not, so you can see Big O happen. The tests check each structure against Python's own
version (`dict`, `heapq`, `sorted`) so you know the hand-made one is right. Standard library only.

| File | What it shows | What you will see |
|---|---|---|
| [`big_o.py`](big_o.py) | Linear vs binary search; nested loops vs a set | n grows 1,000×: linear 1,000×, binary 3.5×, nested 1,111,000× |
| [`hash_table.py`](hash_table.py) | Buckets, a hash function (FNV-1a), collisions, resizing | 1,000 keys, longest bucket 4; with a bad hash, one bucket of 1,000 |
| [`heap.py`](heap.py) | A binary min-heap: the priority queue behind schedulers | Jobs pop in priority order; top 3 without sorting everything |
| [`graph.py`](graph.py) | Breadth-first search vs Dijkstra on a map of service calls | Fewest calls: 1 hop at 200 ms. Lowest latency: 3 hops at 65 ms |
| [`lru.py`](lru.py) | An LRU cache: a dict plus a doubly linked list | Which key is evicted, step by step |
| [`sorting.py`](sorting.py) | Insertion sort vs merge sort | 4,000 items: 3,999,453 comparisons vs 42,849 |

## Run it

You need Python 3.10 or newer. From this folder:

```bash
python3 big_o.py
python3 hash_table.py
python3 heap.py
python3 graph.py
python3 lru.py
python3 sorting.py
python3 -m pip install pytest && python3 -m pytest
```

## What happens, step by step

**Big O, counted.** For each list size, the worst case (searching for a value that is not there; a list with no
duplicates):

```text
        n    linear  binary   nested dup  set dup
       10        10       4           45       10
      100       100       7         4950      100
     1000      1000      10       499500     1000
    10000     10000      14     49995000    10000

n grew 1,000 times. Steps grew: linear 1,000x, binary 3.5x, nested 1,111,000x, set 1,000x.
```

Binary search needs a sorted list and halves it each time, so it takes about log₂ n steps. Checking every pair is
n(n−1)/2 steps; remembering what you have seen in a hash set is one lookup per item. That last change, from a nested
loop to a set, is a common fix for slow code.

**Inside a hash table.** A key is hashed to a number, and the number modulo the bucket count picks a bucket. When the
table is more than 75% full it doubles its buckets and re-inserts everything, so buckets stay short. The hash function
is FNV-1a, written out in the file, because Python randomises its built-in string hashes each time it starts, and the
output would change from run to run.

```text
good hash : 1000 keys, 2048 buckets after 8 resizes, longest bucket 4, get('user-999') took 2 comparisons
bad hash  : 1000 keys, 2048 buckets, longest bucket 1000, get('user-999') took 1000 comparisons
```

A hash function that sends every key to the same bucket turns every lookup into a linear search: O(1) becomes O(n).

**A heap.** A list read as a tree: the children of index `i` are at `2i+1` and `2i+2`, and each parent is no larger
than its children, so the smallest item is always first. Push and pop each move one item up or down one path, O(log n).

```text
pop order: [(1, 'page on-call'), (1, 'restart db'), (2, 'retry payment'), (3, 'send report'), (5, 'tidy logs')]
top 3 of [7, 2, 9, 4, 11, 5]: [11, 9, 7]
```

**Graphs.** Services calling each other, with latency on each call. Breadth-first search uses a queue and finds the
route with the fewest calls; Dijkstra uses a priority queue (a heap) and finds the route with the lowest total latency.
They disagree here, which is the point:

```text
fewest calls   gateway -> ledger: gateway -> ledger
lowest latency gateway -> ledger: gateway -> orders -> payments -> ledger (65 ms)
```

**An LRU cache.** A dict finds an entry in O(1); a doubly linked list keeps the entries in order of use, so the least
recently used one is always at the back. `get` moves an entry to the front; `put` evicts from the back when full.

**Sorting.** Comparisons on the same random lists (a fixed seed, so the numbers repeat):

```text
     n   insertion    merge
    10          33       24
   100        2464      537
  1000      244224     8697
  4000     3999453    42849
```

## The same structures in Java

[`java/`](java/) holds the same six programs in Java, file for file. Five print exactly what their Python twins print;
`Sorting.java` gets slightly different counts because `java.util.Random(42)` is a different generator from Python's
`random.Random(42)`, so the "random" arrays differ (the growth is the same). There is a seventh program,
`HashMapTrees.java`, because Java's own `HashMap` does something Python's `dict` does not. You need a JDK, version 21 or
newer, and nothing else: the `java` command runs a source file directly ([JEP 330](https://openjdk.org/jeps/330)).
From `java/`:

```bash
java BigO.java
java HashTable.java
java HashMapTrees.java
java Heap.java
java Graph.java
java Lru.java
java Sorting.java
javac -d out *.java && java -cp out DsaTests
```

| Python | Java | What to notice |
|---|---|---|
| returns a tuple `(index, steps)` | returns a `record Found(int index, long steps)` | Java has no tuples; a record is the short way to name one |
| `(lo + hi) // 2` | `(lo + hi) >>> 1` | Python integers never overflow; a Java `int` does past 2³¹, so `/ 2` can go negative on huge arrays |
| FNV-1a needs `& 0xFFFFFFFF` | the `int` wraps at 32 bits by itself | but it is signed, so the bucket uses `Integer.remainderUnsigned` |
| `hash(str)` changes every run | `String.hashCode()` is the same on every run | `"user-999".hashCode()` is always -267689961 ([the formula](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html#hashCode())) |
| tuples compare themselves | `record Job(...) implements Comparable<Job>` | Java must be told how to order your objects |
| `dict` keeps insertion order | `HashMap` keeps none; `LinkedHashMap` does | `Graph.java` uses `LinkedHashMap`, or BFS could try neighbours in any order |
| `heapq`, `deque`, `functools.lru_cache` | `PriorityQueue`, `ArrayDeque`, `LinkedHashMap(16, 0.75f, true)` | `Lru.java` builds the cache by hand, then in five lines with `removeEldestEntry`; the tests check both evict the same keys |
| `sorted()` is Timsort | `List.sort` is TimSort too | the JDK docs say it "was adapted from Tim Peters's list sort for Python" |

**A bad hash in Java's own HashMap.** `HashTable.java` prints the same three rows as Python, plus Java's
`String.hashCode` (longest bucket 3). But a real `HashMap` defends itself: when one bucket reaches 8 entries
(`TREEIFY_THRESHOLD` in the [JDK source](https://github.com/openjdk/jdk/blob/jdk-21%2B35/src/java.base/share/classes/java/util/HashMap.java))
and the table has at least 64 buckets, the bucket becomes a red-black tree. A tree is only fast if the keys can be
ordered, so making your key `Comparable` matters. One run:

```text
5,000 lookups in a HashMap of 5,000 keys
  good hashCode                     :      0.2 ms
  every hash 42, keys Comparable    :      3.0 ms
  every hash 42, keys not Comparable:     74.5 ms
```

The lesson for your own classes: a `hashCode()` that spreads keys out matters most; a natural order (`Comparable`) is
the safety net.

## Try next

1. In `big_o.py`, search for the first item instead of a missing one. Which counts change, and why is that the
   best case?
2. In `hash_table.py`, change `max_load` to `3.0`. How long does the longest bucket get, and how many comparisons does
   a lookup take now?
3. Turn `MinHeap` into a max-heap by changing two comparisons. Then use it for `top_k_largest` without negating anything.
4. In `graph.py`, add an edge with a negative latency and see whether Dijkstra still gives the right answer. Why does it assume costs are
   never negative?
5. Replace `LRUCache` with `functools.lru_cache` on a slow function and compare `cache_info()` with `evicted`.
6. Run `sorting.py` on input that is already sorted. Which algorithm wins now?
7. In `java/HashMapTrees.java`, raise `n` to 20,000 (4× more keys). The first two rows grow about 4×. O(n) per lookup
   predicts the last row grows 16× (4× more lookups, each searching a 4× longer tree); on our machine it grew from
   74.5 ms to 2,816.8 ms, about 38×, because the longer tree no longer fits in the CPU's caches. Big O is the floor of
   the bad news, not the ceiling.
8. In `java/BigO.java`, change `>>> 1` to `/ 2` and work out by hand what `(lo + hi) / 2` gives when `lo` and `hi`
   are both 1,500,000,000. (Java's own library had this overflow in its binary search for more than nine years: see Read.)

## Read

- [Data Structures & Algorithms](https://enrichmeai.com/well-rounded-engineer/dsa/) in the guide.
- Python docs: [`heapq`](https://docs.python.org/3/library/heapq.html),
  [`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque),
  [`functools.lru_cache`](https://docs.python.org/3/library/functools.html#functools.lru_cache).
- [Fowler–Noll–Vo hash function](https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function).
- Java docs (21): [`HashMap`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html),
  [`LinkedHashMap`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/LinkedHashMap.html),
  [`PriorityQueue`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/PriorityQueue.html).
- [Binary search: implementation issues](https://en.wikipedia.org/wiki/Binary_search#Implementation_issues),
  including the overflow found in the JDK.
