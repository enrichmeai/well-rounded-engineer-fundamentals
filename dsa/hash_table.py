"""A hash table from scratch: buckets, a hash function, collisions, and resizing.

    python3 hash_table.py

Python's dict is a hash table. This one is small enough to read in full. It uses separate
chaining: each bucket holds a list of (key, value) pairs whose hashes landed there.

  put/get   hash the key, take it modulo the number of buckets, search that one bucket
  resize    when items / buckets (the load factor) passes 0.75, double the buckets and
            re-insert everything, so buckets stay short and lookups stay O(1) on average

The hash function is FNV-1a, written out below, rather than Python's built-in hash(): Python
randomises string hashes each time it starts (PYTHONHASHSEED), so the demo would print
different bucket sizes on every run.

The demo also shows what a bad hash function does: every key lands in one bucket, and
each lookup becomes a linear search, O(n).
"""


def fnv1a(key: str) -> int:
    """FNV-1a, 32-bit: start from an offset, then for each byte XOR it in and multiply by a prime."""
    h = 0x811C9DC5
    for byte in key.encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & 0xFFFFFFFF   # keep 32 bits
    return h


class HashTable:
    def __init__(self, buckets: int = 8, hash_fn=fnv1a, max_load: float = 0.75):
        self.buckets: list[list[tuple]] = [[] for _ in range(buckets)]
        self.hash_fn = hash_fn
        self.max_load = max_load
        self.size = 0
        self.resizes = 0

    def _bucket(self, key) -> list:
        return self.buckets[self.hash_fn(key) % len(self.buckets)]

    def put(self, key, value) -> None:
        bucket = self._bucket(key)
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)      # replace an existing key
                return
        bucket.append((key, value))
        self.size += 1
        if self.size / len(self.buckets) > self.max_load:
            self._resize()

    def get(self, key):
        """Returns (value, comparisons). Raises KeyError if absent."""
        steps = 0
        for k, v in self._bucket(key):
            steps += 1
            if k == key:
                return v, steps
        raise KeyError(key)

    def _resize(self) -> None:
        old = [pair for bucket in self.buckets for pair in bucket]
        self.buckets = [[] for _ in range(len(self.buckets) * 2)]
        self.size = 0
        self.resizes += 1
        for k, v in old:
            self.put(k, v)

    def longest_bucket(self) -> int:
        return max(len(b) for b in self.buckets)


def fill(n: int, hash_fn=fnv1a) -> HashTable:
    t = HashTable(hash_fn=hash_fn)
    for i in range(n):
        t.put(f"user-{i}", i)
    return t


def bad_hash(key) -> int:
    return 42                                  # every key collides


if __name__ == "__main__":
    good = fill(1000)
    print(f"good hash : 1000 keys, {len(good.buckets)} buckets after {good.resizes} resizes, "
          f"longest bucket {good.longest_bucket()}, get('user-999') took {good.get('user-999')[1]} comparisons")
    bad = fill(1000, bad_hash)
    print(f"bad hash  : 1000 keys, {len(bad.buckets)} buckets, longest bucket {bad.longest_bucket()}, "
          f"get('user-999') took {bad.get('user-999')[1]} comparisons")
